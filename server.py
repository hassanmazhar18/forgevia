"""
Forgevia — the all-in-one web platform.
Build · Deploy · Rank · Scrape · Monitor · Grow
"""
import shlex, sys
import os, re, json, shutil, subprocess, time, hashlib, secrets, sqlite3, zipfile, io, threading, signal, socket, mimetypes
from pathlib import Path
from urllib.parse import urljoin, urlparse
from datetime import datetime

import httpx
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException, Request, Depends, UploadFile, File, Response
from fastapi.responses import PlainTextResponse, HTMLResponse, FileResponse, JSONResponse, StreamingResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional

ROOT = Path(__file__).parent
DATA = Path(os.environ.get("FV_DATA") or (ROOT / "data")); PROJECTS = DATA / "projects"; SITES = DATA / "sites"; VERSIONS = DATA / "versions"; UPLOADS = DATA / "uploads"
for d in (DATA, PROJECTS, SITES, VERSIONS, UPLOADS): d.mkdir(parents=True, exist_ok=True)
DB = DATA / "forgevia.db"
FREE_PORTS = list(range(9100, 9200))

app = FastAPI(title="Forgevia", docs_url="/api/docs")
from fastapi.middleware.cors import CORSMiddleware
import json as _json, time as _time
REQLOG = DATA / "requests.log"
@app.middleware("http")
async def _reqlog(request, call_next):
    t=_time.time(); exc=None
    try:
        resp = await call_next(request)
        code = resp.status_code
    except Exception as e:
        code = f"EXC {e!r}"; resp = None; exc=e
    try:
        if not request.url.path.startswith("/static"):
            h=request.headers
            with open(REQLOG, "a", encoding="utf-8") as f:
                f.write(_json.dumps({"t":round(t),"ip":request.client.host if request.client else None,"m":request.method,"p":str(request.url),"code":code,
                  "ms":round((_time.time()-t)*1000),"origin":h.get("origin"),"ref":h.get("referer"),"proto":h.get("x-forwarded-proto"),"host":h.get("host"),
                  "ua":(h.get("user-agent") or "")[:60],"cookie":bool(h.get("cookie")),"auth":bool(h.get("authorization")),"sfd":h.get("sec-fetch-dest"),"sfs":h.get("sec-fetch-site"),"hdrs":(sorted(h.keys()) if request.url.path=="/api/me" else None),"qs":(str(request.url.query)[:40] if request.url.path=="/api/me" else None)})+"\n")
    except Exception: pass
    if exc is not None: raise exc
    return resp
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
mimetypes.add_type("application/javascript", ".js")

# ═══════════════════════════════ DB ═══════════════════════════════
def db():
    c = sqlite3.connect(DB, check_same_thread=False); c.row_factory = sqlite3.Row; return c

with db() as c:
    c.executescript("""
    CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, email TEXT UNIQUE, name TEXT, pw TEXT, plan TEXT DEFAULT 'free', created REAL);
    CREATE TABLE IF NOT EXISTS sessions(token TEXT PRIMARY KEY, uid INTEGER, created REAL);
    CREATE TABLE IF NOT EXISTS projects(id INTEGER PRIMARY KEY, uid INTEGER, name TEXT UNIQUE, kind TEXT DEFAULT 'static', domain TEXT, published REAL, created REAL, template TEXT, seo_title TEXT, seo_desc TEXT, ga TEXT, password TEXT);
    CREATE TABLE IF NOT EXISTS versions(id INTEGER PRIMARY KEY, project TEXT, label TEXT, created REAL, path TEXT);
    CREATE TABLE IF NOT EXISTS hits(id INTEGER PRIMARY KEY, project TEXT, path TEXT, ref TEXT, ua TEXT, ip TEXT, country TEXT, ts REAL);
    CREATE TABLE IF NOT EXISTS forms(id INTEGER PRIMARY KEY, project TEXT, form TEXT, data TEXT, ts REAL);
    CREATE TABLE IF NOT EXISTS monitors(id INTEGER PRIMARY KEY, uid INTEGER, url TEXT, interval INTEGER DEFAULT 300, last_status INTEGER, last_ms INTEGER, last_check REAL, up_count INTEGER DEFAULT 0, down_count INTEGER DEFAULT 0, created REAL);
    CREATE TABLE IF NOT EXISTS monitor_log(id INTEGER PRIMARY KEY, mid INTEGER, status INTEGER, ms INTEGER, ts REAL);
    CREATE TABLE IF NOT EXISTS kv(project TEXT, k TEXT, v TEXT, PRIMARY KEY(project,k));
    CREATE TABLE IF NOT EXISTS domains(domain TEXT PRIMARY KEY, project TEXT, verified INTEGER DEFAULT 0, token TEXT, created REAL);
    CREATE TABLE IF NOT EXISTS activity(id INTEGER PRIMARY KEY, uid INTEGER, project TEXT, action TEXT, detail TEXT, ts REAL);
    CREATE TABLE IF NOT EXISTS snippets(id INTEGER PRIMARY KEY, uid INTEGER, title TEXT, lang TEXT, code TEXT, public INTEGER DEFAULT 1, slug TEXT UNIQUE, created REAL);
    """)

def log(uid, project, action, detail=""):
    with db() as c: c.execute("INSERT INTO activity(uid,project,action,detail,ts) VALUES(?,?,?,?,?)", (uid, project, action, detail, time.time()))

# ═══════════════════════════════ AUTH ═══════════════════════════════
def set_session_cookie(res, req, tok):
    """Set the session cookie in every form a browser might accept.
    Proxies (e.g. preview hosts) often omit x-forwarded-proto, so we cannot trust the scheme:
    - 'fv'  : SameSite=None; Secure  -> works in cross-site iframes over HTTPS
    - 'fvl' : SameSite=Lax           -> works top-level over plain HTTP (local dev)
    """
    host = req.headers.get("x-forwarded-host") or req.headers.get("host") or ""
    local = host.startswith(("localhost", "127.0.0.1"))
    res.set_cookie("fvl", tok, httponly=True, max_age=86400*30, samesite="lax", secure=False)
    if not local: res.set_cookie("fv", tok, httponly=True, max_age=86400*30, samesite="none", secure=True)
    else: res.set_cookie("fv", tok, httponly=True, max_age=86400*30, samesite="lax", secure=False)

def _tok_from(req: Request):
    return (req.headers.get("authorization", "").replace("Bearer ", "").strip()
            or req.headers.get("x-fv-token", "").strip()
            or req.query_params.get("_fvt", "").strip()
            or req.cookies.get("fv") or req.cookies.get("fvl") or req.cookies.get("fvs_fv_token") or None)

def hashpw(p, salt=None):
    salt = salt or secrets.token_hex(8)
    return salt + ":" + hashlib.sha256((salt + p).encode()).hexdigest()
def checkpw(p, h):
    salt = h.split(":")[0]; return hashpw(p, salt) == h

def user(req: Request):
    tok = _tok_from(req)
    if not tok: raise HTTPException(401, "Sign in required")
    with db() as c:
        r = c.execute("SELECT u.* FROM sessions s JOIN users u ON u.id=s.uid WHERE token=?", (tok,)).fetchone()
    if not r: raise HTTPException(401, "Session expired")
    return dict(r)

class Auth(BaseModel): email: str; password: str; name: Optional[str] = None

@app.post("/api/auth/signup")
def signup(a: Auth, res: Response, req: Request):
    if len(a.password) < 6: raise HTTPException(400, "Password must be at least 6 characters")
    if "@" not in a.email or "." not in a.email: raise HTTPException(400, "Enter a valid email address")
    with db() as c:
        if c.execute("SELECT 1 FROM users WHERE email=?", (a.email.lower(),)).fetchone(): raise HTTPException(409, "Email already registered")
        cur = c.execute("INSERT INTO users(email,name,pw,created) VALUES(?,?,?,?)", (a.email.lower(), a.name or a.email.split("@")[0], hashpw(a.password), time.time()))
        uid = cur.lastrowid; tok = secrets.token_urlsafe(32)
        c.execute("INSERT INTO sessions VALUES(?,?,?)", (tok, uid, time.time()))
    set_session_cookie(res, req, tok)
    try: _starter_project(uid, a.name or a.email.split("@")[0])
    except Exception as e: log.warning("starter project failed: %s", e)
    return {"ok": True, "name": a.name, "token": tok}

def _starter_project(uid: int, display: str):
    """Give every new account a ready, published sample site so nothing is empty on first login."""
    base = re.sub(r"[^a-z0-9-]", "-", display.lower()).strip("-")[:20] or "my"
    name = f"{base}-site"; i = 2
    while safe(name).exists(): name = f"{base}-site-{i}"; i += 1
    tpl = TEMPLATES["landing"]; d = safe(name); d.mkdir(parents=True)
    for fn, content in tpl["files"].items():
        p = d / fn; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(content.replace("{{NAME}}", display), encoding="utf-8")
    with db() as c:
        c.execute("INSERT INTO projects(uid,name,kind,created,template) VALUES(?,?,?,?,?)", (uid, name, "static", time.time(), "landing"))
        u = dict(c.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone())
    publish(name, u)
    return name

@app.post("/api/auth/login")
def login(a: Auth, res: Response, req: Request):
    with db() as c:
        u = c.execute("SELECT * FROM users WHERE email=?", (a.email.lower(),)).fetchone()
        if not u or not checkpw(a.password, u["pw"]): raise HTTPException(401, "Invalid email or password")
        tok = secrets.token_urlsafe(32); c.execute("INSERT INTO sessions VALUES(?,?,?)", (tok, u["id"], time.time()))
    set_session_cookie(res, req, tok)
    return {"ok": True, "name": u["name"], "token": tok}

@app.post("/api/auth/logout")
def logout(req: Request, res: Response):
    tok = _tok_from(req)
    with db() as c: c.execute("DELETE FROM sessions WHERE token=?", (tok,))
    for k in ("fv","fvl","fvs_fv_token"): res.delete_cookie(k)
    return {"ok": True}

@app.get("/api/me")
def me(u=Depends(user)):
    with db() as c:
        n = c.execute("SELECT COUNT(*) FROM projects WHERE uid=?", (u["id"],)).fetchone()[0]
        hits = c.execute("SELECT COUNT(*) FROM hits WHERE project IN (SELECT name FROM projects WHERE uid=?)", (u["id"],)).fetchone()[0]
        act = [dict(r) for r in c.execute("SELECT * FROM activity WHERE uid=? ORDER BY ts DESC LIMIT 20", (u["id"],))]
    return {"id": u["id"], "email": u["email"], "name": u["name"], "plan": u["plan"], "projects": n, "total_hits": hits, "activity": act}

# ═══════════════════════════════ TEMPLATES ═══════════════════════════════
from templates import TEMPLATES
try:
    import persist as _persist
    _persist.restore(DATA); _persist.start_backup_loop(DATA)
    @app.middleware("http")
    async def _mark_dirty(request, call_next):
        resp = await call_next(request)
        if request.method in ("POST", "PUT", "DELETE", "PATCH") and resp.status_code < 400 and "/beacon/" not in request.url.path:
            _persist.mark_dirty()
        return resp
except Exception as _e:
    print("persist disabled:", _e)

@app.get("/api/templates")
def templates(): return [{"id": k, **{kk: vv for kk, vv in v.items() if kk != "files"}} for k, v in TEMPLATES.items()]

# ═══════════════════════════════ PROJECTS ═══════════════════════════════
def safe(project: str, file: str = "") -> Path:  # project dirs are private (0700); sandbox gets access only while running
    base = (PROJECTS / project).resolve()
    if not str(base).startswith(str(PROJECTS.resolve())): raise HTTPException(400, "bad path")
    p = (base / file).resolve() if file else base
    if not str(p).startswith(str(base)): raise HTTPException(400, "bad path")
    return p

def own(name, u):
    with db() as c: p = c.execute("SELECT * FROM projects WHERE name=? AND uid=?", (name, u["id"])).fetchone()
    if not p: raise HTTPException(404, "Project not found")
    return dict(p)

class ProjectIn(BaseModel): name: str; template: str = "blank"; kind: str = "static"
class FileIn(BaseModel): content: str
class RenameIn(BaseModel): to: str
class SettingsIn(BaseModel):
    seo_title: Optional[str] = None; seo_desc: Optional[str] = None; ga: Optional[str] = None; password: Optional[str] = None; kind: Optional[str] = None

@app.get("/api/projects")
def list_projects(u=Depends(user)):
    with db() as c:
        rows = c.execute("SELECT p.*, (SELECT COUNT(*) FROM hits h WHERE h.project=p.name) hits, (SELECT COUNT(*) FROM hits h WHERE h.project=p.name AND ts>?) hits24 FROM projects p WHERE uid=? ORDER BY created DESC", (time.time()-86400, u["id"])).fetchall()
    out = []
    for r in rows:
        d = dict(r); pdir = PROJECTS / d["name"]
        d["files"] = sum(1 for _ in pdir.rglob("*") if _.is_file()) if pdir.exists() else 0
        d["size"] = sum(f.stat().st_size for f in pdir.rglob("*") if f.is_file()) if pdir.exists() else 0
        d["running"] = d["name"] in RUNNING
        out.append(d)
    return out

@app.post("/api/projects")
def create_project(p: ProjectIn, u=Depends(user)):
    name = re.sub(r"[^a-z0-9-]", "-", p.name.lower().strip()).strip("-")[:40] or "site"
    d = safe(name)
    if d.exists() or name in ("api", "static", "sites", "app", "admin"): raise HTTPException(409, "Name already taken")
    tpl = TEMPLATES.get(p.template, TEMPLATES["blank"])
    d.mkdir()
    for f, content in tpl["files"].items():
        fp = d / f; fp.parent.mkdir(parents=True, exist_ok=True); fp.write_text(content.replace("{{NAME}}", name), encoding="utf-8")
    with db() as c: c.execute("INSERT INTO projects(uid,name,kind,created,template) VALUES(?,?,?,?,?)", (u["id"], name, tpl.get("kind", p.kind), time.time(), p.template))
    log(u["id"], name, "created", f"from template {p.template}")
    return {"name": name}

@app.post("/api/projects/import")
async def import_zip(name: str, file: UploadFile = File(...), u=Depends(user)):
    name = re.sub(r"[^a-z0-9-]", "-", name.lower())[:40]; d = safe(name)
    if d.exists(): raise HTTPException(409, "Name taken")
    d.mkdir(); z = zipfile.ZipFile(io.BytesIO(await file.read()))
    for m in z.namelist():
        if m.endswith("/") or ".." in m or m.startswith("/"): continue
        parts = m.split("/"); parts = parts[1:] if len(parts) > 1 and all(n.startswith(parts[0] + "/") for n in z.namelist()) else parts
        t = d / "/".join(parts); t.parent.mkdir(parents=True, exist_ok=True); t.write_bytes(z.read(m))
    with db() as c: c.execute("INSERT INTO projects(uid,name,created,template) VALUES(?,?,?,?)", (u["id"], name, time.time(), "import"))
    log(u["id"], name, "imported zip"); return {"name": name}

@app.get("/api/projects/{name}/export")
def export_zip(name: str, u=Depends(user)):
    own(name, u); d = safe(name); buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for f in d.rglob("*"):
            if f.is_file(): z.write(f, f.relative_to(d))
    buf.seek(0)
    return StreamingResponse(buf, media_type="application/zip", headers={"Content-Disposition": f"attachment; filename={name}.zip"})

@app.delete("/api/projects/{name}")
def delete_project(name: str, u=Depends(user)):
    own(name, u); stop_app(name)
    shutil.rmtree(safe(name), ignore_errors=True); shutil.rmtree(SITES / name, ignore_errors=True)
    with db() as c:
        for t in ("projects", "hits", "forms", "versions", "kv", "domains"): c.execute(f"DELETE FROM {t} WHERE {'name' if t=='projects' else 'project'}=?", (name,))
    return {"ok": True}

@app.post("/api/projects/{name}/rename")
def rename_project(name: str, r: RenameIn, u=Depends(user)):
    own(name, u); to = re.sub(r"[^a-z0-9-]", "-", r.to.lower())[:40]
    if safe(to).exists(): raise HTTPException(409, "Name taken")
    safe(name).rename(safe(to))
    if (SITES / name).exists(): (SITES / name).rename(SITES / to)
    with db() as c:
        c.execute("UPDATE projects SET name=? WHERE name=?", (to, name))
        for t in ("hits", "forms", "versions", "kv", "domains"): c.execute(f"UPDATE {t} SET project=? WHERE project=?", (to, name))
    return {"name": to}

@app.post("/api/projects/{name}/duplicate")
def duplicate(name: str, u=Depends(user)):
    own(name, u); to = f"{name}-copy"; i = 2
    while safe(to).exists(): to = f"{name}-copy{i}"; i += 1
    shutil.copytree(safe(name), safe(to))
    with db() as c: c.execute("INSERT INTO projects(uid,name,created,template) VALUES(?,?,?,?)", (u["id"], to, time.time(), "copy"))
    return {"name": to}

@app.get("/api/projects/{name}/settings")
def get_settings(name: str, u=Depends(user)):
    p = own(name, u)
    with db() as c: doms = [dict(r) for r in c.execute("SELECT * FROM domains WHERE project=?", (name,))]
    p["domains"] = doms; return p

@app.put("/api/projects/{name}/settings")
def put_settings(name: str, s: SettingsIn, u=Depends(user)):
    own(name, u)
    with db() as c:
        for k, v in s.dict(exclude_none=True).items(): c.execute(f"UPDATE projects SET {k}=? WHERE name=?", (v, name))
    return {"ok": True}

# ═══════════════════════════════ FILES ═══════════════════════════════
@app.get("/api/projects/{name}/files")
def list_files(name: str, u=Depends(user)):
    own(name, u); d = safe(name)
    return sorted([{"path": str(p.relative_to(d)), "size": p.stat().st_size} for p in d.rglob("*") if p.is_file() and "node_modules" not in p.parts and "__pycache__" not in p.parts], key=lambda x: x["path"])

@app.get("/api/projects/{name}/files/{path:path}")
def read_file(name: str, path: str, u=Depends(user)):
    own(name, u); p = safe(name, path)
    if not p.exists(): raise HTTPException(404, "File not found")
    try: return {"content": p.read_text(encoding="utf-8"), "binary": False}
    except UnicodeDecodeError: return {"content": "", "binary": True, "size": p.stat().st_size}

@app.put("/api/projects/{name}/files/{path:path}")
async def write_file(name: str, path: str, request: Request, u=Depends(user)):
    own(name, u); p = safe(name, path); raw = await request.body()
    if "application/json" in (request.headers.get("content-type") or ""):
        try: content = json.loads(raw or b"{}").get("content", "")
        except Exception: raise HTTPException(400, "Invalid JSON body")
    else: content = raw.decode("utf-8", "replace")
    p.parent.mkdir(parents=True, exist_ok=True); p.write_text(content, encoding="utf-8"); return {"ok": True}

@app.post("/api/projects/{name}/upload")
async def upload(name: str, path: str = "", files: list[UploadFile] = File(...), u=Depends(user)):
    own(name, u); out = []
    for f in files:
        p = safe(name, (path + "/" if path else "") + f.filename); p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(await f.read()); out.append(str(p.relative_to(safe(name))))
    return {"files": out}

@app.delete("/api/projects/{name}/files/{path:path}")
def delete_file(name: str, path: str, u=Depends(user)):
    own(name, u); p = safe(name, path)
    if p.is_dir(): shutil.rmtree(p)
    else: p.unlink(missing_ok=True)
    return {"ok": True}

@app.post("/api/projects/{name}/files/{path:path}/rename")
def rename_file(name: str, path: str, r: RenameIn, u=Depends(user)):
    own(name, u); src = safe(name, path); dst = safe(name, r.to)
    if not src.exists(): raise HTTPException(404, "File not found")
    if dst.exists(): raise HTTPException(409, "A file with that name already exists")
    dst.parent.mkdir(parents=True, exist_ok=True); src.rename(dst); return {"ok": True}

@app.get("/api/projects/{name}/search")
def search_files(name: str, q: str, u=Depends(user)):
    own(name, u); d = safe(name); out = []
    for p in d.rglob("*"):
        if p.is_file():
            try:
                for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
                    if q.lower() in line.lower(): out.append({"file": str(p.relative_to(d)), "line": i, "text": line.strip()[:160]})
            except Exception: pass
        if len(out) > 200: break
    return out

# ═══════════════════════════════ VERSIONS ═══════════════════════════════
@app.get("/api/projects/{name}/versions")
def list_versions(name: str, u=Depends(user)):
    own(name, u)
    with db() as c: return [dict(r) for r in c.execute("SELECT id,label,created FROM versions WHERE project=? ORDER BY created DESC", (name,))]

@app.post("/api/projects/{name}/versions")
def snapshot(name: str, label: str = "", u=Depends(user)):
    own(name, u); vid = f"{name}-{int(time.time()*1000)}"; dst = VERSIONS / vid
    shutil.copytree(safe(name), dst, ignore=shutil.ignore_patterns("node_modules", "__pycache__"))
    with db() as c: c.execute("INSERT INTO versions(project,label,created,path) VALUES(?,?,?,?)", (name, label or datetime.now().strftime("%b %d, %H:%M"), time.time(), str(dst)))
    with db() as c:  # keep 30
        old = c.execute("SELECT id,path FROM versions WHERE project=? ORDER BY created DESC LIMIT -1 OFFSET 30", (name,)).fetchall()
        for o in old: shutil.rmtree(o["path"], ignore_errors=True); c.execute("DELETE FROM versions WHERE id=?", (o["id"],))
    return {"ok": True}

@app.post("/api/projects/{name}/versions/{vid}/restore")
def restore(name: str, vid: int, u=Depends(user)):
    own(name, u)
    with db() as c: v = c.execute("SELECT * FROM versions WHERE id=? AND project=?", (vid, name)).fetchone()
    if not v: raise HTTPException(404)
    snapshot(name, "before restore", u)
    d = safe(name); shutil.rmtree(d); shutil.copytree(v["path"], d); log(u["id"], name, "restored", v["label"]); return {"ok": True}

# ═══════════════════════════════ PUBLISH / SERVE ═══════════════════════════════
INJECT = """<script>(function(){try{navigator.sendBeacon('/api/beacon/%s',JSON.stringify({p:location.pathname,r:document.referrer}))}catch(e){}})();</script>"""

@app.post("/api/projects/{name}/publish")
def publish(name: str, u=Depends(user)):
    p = own(name, u); src = safe(name); dst = SITES / name
    snapshot(name, "publish", u)
    if dst.exists(): shutil.rmtree(dst)
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns("node_modules", "__pycache__", ".git"))
    # inject analytics + GA + SEO defaults + generate sitemap/robots
    pages = []
    for f in dst.rglob("*.html"):
        html = f.read_text(encoding="utf-8", errors="replace")
        if p.get("ga"): html = html.replace("</head>", f'<script async src="https://www.googletagmanager.com/gtag/js?id={p["ga"]}"></script><script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments)}}gtag("js",new Date());gtag("config","{p["ga"]}");</script></head>', 1)
        html = html.replace("</body>", (INJECT % name) + "</body>", 1) if "</body>" in html else html + (INJECT % name)
        f.write_text(html, encoding="utf-8"); pages.append(str(f.relative_to(dst)))
    base = f"/sites/{name}/"
    if not (dst / "sitemap.xml").exists():
        (dst / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + "".join(f"<url><loc>{base}{'' if pg=='index.html' else pg}</loc><lastmod>{datetime.now().date()}</lastmod></url>" for pg in pages) + "</urlset>")
    if not (dst / "robots.txt").exists(): (dst / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {base}sitemap.xml\n", encoding="utf-8")
    with db() as c: c.execute("UPDATE projects SET published=? WHERE name=?", (time.time(), name))
    log(u["id"], name, "published", f"{len(pages)} pages")
    if p["kind"] != "static": start_app(name, p["kind"])
    return {"url": base, "pages": len(pages)}

@app.post("/api/projects/{name}/unpublish")
def unpublish(name: str, u=Depends(user)):
    own(name, u); shutil.rmtree(SITES / name, ignore_errors=True); stop_app(name)
    with db() as c: c.execute("UPDATE projects SET published=NULL WHERE name=?", (name,))
    return {"ok": True}

@app.post("/api/beacon/{name}")
async def beacon(name: str, req: Request):
    try: b = json.loads(await req.body())
    except Exception: b = {}
    ip = req.headers.get("x-forwarded-for", req.client.host if req.client else "").split(",")[0]
    with db() as c: c.execute("INSERT INTO hits(project,path,ref,ua,ip,ts) VALUES(?,?,?,?,?,?)", (name, b.get("p", "/"), b.get("r", ""), req.headers.get("user-agent", "")[:200], ip, time.time()))
    return Response(status_code=204)

@app.api_route("/sites/{name}/{path:path}", methods=["GET", "HEAD"])
@app.api_route("/sites/{name}", methods=["GET", "HEAD"])
async def serve_site(name: str, req: Request, path: str = ""):
    with db() as c: p = c.execute("SELECT * FROM projects WHERE name=?", (name,)).fetchone()
    if not (SITES / name).exists() and not (p and p["kind"] != "static" and name in RUNNING):
        return HTMLResponse(f"<!doctype html><meta charset=utf-8><title>Not found</title><body style='font-family:system-ui;background:#0b0c12;color:#eee;display:grid;place-items:center;height:100vh;margin:0'><div style='text-align:center'><h1 style='font-size:64px;margin:0'>404</h1><p>There's no site published at <b>{name}</b> yet.</p><a href='/' style='color:#a78bfa'>Build one on Forgevia →</a></div>", status_code=404)
    if p and p["password"]:
        if req.cookies.get(f"pw_{name}") != hashlib.md5(p["password"].encode()).hexdigest():
            return HTMLResponse(PW_PAGE % name, status_code=401)
    if p and p["kind"] != "static" and name in RUNNING: return await proxy(name, path, req)
    base = (SITES / name).resolve(); f = (base / (path or "index.html")).resolve()
    if f.is_dir(): f = f / "index.html"
    if not str(f).startswith(str(base)): raise HTTPException(404)
    if not f.exists() and not path.endswith(".html") and (base / (path + ".html")).exists(): f = base / (path + ".html")
    if not f.exists():
        nf = base / "404.html"
        if nf.exists(): return HTMLResponse(nf.read_text(encoding="utf-8"), status_code=404)
        return HTMLResponse(NOT_FOUND, status_code=404)
    return FileResponse(f, headers={"Cache-Control": "public, max-age=60", "X-Powered-By": "Forgevia"})

PW_PAGE = """<!doctype html><html><head><meta charset=utf-8><title>Protected</title><style>body{font-family:system-ui;background:#0b0d12;color:#fff;display:grid;place-items:center;height:100vh;margin:0}form{background:#161a24;padding:32px;border-radius:16px;text-align:center}input{padding:10px;border-radius:8px;border:1px solid #333;background:#0b0d12;color:#fff;margin:12px 0;width:220px}button{padding:10px 20px;border-radius:8px;border:0;background:#7c5cff;color:#fff;cursor:pointer}</style></head><body><form method=post action="/api/unlock/%s"><h2>🔒 Password protected</h2><input name=pw type=password placeholder="Password" autofocus><br><button>Enter</button></form></body></html>"""
NOT_FOUND = """<!doctype html><html><head><meta charset=utf-8><title>404</title><style>body{font-family:system-ui;background:#0b0d12;color:#fff;display:grid;place-items:center;height:100vh;margin:0;text-align:center}h1{font-size:80px;margin:0;background:linear-gradient(90deg,#7c5cff,#22d3ee);-webkit-background-clip:text;color:transparent}a{color:#22d3ee}</style></head><body><div><h1>404</h1><p>This page doesn't exist.</p><small>Powered by <a href="/">Forgevia</a></small></div></body></html>"""

@app.post("/api/unlock/{name}")
async def unlock(name: str, req: Request):
    form = await req.form(); pw = form.get("pw", "")
    with db() as c: p = c.execute("SELECT password FROM projects WHERE name=?", (name,)).fetchone()
    r = RedirectResponse(f"/sites/{name}/", status_code=303)
    if p and p["password"] == pw: r.set_cookie(f"pw_{name}", hashlib.md5(pw.encode()).hexdigest(), max_age=86400)
    return r

# ═══════════════════════════════ APP HOSTING (Python / Node) ═══════════════════════════════
RUNNING: dict = {}   # name -> {proc, port, log}

def free_port():
    used = {v["port"] for v in RUNNING.values()}
    for p in FREE_PORTS:
        if p in used: continue
        with socket.socket() as s:
            if s.connect_ex(("127.0.0.1", p)) != 0: return p
    raise HTTPException(503, "No free ports")

def start_app(name, kind):
    stop_app(name); d = safe(name); port = free_port(); env = {**os.environ, "PORT": str(port), "FORGEVIA_PROJECT": name}
    if kind == "python":
        entry = "main.py" if (d / "main.py").exists() else "app.py"
        if (d / "requirements.txt").exists(): subprocess.run(["pip", "install", "-q", "-r", "requirements.txt"], cwd=d, capture_output=True, timeout=180)
        cmd = ["python3", entry]
    else:
        pkg = d / "package.json"; entry = "index.js"
        if pkg.exists():
            try: entry = json.loads(pkg.read_text(encoding="utf-8")).get("main", "index.js")
            except Exception: pass
            if not (d / "node_modules").exists(): subprocess.run(["npm", "install", "--silent"], cwd=d, capture_output=True, timeout=300)
        cmd = ["node", entry]
    logf = open(d / ".forgevia.log", "w", encoding="utf-8")
    env = {"PATH": "/usr/local/bin:/usr/bin:/bin", "HOME": str(d), "LANG": "C.UTF-8", "PORT": str(port), "FORGEVIA_PROJECT": name}
    if os.name == "nt":
        env = {**os.environ, "PORT": str(port), "FORGEVIA_PROJECT": name, "HOME": str(d)}
        if cmd[0] == "python3": cmd[0] = sys.executable
        proc = subprocess.Popen(cmd, cwd=d, env=env, stdout=logf, stderr=subprocess.STDOUT, creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0))
        RUNNING[name] = {"proc": proc, "port": port, "started": time.time(), "cmd": " ".join(cmd)}
        time.sleep(1.5); return port
    if HAVE_SANDBOX:
        # user apps run as the unprivileged sandbox user; give it access to this project dir only
        subprocess.run(["chmod", "-R", "a+rwX", str(d)], capture_output=True)
        cmd = ["sudo", "-n", "-u", SANDBOX_USER, "env", "-i"] + [f"{k}={v}" for k, v in env.items()] + ["bash", "-c", "ulimit -v 4194304 -u 256; exec " + " ".join(shlex.quote(c) for c in cmd)]
    proc = subprocess.Popen(cmd, cwd=d, env=env, stdout=logf, stderr=subprocess.STDOUT, start_new_session=True)
    RUNNING[name] = {"proc": proc, "port": port, "started": time.time(), "cmd": " ".join(cmd)}
    time.sleep(1.5); return port

def stop_app(name):
    r = RUNNING.pop(name, None)
    if r:
        if os.name == "nt":
            try: subprocess.run(["taskkill", "/F", "/T", "/PID", str(r["proc"].pid)], capture_output=True, timeout=10)
            except Exception: pass
            return
        try: os.killpg(os.getpgid(r["proc"].pid), signal.SIGTERM)
        except Exception: pass
        if HAVE_SANDBOX:
            try: subprocess.run(["chmod", "-R", "o-rwx", str(safe(name))], capture_output=True)
            except Exception: pass
            try: subprocess.run(["sudo", "-n", "pkill", "-TERM", "-g", str(os.getpgid(r["proc"].pid))], capture_output=True, timeout=5)
            except Exception: pass
            try: subprocess.run(["sudo", "-n", "pkill", "-TERM", "-u", SANDBOX_USER, "-f", f"FORGEVIA_PROJECT={name}"], capture_output=True, timeout=5)
            except Exception: pass

async def proxy(name, path, req: Request):
    port = RUNNING[name]["port"]; url = f"http://127.0.0.1:{port}/{path}" + (f"?{req.url.query}" if req.url.query else "")
    try:
        async with httpx.AsyncClient(timeout=30) as cl:
            r = await cl.request(req.method, url, headers={k: v for k, v in req.headers.items() if k.lower() not in ("host", "content-length")}, content=await req.body())
        return Response(r.content, r.status_code, headers={k: v for k, v in r.headers.items() if k.lower() in ("content-type", "cache-control", "location", "set-cookie")})
    except Exception as e: return HTMLResponse(f"<pre>App not responding on port {port}: {e}\n\nCheck logs in the Forgevia dashboard.</pre>", 502)

@app.post("/api/projects/{name}/app/start")
def app_start(name: str, u=Depends(user)):
    p = own(name, u); port = start_app(name, p["kind"] if p["kind"] != "static" else "python"); log(u["id"], name, "app started"); return {"port": port}
@app.post("/api/projects/{name}/app/stop")
def app_stop(name: str, u=Depends(user)): own(name, u); stop_app(name); return {"ok": True}
@app.get("/api/projects/{name}/app/status")
def app_status(name: str, u=Depends(user)):
    own(name, u); r = RUNNING.get(name); logp = safe(name) / ".forgevia.log"
    alive = r and r["proc"].poll() is None
    return {"running": bool(alive), "port": r["port"] if r else None, "uptime": time.time() - r["started"] if r else 0, "cmd": r["cmd"] if r else None, "log": logp.read_text(encoding="utf-8", errors="replace")[-8000:] if logp.exists() else ""}

# ═══════════════════════════════ TERMINAL / RUN ═══════════════════════════════
class RunIn(BaseModel): code: str = ""; lang: str = "python"; cmd: str = ""; project: Optional[str] = None; stdin: str = ""
LANGS = {"python": ["python3", "-c"], "node": ["node", "-e"], "bash": ["bash", "-c"]}

@app.post("/api/run")
def run_code(r: RunIn, u=Depends(user)):
    cwd = safe(r.project) if r.project else DATA
    if r.cmd:
        if re.search(r"\b(rm\s+-rf\s+/|mkfs|shutdown|reboot|:\(\)\{)", r.cmd): raise HTTPException(400, "Command blocked")
        cmd = ["bash", "-c", r.cmd]
    else:
        if r.lang not in LANGS: raise HTTPException(400, "Unsupported language")
        cmd = LANGS[r.lang] + [r.code]
    t = time.time()
    try:
        res = sandbox_run(cmd, cwd, r.stdin, project=bool(r.project))
        err = res.stderr
        if res.returncode in (137, 124) or "Killed" in err[-300:]: err = (err.strip() + "\n⏱ Timed out / exceeded CPU limit (20s)").strip()
        return {"stdout": res.stdout[-50000:], "stderr": err[-10000:], "code": res.returncode, "ms": int((time.time()-t)*1000)}
    except subprocess.TimeoutExpired: return {"stdout": "", "stderr": "⏱ Timed out after 30s", "code": -1, "ms": 30000}

# ── Sandbox: user code runs as an unprivileged user, in a throwaway dir, with CPU/memory/file limits ──
SANDBOX_USER = os.environ.get("FV_SANDBOX_USER", "fvrun")
def _have_sandbox_user():
    if os.name == "nt": return False
    try: import pwd; pwd.getpwnam(SANDBOX_USER); return subprocess.run(["sudo", "-n", "-u", SANDBOX_USER, "true"], capture_output=True, timeout=5).returncode == 0
    except Exception: return False
HAVE_SANDBOX = _have_sandbox_user()
def sandbox_run(cmd, cwd, stdin, project=False):
    import tempfile
    limits = "ulimit -t 20 -v 2097152 -f 20480 -u 64 -n 128;"
    if project:
        # run inside a temporary copy of the project so user code cannot modify server data
        work = tempfile.mkdtemp(prefix="fvrun_"); shutil.copytree(cwd, work, dirs_exist_ok=True, ignore=shutil.ignore_patterns("node_modules", ".git"))
    else:
        work = tempfile.mkdtemp(prefix="fvrun_")
    os.chmod(work, 0o777)
    try:
        inner = " ".join(shlex.quote(c) for c in cmd)
        env = {"PATH": "/usr/local/bin:/usr/bin:/bin", "HOME": work, "LANG": "C.UTF-8", "PYTHONDONTWRITEBYTECODE": "1"}
        if os.name == "nt":
            wenv = {"PATH": os.environ.get("PATH", ""), "SYSTEMROOT": os.environ.get("SYSTEMROOT", r"C:\Windows"), "TEMP": work, "TMP": work, "HOME": work, "USERPROFILE": work, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8"}
            wcmd = list(cmd)
            if wcmd and wcmd[0] == "python3": wcmd[0] = sys.executable
            if wcmd and wcmd[0] == "bash": wcmd = ["cmd", "/c"] + wcmd[2:]
            return subprocess.run(wcmd, capture_output=True, text=True, timeout=30, input=stdin, env=wenv, cwd=work, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        if HAVE_SANDBOX:
            full = ["sudo", "-n", "-u", SANDBOX_USER, "env", "-i"] + [f"{k}={v}" for k, v in env.items()] + ["bash", "-c", limits + "cd " + shlex.quote(work) + " && " + inner]
        else:
            full = ["bash", "-c", limits + "cd " + shlex.quote(work) + " && " + inner]
        return subprocess.run(full, capture_output=True, text=True, timeout=30, input=stdin, env=env)
    finally:
        try:
            if HAVE_SANDBOX: subprocess.run(["sudo", "-n", "rm", "-rf", work], capture_output=True, timeout=10)
            else: shutil.rmtree(work, ignore_errors=True)
        except Exception: pass

# ═══════════════════════════════ FORMS ═══════════════════════════════
@app.post("/api/forms/{name}/{form}")
@app.post("/api/forms/{name}")
async def form_submit(name: str, req: Request, form: str = "default"):
    ct = req.headers.get("content-type", "")
    data = json.loads(await req.body()) if "json" in ct else {k: v for k, v in (await req.form()).items()}
    with db() as c: c.execute("INSERT INTO forms(project,form,data,ts) VALUES(?,?,?,?)", (name, form, json.dumps(data), time.time()))
    nxt = data.get("_next") or req.headers.get("referer")
    if "json" in ct or "application/json" in req.headers.get("accept", ""): return {"ok": True}
    return HTMLResponse(f'<!doctype html><meta charset=utf-8><body style="font-family:system-ui;text-align:center;padding:80px"><h2>✅ Thanks! Your submission was received.</h2><a href="{nxt or "/"}">← Go back</a>')

@app.get("/api/projects/{name}/forms")
def list_forms(name: str, u=Depends(user)):
    own(name, u)
    with db() as c: return [{**dict(r), "data": json.loads(r["data"])} for r in c.execute("SELECT * FROM forms WHERE project=? ORDER BY ts DESC LIMIT 500", (name,))]

@app.delete("/api/projects/{name}/forms/{fid}")
def del_form(name: str, fid: int, u=Depends(user)):
    own(name, u)
    with db() as c: c.execute("DELETE FROM forms WHERE id=? AND project=?", (fid, name))
    return {"ok": True}

# ═══════════════════════════════ KV DATABASE (for user apps) ═══════════════════════════════
@app.get("/api/kv/{name}")
def kv_list(name: str):
    with db() as c: return {r["k"]: json.loads(r["v"]) for r in c.execute("SELECT k,v FROM kv WHERE project=?", (name,))}
@app.get("/api/kv/{name}/{k}")
def kv_get(name: str, k: str):
    with db() as c: r = c.execute("SELECT v FROM kv WHERE project=? AND k=?", (name, k)).fetchone()
    if not r: raise HTTPException(404)
    return json.loads(r["v"])
@app.put("/api/kv/{name}/{k}")
async def kv_put(name: str, k: str, req: Request):
    v = await req.body()
    with db() as c:
        n = c.execute("SELECT COUNT(*) FROM kv WHERE project=?", (name,)).fetchone()[0]
        if n > 5000: raise HTTPException(429, "KV limit reached")
        c.execute("INSERT OR REPLACE INTO kv VALUES(?,?,?)", (name, k, v.decode() or "null"))
    return {"ok": True}
@app.delete("/api/kv/{name}/{k}")
def kv_del(name: str, k: str):
    with db() as c: c.execute("DELETE FROM kv WHERE project=? AND k=?", (name, k))
    return {"ok": True}

# ═══════════════════════════════ ANALYTICS ═══════════════════════════════
@app.get("/api/projects/{name}/analytics")
def analytics(name: str, days: int = 30, u=Depends(user)):
    own(name, u); since = time.time() - days*86400
    with db() as c:
        rows = [dict(r) for r in c.execute("SELECT * FROM hits WHERE project=? AND ts>?", (name, since))]
    total = len(rows); uniq = len({r["ip"] for r in rows}); daily = {}
    for r in rows: d = datetime.fromtimestamp(r["ts"]).strftime("%Y-%m-%d"); daily[d] = daily.get(d, 0) + 1
    def top(key, n=10, f=lambda x: x):
        cnt = {}
        for r in rows: k = f(r[key]) or "(direct)"; cnt[k] = cnt.get(k, 0) + 1
        return sorted(cnt.items(), key=lambda x: -x[1])[:n]
    def dev(ua):
        ua = ua.lower(); return "Bot" if "bot" in ua or "crawl" in ua else "Mobile" if "mobile" in ua or "android" in ua else "Tablet" if "ipad" in ua or "tablet" in ua else "Desktop"
    def browser(ua):
        for b in ("Edg", "OPR", "Chrome", "Safari", "Firefox"):
            if b in ua: return {"Edg": "Edge", "OPR": "Opera"}.get(b, b)
        return "Other"
    return {"total": total, "unique": uniq, "daily": sorted(daily.items()), "pages": top("path"), "referrers": top("ref", f=lambda r: urlparse(r).netloc if r else ""),
            "devices": top("ua", f=dev), "browsers": top("ua", f=browser), "recent": rows[-20:][::-1]}

# ═══════════════════════════════ SEO SUITE ═══════════════════════════════
class UrlIn(BaseModel): url: str
class KwIn(BaseModel): keyword: str
UA = {"User-Agent": "Mozilla/5.0 (compatible; ForgeviaBot/2.0; +https://forgevia.com/bot)"}

def fetch(url: str):
    if not url.startswith("http"): url = "https://" + url
    t = time.time(); r = httpx.get(url, follow_redirects=True, timeout=20, headers=UA); return str(r.url), r, time.time() - t

def audit_html(url, html, r=None, elapsed=0):
    soup = BeautifulSoup(html, "lxml"); checks = []; score = 100
    def add(cat, name, ok, detail, weight=5, fix=""):
        nonlocal score; checks.append({"cat": cat, "name": name, "ok": bool(ok), "detail": detail, "fix": fix if not ok else "", "weight": weight})
        if not ok: score -= weight
    title = (soup.title.string or "").strip() if soup.title else ""
    add("Content", "Title tag", 10 <= len(title) <= 60, f'"{title}" ({len(title)} chars)' if title else "Missing", 10, "Add a unique <title> of 10–60 characters containing your main keyword.")
    m = soup.find("meta", attrs={"name": "description"}); d = (m.get("content") or "").strip() if m else ""
    add("Content", "Meta description", 50 <= len(d) <= 160, f"{len(d)} chars" if d else "Missing", 8, "Write a compelling 50–160 char description; it becomes your search snippet.")
    h1 = soup.find_all("h1"); add("Content", "Exactly one H1", len(h1) == 1, f"{len(h1)} found" + (f': "{h1[0].get_text(strip=True)[:60]}"' if h1 else ""), 8, "Use a single H1 that states the page topic.")
    hs = [int(h.name[1]) for h in soup.find_all(re.compile("^h[1-6]$"))]
    skips = any(b - a > 1 for a, b in zip(hs, hs[1:])) if hs else True
    add("Content", "Heading hierarchy", hs and not skips, f"{len(hs)} headings" + (" — levels skipped" if skips else ""), 3, "Don't skip heading levels (H1→H2→H3).")
    text = soup.get_text(" ", strip=True); words = len(text.split())
    add("Content", "Word count", words >= 300, f"{words} words", 6, "Thin content ranks poorly; aim for 300+ meaningful words.")
    add("Technical", "Viewport meta", soup.find("meta", attrs={"name": "viewport"}) is not None, "Mobile-friendly viewport", 8, 'Add <meta name="viewport" content="width=device-width, initial-scale=1">.')
    add("Technical", "HTML lang", soup.html is not None and soup.html.get("lang"), f"lang={soup.html.get('lang') if soup.html else None}", 3, 'Set <html lang="en"> so search engines know the language.')
    add("Technical", "Charset", soup.find("meta", charset=True) is not None or soup.find("meta", attrs={"http-equiv": "Content-Type"}) is not None, "UTF-8 declared", 2, 'Add <meta charset="UTF-8"> as the first tag in <head>.')
    can = soup.find("link", rel="canonical"); add("Technical", "Canonical URL", can is not None, can.get("href") if can else "Missing", 5, 'Add <link rel="canonical" href="..."> to avoid duplicate-content penalties.')
    add("Technical", "HTTPS", url.startswith("https"), url, 10, "Serve over HTTPS — it's a confirmed ranking signal.")
    add("Technical", "Favicon", soup.find("link", rel=re.compile("icon")) is not None, "Icon link", 1, 'Add <link rel="icon" href="/favicon.ico">.')
    robots_meta = soup.find("meta", attrs={"name": "robots"}); ni = robots_meta and "noindex" in (robots_meta.get("content") or "")
    add("Technical", "Indexable", not ni, "noindex present!" if ni else "Page is indexable", 15, "Remove noindex from the robots meta tag.")
    if r is not None:
        add("Performance", "Response time", elapsed < 1.0, f"{elapsed*1000:.0f} ms (TTFB)", 8, "Use caching/CDN; aim for < 1000 ms.")
        add("Performance", "Page size", len(r.content) < 1_000_000, f"{len(r.content)/1024:.0f} KB HTML", 4, "Minify HTML and defer non-critical resources.")
        add("Performance", "Compression", "gzip" in r.headers.get("content-encoding", "") or "br" in r.headers.get("content-encoding", ""), r.headers.get("content-encoding", "none"), 4, "Enable gzip/brotli compression on your server.")
        add("Performance", "Status code", r.status_code == 200, f"HTTP {r.status_code}", 15, "Page must return 200.")
    scripts = soup.find_all("script", src=True); blocking = [s for s in scripts if not s.get("async") and not s.get("defer")]
    add("Performance", "Non-blocking scripts", len(blocking) <= 2, f"{len(blocking)} render-blocking of {len(scripts)}", 4, "Add defer/async to script tags.")
    imgs = soup.find_all("img"); noalt = [i for i in imgs if not (i.get("alt") or "").strip()]
    add("Images", "Alt text", not noalt, f"{len(noalt)}/{len(imgs)} missing alt", 6, "Describe every image in its alt attribute.")
    lazy = [i for i in imgs if i.get("loading") == "lazy"]
    add("Images", "Lazy loading", len(imgs) < 4 or lazy, f"{len(lazy)}/{len(imgs)} lazy", 2, 'Add loading="lazy" to below-the-fold images.')
    add("Social", "Open Graph", soup.find("meta", property="og:title") and soup.find("meta", property="og:image"), "og:title + og:image", 5, "Add og:title, og:description, og:image for rich social previews.")
    add("Social", "Twitter card", soup.find("meta", attrs={"name": "twitter:card"}) is not None, "twitter:card", 2, 'Add <meta name="twitter:card" content="summary_large_image">.')
    ld = soup.find_all("script", type="application/ld+json"); types = []
    for s in ld:
        try: j = json.loads(s.string or ""); types.append(j.get("@type", "?") if isinstance(j, dict) else "list")
        except Exception: types.append("invalid")
    add("Rich results", "Structured data", ld and "invalid" not in types, ", ".join(types) or "No JSON-LD", 5, "Add JSON-LD schema (Organization, Article, Product, FAQ...).")
    links = soup.find_all("a", href=True); host = urlparse(url).netloc
    internal = [l for l in links if urlparse(urljoin(url, l["href"])).netloc == host]; ext = len(links) - len(internal)
    add("Links", "Internal links", len(internal) >= 3, f"{len(internal)} internal, {ext} external", 4, "Link to at least 3 related internal pages.")
    generic = [l for l in links if l.get_text(strip=True).lower() in ("click here", "here", "read more", "link")]
    add("Links", "Descriptive anchors", len(generic) <= 1, f"{len(generic)} generic anchors", 2, 'Replace "click here" with descriptive anchor text.')
    ext_nofollow = [l for l in links if urlparse(urljoin(url, l["href"])).netloc != host and l["href"].startswith("http") and l.get("target") == "_blank" and "noopener" not in (l.get("rel") or [])]
    add("Links", "Safe external links", not ext_nofollow, f"{len(ext_nofollow)} target=_blank without noopener", 1, 'Add rel="noopener" to target="_blank" links.')
    # keyword density
    wl = re.findall(r"[a-z]{4,}", text.lower()); stop = set("this that with from have your about more they will been were what when there their which would there also into than them then some only over such just like".split())
    freq = {}
    for w in wl:
        if w not in stop: freq[w] = freq.get(w, 0) + 1
    kws = sorted(freq.items(), key=lambda x: -x[1])[:12]
    return {"score": max(score, 0), "title": title, "description": d, "h1": [h.get_text(strip=True) for h in h1], "words": words, "checks": checks, "keywords": [{"word": w, "count": n, "density": round(n/max(len(wl),1)*100, 2)} for w, n in kws],
            "passed": sum(1 for c in checks if c["ok"]), "total": len(checks)}

@app.post("/api/seo/audit")
def seo_audit(body: UrlIn, u=Depends(user)):
    try: url, r, el = fetch(body.url)
    except Exception as e: raise HTTPException(400, f"Could not fetch: {e}")
    res = audit_html(url, r.text, r, el); res["url"] = url; res["status"] = r.status_code
    for f in ("robots.txt", "sitemap.xml"):
        try: res[f] = httpx.get(urljoin(url, "/" + f), timeout=6, headers=UA).status_code == 200
        except Exception: res[f] = False
    res["serp"] = {"title": (res["title"] or url)[:60], "url": url, "desc": (res["description"] or "No description")[:160]}
    log(u["id"], None, "seo audit", url); return res

@app.post("/api/seo/crawl")
def seo_crawl(body: UrlIn, limit: int = 25, u=Depends(user)):
    """Crawl an entire site, audit every page, find broken links."""
    try: start, r, _ = fetch(body.url)
    except Exception as e: raise HTTPException(400, f"Could not fetch: {e}")
    host = urlparse(start).netloc; seen = {start}; queue = [start]; pages = []; broken = []
    while queue and len(pages) < limit:
        url = queue.pop(0)
        try: url, r, el = fetch(url)
        except Exception as e: broken.append({"url": url, "error": str(e)[:80]}); continue
        if r.status_code >= 400: broken.append({"url": url, "error": f"HTTP {r.status_code}"}); continue
        if "html" not in r.headers.get("content-type", ""): continue
        a = audit_html(url, r.text, r, el)
        pages.append({"url": url, "score": a["score"], "title": a["title"], "words": a["words"], "status": r.status_code, "ms": int(el*1000), "issues": [c["name"] for c in a["checks"] if not c["ok"]]})
        soup = BeautifulSoup(r.text, "lxml")
        for l in soup.find_all("a", href=True):
            h = urljoin(url, l["href"]).split("#")[0]
            if urlparse(h).netloc == host and h not in seen and not re.search(r"\.(pdf|jpg|png|zip|mp4)$", h, re.I): seen.add(h); queue.append(h)
    dup_titles = {}
    for p in pages: dup_titles.setdefault(p["title"], []).append(p["url"])
    return {"start": start, "pages": pages, "broken": broken, "avg": round(sum(p["score"] for p in pages)/max(len(pages),1)), "duplicate_titles": {k: v for k, v in dup_titles.items() if len(v) > 1 and k}}

@app.post("/api/seo/keywords")
def seo_keywords(body: KwIn, u=Depends(user)):
    """Keyword ideas via Google/Bing autosuggest + question variants."""
    kw = body.keyword.strip(); ideas = set()
    try:
        r = httpx.get("https://suggestqueries.google.com/complete/search", params={"client": "firefox", "q": kw}, timeout=8, headers=UA)
        ideas.update(r.json()[1])
    except Exception: pass
    for pre in ("how to", "best", "what is", "why", "vs", "free", "cheap", "near me", "for beginners", "2026"):
        try:
            q = f"{pre} {kw}" if pre not in ("vs", "near me", "for beginners", "2026", "free", "cheap") else f"{kw} {pre}"
            r = httpx.get("https://suggestqueries.google.com/complete/search", params={"client": "firefox", "q": q}, timeout=6, headers=UA)
            ideas.update(r.json()[1][:5])
        except Exception: pass
    for l in "abcdefghijklmnopqrstuvwxyz"[:10]:
        try: ideas.update(httpx.get("https://suggestqueries.google.com/complete/search", params={"client": "firefox", "q": f"{kw} {l}"}, timeout=5, headers=UA).json()[1][:3])
        except Exception: pass
    out = sorted(ideas - {kw}, key=lambda s: (len(s.split()), s))
    questions = [i for i in out if re.match(r"^(how|what|why|when|where|who|can|is|are|does|do|should)\b", i)]
    return {"keyword": kw, "ideas": out[:120], "questions": questions[:30], "longtail": [i for i in out if len(i.split()) >= 4][:40], "count": len(out)}

class MetaGen(BaseModel): topic: str; keywords: str = ""; brand: str = ""; type: str = "website"
@app.post("/api/seo/generate")
def seo_generate(m: MetaGen, u=Depends(user)):
    kw = [k.strip() for k in m.keywords.split(",") if k.strip()]; main = kw[0] if kw else m.topic
    title = f"{m.topic} — {main.title()}" if kw and main.lower() not in m.topic.lower() else m.topic
    if m.brand: title = f"{title} | {m.brand}"
    desc = f"{m.topic}. Discover {', '.join(kw[:3]) or 'everything you need'}{' with ' + m.brand if m.brand else ''}. Fast, reliable and easy to get started."
    ld = {"@context": "https://schema.org", "@type": {"website": "WebSite", "article": "Article", "product": "Product", "business": "LocalBusiness", "faq": "FAQPage"}.get(m.type, "WebSite"), "name": m.topic, "description": desc[:160]}
    if m.brand: ld["publisher" if m.type == "article" else "brand"] = {"@type": "Organization", "name": m.brand}
    slug = re.sub(r"[^a-z0-9]+", "-", main.lower()).strip("-")
    head = f'''<title>{title[:60]}</title>
<meta name="description" content="{desc[:160]}">
<meta name="keywords" content="{', '.join(kw)}">
<link rel="canonical" href="https://example.com/{slug}">
<meta property="og:type" content="{m.type if m.type in ('website','article') else 'website'}">
<meta property="og:title" content="{title[:60]}">
<meta property="og:description" content="{desc[:160]}">
<meta property="og:image" content="https://example.com/og.jpg">
<meta name="twitter:card" content="summary_large_image">
<script type="application/ld+json">{json.dumps(ld, indent=1)}</script>'''
    return {"title": title[:60], "description": desc[:160], "slug": slug, "head": head, "jsonld": ld, "h1": m.topic, "outline": [f"What is {main}?", f"Why {main} matters", f"How to get started with {main}", f"{main.title()}: best practices", "FAQ", "Conclusion"]}

@app.post("/api/seo/fix/{name}")
def seo_autofix(name: str, u=Depends(user)):
    """Auto-fix common SEO problems across all HTML files in a project."""
    p = own(name, u); d = safe(name); fixed = []
    for f in d.rglob("*.html"):
        html = f.read_text(encoding="utf-8", errors="replace"); soup = BeautifulSoup(html, "lxml"); changed = []
        if not soup.head: continue
        if not soup.find("meta", charset=True): soup.head.insert(0, soup.new_tag("meta", charset="UTF-8")); changed.append("charset")
        if not soup.find("meta", attrs={"name": "viewport"}): t = soup.new_tag("meta"); t["name"] = "viewport"; t["content"] = "width=device-width, initial-scale=1"; soup.head.insert(1, t); changed.append("viewport")
        if soup.html and not soup.html.get("lang"): soup.html["lang"] = "en"; changed.append("lang")
        h1 = soup.find("h1"); title_txt = (soup.title.string if soup.title and soup.title.string else "") or (h1.get_text(strip=True) if h1 else "") or p.get("seo_title") or name.replace("-", " ").title()
        if not soup.title: t = soup.new_tag("title"); t.string = title_txt[:60]; soup.head.append(t); changed.append("title")
        if not soup.find("meta", attrs={"name": "description"}):
            txt = soup.get_text(" ", strip=True)[:155] or p.get("seo_desc") or f"{title_txt} — built with Forgevia."
            t = soup.new_tag("meta"); t["name"] = "description"; t["content"] = txt; soup.head.append(t); changed.append("description")
        if not soup.find("meta", property="og:title"):
            for k, v in (("og:title", title_txt[:60]), ("og:type", "website"), ("og:description", (soup.find("meta", attrs={"name": "description"}) or {}).get("content", ""))):
                t = soup.new_tag("meta"); t["property"] = k; t["content"] = v; soup.head.append(t)
            t = soup.new_tag("meta"); t["name"] = "twitter:card"; t["content"] = "summary_large_image"; soup.head.append(t); changed.append("open graph")
        if not soup.find("link", rel="canonical"): t = soup.new_tag("link", rel="canonical", href=f"/sites/{name}/" + ("" if f.name == "index.html" else str(f.relative_to(d)))); soup.head.append(t); changed.append("canonical")
        n = 0
        for img in soup.find_all("img"):
            if not (img.get("alt") or "").strip(): img["alt"] = re.sub(r"[-_]+", " ", Path(img.get("src", "image")).stem).strip() or "image"; n += 1
            if not img.get("loading"): img["loading"] = "lazy"
        if n: changed.append(f"{n} alt tags")
        for s in soup.find_all("script", src=True):
            if not s.get("async") and not s.get("defer"): s["defer"] = ""
        for a in soup.find_all("a", target="_blank"):
            if "noopener" not in (a.get("rel") or []): a["rel"] = (a.get("rel") or []) + ["noopener"]
        if changed: f.write_text(str(soup), encoding="utf-8"); fixed.append({"file": str(f.relative_to(d)), "fixed": changed})
    log(u["id"], name, "seo autofix", f"{len(fixed)} files"); return {"fixed": fixed}

# ═══════════════════════════════ SCRAPER ═══════════════════════════════
class ScrapeIn(BaseModel):
    url: str; selector: str = ""; mode: str = "text"; attr: str = ""; pages: int = 1; next_selector: str = ""
    fields: Optional[dict] = None  # {"title": "h2 a", "price": ".price"}  → structured rows

@app.post("/api/scrape")
def scrape(body: ScrapeIn, u=Depends(user)):
    url = body.url; results = []; visited = []
    for _ in range(max(1, min(body.pages, 20))):
        try: url, r, _ = fetch(url)
        except Exception as e:
            if not results: raise HTTPException(400, f"Could not fetch: {e}")
            break
        visited.append(url); soup = BeautifulSoup(r.text, "lxml")
        for s in soup(["script", "style", "noscript", "svg"]): s.decompose()
        m = body.mode
        if body.fields:
            container = soup.select(body.selector) if body.selector else [soup]
            for c in container:
                row = {}
                for k, sel in body.fields.items():
                    sel, _, at = sel.partition("@"); e = c.select_one(sel)
                    row[k] = (e.get(at) if at and e else e.get_text(" ", strip=True) if e else None)
                    if at in ("href", "src") and row[k]: row[k] = urljoin(url, row[k])
                if any(row.values()): results.append(row)
        elif body.selector:
            for e in soup.select(body.selector):
                if body.attr: v = e.get(body.attr); results.append(urljoin(url, v) if v and body.attr in ("href", "src") else v)
                else: results.append(e.get_text(" ", strip=True))
        elif m == "links": results += [{"text": a.get_text(strip=True)[:100], "href": urljoin(url, a["href"])} for a in soup.find_all("a", href=True)]
        elif m == "images": results += [{"alt": i.get("alt", ""), "src": urljoin(url, i.get("src") or i.get("data-src") or "")} for i in soup.find_all("img")]
        elif m == "headings": results += [{"tag": h.name, "text": h.get_text(strip=True)} for h in soup.find_all(re.compile("^h[1-6]$"))]
        elif m == "emails": results += sorted(set(re.findall(r"[\w.+-]+@[\w-]+\.[\w.]+", r.text)))
        elif m == "phones": results += sorted(set(re.findall(r"\+?\d[\d\s().-]{8,}\d", soup.get_text())))
        elif m == "meta":
            results.append({"title": soup.title.string if soup.title else None, **{(mt.get("name") or mt.get("property")): mt.get("content") for mt in soup.find_all("meta") if (mt.get("name") or mt.get("property"))}})
        elif m == "table":
            for t in soup.find_all("table"):
                rows = [[c.get_text(" ", strip=True) for c in tr.find_all(["td", "th"])] for tr in t.find_all("tr")]
                if rows: results.append(rows)
        elif m == "json":
            for s in soup.find_all("script", type="application/ld+json"):
                try: results.append(json.loads(s.string))
                except Exception: pass
        elif m == "markdown":
            out = []
            for el in soup.find_all(["h1", "h2", "h3", "p", "li", "a"]):
                t = el.get_text(" ", strip=True)
                if not t: continue
                if el.name[0] == "h": out.append("#" * int(el.name[1]) + " " + t)
                elif el.name == "li": out.append("- " + t)
                elif el.name == "p": out.append(t)
            results.append("\n\n".join(out))
        else: results.append(soup.get_text("\n", strip=True))
        if body.pages > 1 and body.next_selector:
            nx = soup.select_one(body.next_selector)
            if nx and nx.get("href"): url = urljoin(url, nx["href"]); continue
        break
    if body.mode in ("text", "markdown") and not body.selector and not body.fields: results = "\n\n---\n\n".join(results)
    log(u["id"], None, "scrape", body.url)
    return {"url": body.url, "visited": visited, "count": len(results) if isinstance(results, list) else None, "data": results[:2000] if isinstance(results, list) else results[:100000]}

@app.post("/api/scrape/screenshot")
def scrape_preview(body: UrlIn, u=Depends(user)):
    """Return page structure summary to help build selectors."""
    url, r, _ = fetch(body.url); soup = BeautifulSoup(r.text, "lxml")
    classes = {}
    for el in soup.find_all(class_=True):
        for c in el.get("class", []): classes[c] = classes.get(c, 0) + 1
    ids = [el.get("id") for el in soup.find_all(id=True)][:40]
    return {"title": soup.title.string if soup.title else "", "classes": sorted(classes.items(), key=lambda x: -x[1])[:40], "ids": ids, "tables": len(soup.find_all("table")), "forms": len(soup.find_all("form")), "images": len(soup.find_all("img")), "links": len(soup.find_all("a"))}

# ═══════════════════════════════ UPTIME MONITOR ═══════════════════════════════
def check_monitor(m):
    t = time.time()
    try: s = httpx.get(m["url"], timeout=15, follow_redirects=True, headers=UA).status_code
    except Exception: s = 0
    ms = int((time.time()-t)*1000); up = 200 <= s < 400
    with db() as c:
        c.execute("UPDATE monitors SET last_status=?,last_ms=?,last_check=?,up_count=up_count+?,down_count=down_count+? WHERE id=?", (s, ms, time.time(), int(up), int(not up), m["id"]))
        c.execute("INSERT INTO monitor_log(mid,status,ms,ts) VALUES(?,?,?,?)", (m["id"], s, ms, time.time()))
        c.execute("DELETE FROM monitor_log WHERE mid=? AND id NOT IN (SELECT id FROM monitor_log WHERE mid=? ORDER BY ts DESC LIMIT 500)", (m["id"], m["id"]))

def monitor_loop():
    while True:
        try:
            with db() as c: ms = [dict(r) for r in c.execute("SELECT * FROM monitors")]
            for m in ms:
                if time.time() - (m["last_check"] or 0) >= m["interval"]: check_monitor(m)
        except Exception: pass
        time.sleep(30)
threading.Thread(target=monitor_loop, daemon=True).start()

@app.get("/api/monitors")
def monitors(u=Depends(user)):
    with db() as c:
        out = []
        for m in c.execute("SELECT * FROM monitors WHERE uid=? ORDER BY created", (u["id"],)):
            d = dict(m); d["history"] = [dict(r) for r in c.execute("SELECT status,ms,ts FROM monitor_log WHERE mid=? ORDER BY ts DESC LIMIT 60", (m["id"],))][::-1]
            tot = d["up_count"] + d["down_count"]; d["uptime"] = round(d["up_count"]/tot*100, 2) if tot else None; out.append(d)
    return out
@app.post("/api/monitors")
def add_monitor(b: UrlIn, interval: int = 300, u=Depends(user)):
    url = b.url if b.url.startswith("http") else "https://" + b.url
    with db() as c:
        if c.execute("SELECT COUNT(*) FROM monitors WHERE uid=?", (u["id"],)).fetchone()[0] >= 20: raise HTTPException(429, "Max 20 monitors")
        mid = c.execute("INSERT INTO monitors(uid,url,interval,created) VALUES(?,?,?,?)", (u["id"], url, max(60, interval), time.time())).lastrowid
    threading.Thread(target=check_monitor, args=({"id": mid, "url": url},), daemon=True).start(); return {"id": mid}
@app.delete("/api/monitors/{mid}")
def del_monitor(mid: int, u=Depends(user)):
    with db() as c: c.execute("DELETE FROM monitors WHERE id=? AND uid=?", (mid, u["id"])); c.execute("DELETE FROM monitor_log WHERE mid=?", (mid,))
    return {"ok": True}

# ═══════════════════════════════ DOMAINS ═══════════════════════════════
class DomainIn(BaseModel): domain: str
@app.post("/api/projects/{name}/domains")
def add_domain(name: str, d: DomainIn, u=Depends(user)):
    own(name, u); dom = d.domain.lower().strip().replace("https://", "").replace("http://", "").strip("/")
    if not re.match(r"^[a-z0-9.-]+\.[a-z]{2,}$", dom): raise HTTPException(400, "Invalid domain")
    tok = "forgevia-verify=" + secrets.token_hex(8)
    with db() as c: c.execute("INSERT OR REPLACE INTO domains VALUES(?,?,?,?,?)", (dom, name, 0, tok, time.time()))
    return {"domain": dom, "token": tok, "instructions": [{"type": "CNAME", "host": dom.split(".")[0] if dom.count(".") > 1 else "www", "value": "sites.forgevia.com"}, {"type": "A", "host": "@", "value": "76.76.21.21"}, {"type": "TXT", "host": "_forgevia", "value": tok}]}
@app.post("/api/domains/{dom}/verify")
def verify_domain(dom: str, u=Depends(user)):
    with db() as c: r = c.execute("SELECT * FROM domains WHERE domain=?", (dom,)).fetchone()
    if not r: raise HTTPException(404)
    ok = False
    try:
        j = httpx.get("https://dns.google/resolve", params={"name": f"_forgevia.{dom}", "type": "TXT"}, timeout=8).json()
        ok = any(r["token"] in a.get("data", "") for a in j.get("Answer", []))
    except Exception: pass
    with db() as c: c.execute("UPDATE domains SET verified=? WHERE domain=?", (int(ok), dom))
    return {"verified": ok}
@app.delete("/api/domains/{dom}")
def del_domain(dom: str, u=Depends(user)):
    with db() as c: c.execute("DELETE FROM domains WHERE domain=?", (dom,))
    return {"ok": True}

@app.get("/api/domains/check")
def domain_check(name: str, u=Depends(user)):
    """Check domain availability via DNS (heuristic) across TLDs."""
    base = re.sub(r"[^a-z0-9-]", "", name.lower().split(".")[0]); out = []
    for tld in ("com", "io", "dev", "app", "net", "org", "co", "ai", "xyz", "site"):
        d = f"{base}.{tld}"
        try:
            j = httpx.get("https://dns.google/resolve", params={"name": d, "type": "NS"}, timeout=6).json()
            taken = j.get("Status") == 0 and bool(j.get("Answer"))
        except Exception: taken = None
        out.append({"domain": d, "available": None if taken is None else not taken, "buy": f"https://www.namecheap.com/domains/registration/results/?domain={d}"})
    return out

# ═══════════════════════════════ AI ASSISTANT (rule-based, offline) ═══════════════════════════════
class AiIn(BaseModel): prompt: str; context: str = ""; file: str = ""
@app.post("/api/ai")
def ai(a: AiIn, u=Depends(user)):
    from assistant import respond
    return respond(a.prompt, a.context, a.file)

# ═══════════════════════════════ SNIPPETS / PASTE ═══════════════════════════════
class SnipIn(BaseModel): title: str; lang: str = "text"; code: str; public: bool = True
@app.post("/api/snippets")
def snip_create(s: SnipIn, u=Depends(user)):
    slug = secrets.token_urlsafe(6)
    with db() as c: c.execute("INSERT INTO snippets(uid,title,lang,code,public,slug,created) VALUES(?,?,?,?,?,?,?)", (u["id"], s.title, s.lang, s.code, int(s.public), slug, time.time()))
    return {"slug": slug, "url": f"/s/{slug}"}
@app.get("/api/snippets")
def snip_list(u=Depends(user)):
    with db() as c: return [dict(r) for r in c.execute("SELECT id,title,lang,slug,created,length(code) size FROM snippets WHERE uid=? ORDER BY created DESC", (u["id"],))]
@app.get("/s/{slug}", response_class=HTMLResponse)
def snip_view(slug: str):
    with db() as c: r = c.execute("SELECT * FROM snippets WHERE slug=?", (slug,)).fetchone()
    if not r: raise HTTPException(404)
    import html as H
    return f"""<!doctype html><html><head><meta charset=utf-8><title>{H.escape(r['title'])} — Forgevia</title><style>body{{font-family:system-ui;background:#0b0d12;color:#e6e8ef;margin:0;padding:40px}}pre{{background:#12151d;padding:24px;border-radius:12px;overflow:auto;border:1px solid #232837;font-size:13px;line-height:1.6}}h1{{font-size:20px}}a{{color:#22d3ee}}</style></head><body><h1>{H.escape(r['title'])} <small style="color:#8b91a5">· {r['lang']}</small></h1><pre>{H.escape(r['code'])}</pre><p><small>Shared via <a href="/">Forgevia</a></small></p></body></html>"""

# ═══════════════════════════════ UTILITIES ═══════════════════════════════
@app.get("/api/tools/headers")
def tool_headers(url: str, u=Depends(user)):
    url, r, el = fetch(url); h = dict(r.headers)
    sec = {k: (k.lower() in {x.lower() for x in h}) for k in ("Strict-Transport-Security", "Content-Security-Policy", "X-Frame-Options", "X-Content-Type-Options", "Referrer-Policy", "Permissions-Policy")}
    return {"url": url, "status": r.status_code, "ms": int(el*1000), "headers": h, "security": sec, "security_score": sum(sec.values()) * 100 // len(sec), "server": h.get("server", "unknown")}

@app.get("/api/tools/dns")
def tool_dns(domain: str, u=Depends(user)):
    out = {}
    for t in ("A", "AAAA", "CNAME", "MX", "TXT", "NS"):
        try: out[t] = [a["data"] for a in httpx.get("https://dns.google/resolve", params={"name": domain, "type": t}, timeout=6).json().get("Answer", [])]
        except Exception: out[t] = []
    return out

@app.get("/api/tools/whois")
def tool_whois(domain: str, u=Depends(user)):
    try:
        r = httpx.get(f"https://rdap.org/domain/{domain}", timeout=10, follow_redirects=True)
        if r.status_code == 404: return {"registered": False}
        if r.status_code != 200:
            # RDAP unavailable — fall back to DNS so we never falsely say "available"
            try: socket.gethostbyname(domain); return {"registered": True, "note": "RDAP unavailable; domain resolves in DNS"}
            except Exception: return {"registered": False, "note": "RDAP unavailable; no DNS record"}
        j = r.json(); ev = {e["eventAction"]: e["eventDate"] for e in j.get("events", [])}
        return {"registered": True, "registrar": next((e.get("vcardArray", [None, [[]]])[1][1][3] if len(e.get("vcardArray", [None, [[]]])[1]) > 1 else e.get("handle") for e in j.get("entities", []) if "registrar" in e.get("roles", [])), None), "created": ev.get("registration"), "expires": ev.get("expiration"), "nameservers": [n["ldhName"] for n in j.get("nameservers", [])], "status": j.get("status", [])}
    except Exception as e: return {"error": str(e)}

@app.get("/api/tools/speed")
def tool_speed(url: str, u=Depends(user)):
    url, r, el = fetch(url); soup = BeautifulSoup(r.text, "lxml"); host = urlparse(url).netloc
    assets = []
    for tag, attr in (("script", "src"), ("link", "href"), ("img", "src")):
        for e in soup.find_all(tag, **{attr: True}):
            if tag == "link" and "stylesheet" not in (e.get("rel") or []): continue
            assets.append({"type": tag, "url": urljoin(url, e[attr])})
    sizes = []; tot = len(r.content)
    for a in assets[:25]:
        try:
            t = time.time(); rr = httpx.get(a["url"], timeout=10, headers=UA); a["size"] = len(rr.content); a["ms"] = int((time.time()-t)*1000); tot += a["size"]
        except Exception: a["size"] = 0; a["ms"] = 0
        sizes.append(a)
    score = 100
    if el > 0.8: score -= 15
    if el > 2: score -= 20
    if tot > 1_000_000: score -= 15
    if tot > 3_000_000: score -= 20
    if len(assets) > 30: score -= 10
    if len([a for a in assets if a["type"] == "script"]) > 10: score -= 10
    return {"url": url, "ttfb_ms": int(el*1000), "html_kb": len(r.content)//1024, "total_kb": tot//1024, "requests": len(assets), "assets": sorted(sizes, key=lambda x: -x.get("size", 0)), "score": max(score, 0),
            "tips": [t for c, t in ((el > 0.8, "Slow server response — add caching or a CDN."), (tot > 1_000_000, "Total page weight over 1 MB — compress images (WebP/AVIF)."), (len(assets) > 30, "Too many requests — bundle CSS/JS."), (any(a["type"] == "img" and a.get("size", 0) > 300_000 for a in sizes), "Some images are over 300 KB — resize and compress."), (not any("defer" in str(s) or "async" in str(s) for s in soup.find_all("script", src=True)), "Scripts block rendering — add defer.")) if c]}

# ═══════════════════════════════ ADMIN STATS / PUBLIC ═══════════════════════════════
@app.get("/api/stats")
def public_stats():
    with db() as c:
        return {"users": c.execute("SELECT COUNT(*) FROM users").fetchone()[0], "projects": c.execute("SELECT COUNT(*) FROM projects").fetchone()[0], "published": c.execute("SELECT COUNT(*) FROM projects WHERE published IS NOT NULL").fetchone()[0], "hits": c.execute("SELECT COUNT(*) FROM hits").fetchone()[0], "running_apps": len(RUNNING)}

@app.get("/api/leaderboard")
def leaderboard(period: str = "all", limit: int = 50):
    since = {"day": 86400, "week": 7*86400, "month": 30*86400}.get(period, 10**10)
    with db() as c:
        rows = c.execute("""SELECT p.name, p.template, p.kind, p.published, p.seo_title, p.seo_desc, u.name AS owner, u.plan,
            (SELECT COUNT(*) FROM hits h WHERE h.project=p.name AND h.ts>?) hits,
            (SELECT COUNT(DISTINCT ip) FROM hits h WHERE h.project=p.name AND h.ts>?) uniq,
            (SELECT COUNT(*) FROM forms f WHERE f.project=p.name) forms,
            (SELECT COUNT(*) FROM versions v WHERE v.project=p.name) deploys
            FROM projects p JOIN users u ON u.id=p.uid WHERE p.published IS NOT NULL AND p.password IS NULL
            ORDER BY hits DESC, uniq DESC LIMIT ?""", (time.time()-since, time.time()-since, limit)).fetchall()
        builders = c.execute("""SELECT u.name, u.plan, u.created, COUNT(p.id) projects,
            (SELECT COUNT(*) FROM hits h WHERE h.project IN (SELECT name FROM projects WHERE uid=u.id) AND h.ts>?) hits
            FROM users u LEFT JOIN projects p ON p.uid=u.id GROUP BY u.id HAVING projects>0 ORDER BY hits DESC LIMIT 20""", (time.time()-since,)).fetchall()
        totals = {"users": c.execute("SELECT COUNT(*) FROM users").fetchone()[0], "sites": c.execute("SELECT COUNT(*) FROM projects WHERE published IS NOT NULL").fetchone()[0], "views": c.execute("SELECT COUNT(*) FROM hits").fetchone()[0], "forms": c.execute("SELECT COUNT(*) FROM forms").fetchone()[0]}
    out = []
    for i, r in enumerate(rows, 1):
        d = dict(r); d["rank"] = i; d["score"] = d["hits"] + d["uniq"] * 2 + d["forms"] * 10 + d["deploys"] * 5; out.append(d)
    return {"period": period, "sites": out, "builders": [dict(b) for b in builders], "totals": totals}

@app.get("/leaderboard", response_class=HTMLResponse)
def leaderboard_page(): return _page("leaderboard.html")

@app.get("/api/explore")
def explore():
    with db() as c: rows = c.execute("SELECT p.name, p.template, p.published, p.seo_title, p.seo_desc, (SELECT COUNT(*) FROM hits h WHERE h.project=p.name) hits FROM projects p WHERE published IS NOT NULL AND password IS NULL ORDER BY hits DESC LIMIT 30").fetchall()
    return [dict(r) for r in rows]

def _asset_v():
    h = hashlib.md5()
    for f in ("app.js", "app.css", "app.html"):
        try: h.update((ROOT / "static" / f).read_bytes())
        except Exception: pass
    return h.hexdigest()[:10]
ASSET_V = _asset_v()
def _page(name):
    v = _asset_v()
    html = (ROOT / "static" / name).read_text(encoding="utf-8").replace("/static/app.css", f"/static/a/{v}/app.css").replace("/static/app.js", f"/static/a/{v}/app.js")
    return HTMLResponse(html, headers={"Cache-Control": "no-store, no-cache, must-revalidate, max-age=0", "Pragma": "no-cache", "Expires": "0"})

@app.middleware("http")
async def no_cache_static(request, call_next):
    resp = await call_next(request)
    if request.url.path.startswith("/static/"): resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"; resp.headers["Pragma"] = "no-cache"; resp.headers["Expires"] = "0"
    return resp

@app.get("/", response_class=HTMLResponse)
def landing(): return _page("landing.html")
@app.get("/static/a/{v}/{fname}")
def versioned_asset(v: str, fname: str):
    p = ROOT / "static" / os.path.basename(fname)
    if not p.exists(): raise HTTPException(404)
    return Response(p.read_bytes(), media_type=mimetypes.guess_type(fname)[0] or "application/octet-stream", headers={"Cache-Control": "no-store, no-cache, must-revalidate, max-age=0", "Pragma": "no-cache", "Expires": "0"})

@app.get("/robots.txt", response_class=PlainTextResponse)
def robots(req: Request):
    return f"User-agent: *\nAllow: /\nDisallow: /app\nDisallow: /api/\nSitemap: {str(req.base_url).rstrip('/')}/sitemap.xml\n"

@app.get("/sitemap.xml")
def sitemap(req: Request):
    base = str(req.base_url).rstrip("/")
    urls = [f"{base}/", f"{base}/login", f"{base}/leaderboard", f"{base}/api/docs"]
    try:
        with db() as c:
            urls += [f"{base}/sites/{r[0]}/" for r in c.execute("SELECT name FROM projects WHERE published=1").fetchall()]
    except Exception: pass
    body = '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + "".join(f"<url><loc>{u}</loc></url>" for u in urls) + "</urlset>"
    return Response(body, media_type="application/xml")

@app.get("/login", response_class=HTMLResponse)
def login_page(): return HTMLResponse((ROOT/"static"/"login.html").read_text(encoding="utf-8"), headers={"Cache-Control":"no-store"})
@app.get("/app", response_class=HTMLResponse)
def dashboard(req: Request, t: str = ""):
    resp = _page("app.html")
    tok = t or _tok_from(req)
    if tok:
        with db() as c: ok = c.execute("SELECT 1 FROM sessions WHERE token=?", (tok,)).fetchone()
        if ok:
            body = resp.body.decode()
            # Inline bootstrap: patch window.fetch so EVERY /api call carries this token, regardless of which app.js version the browser has cached.
            boot = ("<script>(function(){var T=" + json.dumps(tok) + ";window.__FV_URL_TOKEN=T;"
                    "var f=window.fetch;window.fetch=function(u,o){o=o||{};var url=(typeof u==='string')?u:(u&&u.url)||'';"
                    "if(url.indexOf('/api/')===0||url.indexOf(location.origin+'/api/')===0){var h=new Headers(o.headers||{});if(!h.has('Authorization'))h.set('Authorization','Bearer '+T);h.set('X-FV-Token',T);o.headers=h;"
                    "if(url.indexOf('_fvt=')<0){url+=(url.indexOf('?')>-1?'&':'?')+'_fvt='+encodeURIComponent(T);u=(typeof u==='string')?url:new Request(url,u);}}"
                    "return f.call(this,u,o)};"
                    "try{localStorage.setItem('fv_token',T)}catch(e){}try{sessionStorage.setItem('fv_token',T)}catch(e){}})();</script>")
            body = body.replace("<head>", "<head>" + boot + "<meta name=\"fv-token\" content=\"" + tok + "\">", 1)
            # never let this page or its scripts be cached
            resp = HTMLResponse(body, headers={"Cache-Control": "no-store, no-cache, must-revalidate, max-age=0", "Pragma": "no-cache", "Expires": "0"})
            if t: set_session_cookie(resp, req, tok)
    return resp
@app.get("/health")
def health(): return {"ok": True, "ts": time.time()}

import integrations
integrations.bind(db, user, log)
integrations.install(app, user)

app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")
