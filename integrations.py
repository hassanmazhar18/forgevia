"""Forgevia — OAuth sign-in (GitHub, Google) + GitHub repo export/import.

Configure via environment variables (or data/oauth.json):
  GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET   → https://github.com/settings/developers  (callback: <origin>/api/auth/github/callback)
  GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET   → https://console.cloud.google.com/apis/credentials (callback: <origin>/api/auth/google/callback)
Without OAuth credentials, users can still connect GitHub with a Personal Access Token (repo scope).
"""
import os, json, time, base64, secrets, hashlib
from pathlib import Path
import httpx
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import RedirectResponse, HTMLResponse
from pydantic import BaseModel
from typing import Optional

router = APIRouter()
DATA = Path(__file__).parent / "data"
CFG_FILE = DATA / "oauth.json"

def cfg(k):
    v = os.environ.get(k)
    if v: return v
    if CFG_FILE.exists():
        try: return json.loads(CFG_FILE.read_text()).get(k)
        except Exception: pass
    return None

_db = None; _user = None; _log = None
def bind(db, user, log):
    global _db, _user, _log; _db, _user, _log = db, user, log
    with _db() as c:
        c.execute("CREATE TABLE IF NOT EXISTS oauth(uid INTEGER, provider TEXT, pid TEXT, login TEXT, token TEXT, avatar TEXT, created REAL, PRIMARY KEY(uid,provider))")
        c.execute("CREATE TABLE IF NOT EXISTS oauth_state(state TEXT PRIMARY KEY, provider TEXT, uid INTEGER, next TEXT, created REAL)")

def origin(req: Request):
    proto = req.headers.get("x-forwarded-proto", req.url.scheme); host = req.headers.get("x-forwarded-host", req.headers.get("host"))
    return f"{proto}://{host}"

def _session_for(uid):
    tok = secrets.token_urlsafe(32)
    with _db() as c: c.execute("INSERT INTO sessions VALUES(?,?,?)", (tok, uid, time.time()))
    return tok

def _link_or_create(provider, pid, login, email, name, token, avatar, uid=None):
    with _db() as c:
        row = c.execute("SELECT uid FROM oauth WHERE provider=? AND pid=?", (provider, pid)).fetchone()
        if row: uid = row["uid"]
        elif uid is None:
            u = c.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone() if email else None
            if u: uid = u["id"]
            else:
                email = email or f"{login}@{provider}.forgevia"
                uid = c.execute("INSERT INTO users(email,name,pw,created) VALUES(?,?,?,?)", (email, name or login, "oauth:" + secrets.token_hex(16), time.time())).lastrowid
        c.execute("INSERT OR REPLACE INTO oauth VALUES(?,?,?,?,?,?,?)", (uid, provider, str(pid), login, token, avatar, time.time()))
    return uid

# ───────────── provider config ─────────────
@router.get("/api/auth/providers")
def providers():
    return {"github": bool(cfg("GITHUB_CLIENT_ID")), "google": bool(cfg("GOOGLE_CLIENT_ID"))}

def _start(req, provider, uid=None, next_="/app"):
    state = secrets.token_urlsafe(24)
    with _db() as c:
        c.execute("DELETE FROM oauth_state WHERE created<?", (time.time() - 900,))
        c.execute("INSERT INTO oauth_state VALUES(?,?,?,?,?)", (state, provider, uid, next_, time.time()))
    cb = f"{origin(req)}/api/auth/{provider}/callback"
    if provider == "github":
        cid = cfg("GITHUB_CLIENT_ID")
        if not cid: raise HTTPException(400, "GitHub OAuth not configured. Set GITHUB_CLIENT_ID / GITHUB_CLIENT_SECRET, or connect with a token.")
        return RedirectResponse(f"https://github.com/login/oauth/authorize?client_id={cid}&redirect_uri={cb}&scope=read:user,user:email,repo&state={state}")
    if provider == "google":
        cid = cfg("GOOGLE_CLIENT_ID")
        if not cid: raise HTTPException(400, "Google OAuth not configured. Set GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET.")
        return RedirectResponse(f"https://accounts.google.com/o/oauth2/v2/auth?client_id={cid}&redirect_uri={cb}&response_type=code&scope=openid%20email%20profile&state={state}&prompt=select_account")
    raise HTTPException(404)

@router.get("/api/auth/{provider}/start")
def oauth_start(provider: str, req: Request, next: str = "/app"):
    # if already signed in, link to existing account
    uid = None
    tok = req.cookies.get("fv")
    if tok:
        with _db() as c:
            r = c.execute("SELECT uid FROM sessions WHERE token=?", (tok,)).fetchone(); uid = r["uid"] if r else None
    return _start(req, provider, uid, next)

@router.get("/api/auth/{provider}/callback")
def oauth_callback(provider: str, req: Request, code: str = "", state: str = "", error: str = ""):
    if error: return HTMLResponse(_popup(f"Sign-in cancelled: {error}", ok=False))
    with _db() as c: st = c.execute("SELECT * FROM oauth_state WHERE state=?", (state,)).fetchone()
    if not st: return HTMLResponse(_popup("Invalid or expired state. Try again.", ok=False))
    with _db() as c: c.execute("DELETE FROM oauth_state WHERE state=?", (state,))
    cb = f"{origin(req)}/api/auth/{provider}/callback"
    try:
        if provider == "github":
            r = httpx.post("https://github.com/login/oauth/access_token", data={"client_id": cfg("GITHUB_CLIENT_ID"), "client_secret": cfg("GITHUB_CLIENT_SECRET"), "code": code, "redirect_uri": cb}, headers={"Accept": "application/json"}, timeout=15).json()
            token = r.get("access_token")
            if not token: raise Exception(r.get("error_description") or "no token")
            h = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
            u = httpx.get("https://api.github.com/user", headers=h, timeout=15).json()
            email = u.get("email")
            if not email:
                for e in httpx.get("https://api.github.com/user/emails", headers=h, timeout=15).json():
                    if e.get("primary") and e.get("verified"): email = e["email"]; break
            uid = _link_or_create("github", u["id"], u["login"], email, u.get("name"), token, u.get("avatar_url"), st["uid"])
        else:
            r = httpx.post("https://oauth2.googleapis.com/token", data={"client_id": cfg("GOOGLE_CLIENT_ID"), "client_secret": cfg("GOOGLE_CLIENT_SECRET"), "code": code, "redirect_uri": cb, "grant_type": "authorization_code"}, timeout=15).json()
            token = r.get("access_token")
            if not token: raise Exception(r.get("error_description") or "no token")
            u = httpx.get("https://www.googleapis.com/oauth2/v2/userinfo", headers={"Authorization": f"Bearer {token}"}, timeout=15).json()
            uid = _link_or_create("google", u["id"], u.get("email", "").split("@")[0], u.get("email"), u.get("name"), token, u.get("picture"), st["uid"])
    except Exception as e:
        return HTMLResponse(_popup(f"{provider} sign-in failed: {e}", ok=False))
    sess = _session_for(uid); _log(uid, None, f"signed in with {provider}")
    resp = HTMLResponse(_popup("Signed in! You can close this window.", ok=True, next_=st["next"], token=sess))
    from server import set_session_cookie; set_session_cookie(resp, req, sess)
    return resp

def _popup(msg, ok=True, next_="/app", token=""):
    return f"""<!doctype html><meta charset=utf-8><body style="font-family:system-ui;background:#07080c;color:#eee;display:grid;place-items:center;height:100vh;margin:0"><div style="text-align:center"><h2>{'✓' if ok else '✕'} {msg}</h2></div>
<script>try{{window.opener&&window.opener.postMessage({{forgevia:'oauth',ok:{str(ok).lower()},token:'{token}'}},'*')}}catch(e){{}}setTimeout(()=>{{if(window.opener)window.close();else location.href='{next_}'}},{800 if ok else 4000})</script>"""

# ───────────── GitHub connection (token or oauth) ─────────────
class TokenIn(BaseModel): token: str

def gh_token(u):
    with _db() as c: r = c.execute("SELECT token FROM oauth WHERE uid=? AND provider='github'", (u["id"],)).fetchone()
    if not r or not r["token"]: raise HTTPException(400, "GitHub not connected. Connect it in Account → Connections.")
    return r["token"]

def GH(token): return {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}

def install(app, user_dep):
    """Register endpoints that need the auth dependency from server.py."""
    @router.post("/api/github/connect")
    def gh_connect(t: TokenIn, u=Depends(user_dep)):
        r = httpx.get("https://api.github.com/user", headers=GH(t.token.strip()), timeout=15)
        if r.status_code != 200: raise HTTPException(400, "Invalid token (needs 'repo' scope)")
        gu = r.json()
        with _db() as c: c.execute("INSERT OR REPLACE INTO oauth VALUES(?,?,?,?,?,?,?)", (u["id"], "github", str(gu["id"]), gu["login"], t.token.strip(), gu.get("avatar_url"), time.time()))
        _log(u["id"], None, "connected GitHub", gu["login"]); return {"login": gu["login"], "avatar": gu.get("avatar_url")}

    @router.get("/api/connections")
    def connections(u=Depends(user_dep)):
        with _db() as c: rows = c.execute("SELECT provider,login,avatar,created FROM oauth WHERE uid=?", (u["id"],)).fetchall()
        return {r["provider"]: dict(r) for r in rows}

    @router.delete("/api/connections/{provider}")
    def disconnect(provider: str, u=Depends(user_dep)):
        with _db() as c: c.execute("DELETE FROM oauth WHERE uid=? AND provider=?", (u["id"], provider))
        return {"ok": True}

    @router.get("/api/github/repos")
    def gh_repos(u=Depends(user_dep)):
        tok = gh_token(u)
        r = httpx.get("https://api.github.com/user/repos", params={"per_page": 100, "sort": "updated", "affiliation": "owner,collaborator"}, headers=GH(tok), timeout=20)
        if r.status_code != 200: raise HTTPException(400, f"GitHub error {r.status_code}")
        return [{"full_name": x["full_name"], "private": x["private"], "default_branch": x["default_branch"], "updated": x["updated_at"], "url": x["html_url"]} for x in r.json()]

    class PushIn(BaseModel):
        repo: str = ""            # "owner/name"; empty → create new repo named after project
        private: bool = False
        message: str = "Deploy from Forgevia"
        branch: Optional[str] = None
        create_pages: bool = False

    @router.post("/api/projects/{name}/github/push")
    def gh_push(name: str, p: PushIn, req: Request, u=Depends(user_dep)):
        from server import own, safe
        own(name, u); tok = gh_token(u); h = GH(tok); d = safe(name)
        me_login = httpx.get("https://api.github.com/user", headers=h, timeout=15).json()["login"]
        repo = p.repo.strip() or f"{me_login}/{name}"
        # ensure repo exists
        r = httpx.get(f"https://api.github.com/repos/{repo}", headers=h, timeout=15)
        if r.status_code == 404:
            cr = httpx.post("https://api.github.com/user/repos", headers=h, json={"name": repo.split("/")[-1], "private": p.private, "auto_init": True, "description": f"Built with Forgevia"}, timeout=20)
            if cr.status_code not in (201, 200): raise HTTPException(400, f"Could not create repo: {cr.json().get('message')}")
            time.sleep(1.5); r = httpx.get(f"https://api.github.com/repos/{repo}", headers=h, timeout=15)
        if r.status_code != 200: raise HTTPException(400, f"Repo error: {r.json().get('message')}")
        branch = p.branch or r.json()["default_branch"]
        # build tree via Git Data API (single commit with all files)
        files = [f for f in d.rglob("*") if f.is_file() and not any(x in f.parts for x in ("node_modules", "__pycache__", ".git")) and f.name != ".forgevia.log"]
        if not files: raise HTTPException(400, "Project is empty")
        blobs = []
        for f in files:
            data = f.read_bytes()
            try: content, enc = data.decode("utf-8"), "utf-8"
            except UnicodeDecodeError: content, enc = base64.b64encode(data).decode(), "base64"
            b = httpx.post(f"https://api.github.com/repos/{repo}/git/blobs", headers=h, json={"content": content, "encoding": enc}, timeout=30).json()
            blobs.append({"path": str(f.relative_to(d)).replace(os.sep, "/"), "mode": "100644", "type": "blob", "sha": b["sha"]})
        ref = httpx.get(f"https://api.github.com/repos/{repo}/git/ref/heads/{branch}", headers=h, timeout=15)
        parent = ref.json()["object"]["sha"] if ref.status_code == 200 else None
        tree = httpx.post(f"https://api.github.com/repos/{repo}/git/trees", headers=h, json={"tree": blobs}, timeout=30).json()
        commit_body = {"message": p.message, "tree": tree["sha"]}
        if parent: commit_body["parents"] = [parent]
        commit = httpx.post(f"https://api.github.com/repos/{repo}/git/commits", headers=h, json=commit_body, timeout=30).json()
        if parent: httpx.patch(f"https://api.github.com/repos/{repo}/git/refs/heads/{branch}", headers=h, json={"sha": commit["sha"], "force": True}, timeout=15)
        else: httpx.post(f"https://api.github.com/repos/{repo}/git/refs", headers=h, json={"ref": f"refs/heads/{branch}", "sha": commit["sha"]}, timeout=15)
        pages_url = None
        if p.create_pages:
            pr = httpx.post(f"https://api.github.com/repos/{repo}/pages", headers=h, json={"source": {"branch": branch, "path": "/"}}, timeout=20)
            if pr.status_code in (201, 409): pages_url = f"https://{repo.split('/')[0]}.github.io/{repo.split('/')[1]}/"
        with _db() as c: c.execute("INSERT OR REPLACE INTO kv VALUES(?,?,?)", (f"__meta__{name}", "github_repo", json.dumps({"repo": repo, "branch": branch, "pushed": time.time()})))
        _log(u["id"], name, "pushed to GitHub", f"{repo}@{branch} ({len(files)} files)")
        return {"repo": repo, "branch": branch, "files": len(files), "commit": commit["sha"][:7], "url": f"https://github.com/{repo}", "pages_url": pages_url}

    class ImportIn(BaseModel): repo: str; name: Optional[str] = None; branch: Optional[str] = None

    @router.post("/api/github/import")
    def gh_import(p: ImportIn, u=Depends(user_dep)):
        import re, zipfile, io
        from server import safe, PROJECTS
        tok = gh_token(u); h = GH(tok)
        repo = p.repo.strip().replace("https://github.com/", "").strip("/")
        name = re.sub(r"[^a-z0-9-]", "-", (p.name or repo.split("/")[-1]).lower())[:40]
        d = safe(name)
        if d.exists(): raise HTTPException(409, "Project name taken")
        info = httpx.get(f"https://api.github.com/repos/{repo}", headers=h, timeout=15)
        if info.status_code != 200: raise HTTPException(404, "Repo not found or no access")
        branch = p.branch or info.json()["default_branch"]
        z = httpx.get(f"https://api.github.com/repos/{repo}/zipball/{branch}", headers=h, follow_redirects=True, timeout=120)
        if z.status_code != 200: raise HTTPException(400, "Download failed")
        d.mkdir(); zf = zipfile.ZipFile(io.BytesIO(z.content)); n = 0
        for m in zf.namelist():
            parts = m.split("/", 1)
            if len(parts) < 2 or not parts[1] or m.endswith("/") or "node_modules/" in m or parts[1].startswith(".git/"): continue
            t = d / parts[1]; t.parent.mkdir(parents=True, exist_ok=True); t.write_bytes(zf.read(m)); n += 1
        kind = "python" if (d / "main.py").exists() or (d / "app.py").exists() else "node" if (d / "package.json").exists() and not (d / "index.html").exists() else "static"
        with _db() as c:
            c.execute("INSERT INTO projects(uid,name,kind,created,template) VALUES(?,?,?,?,?)", (u["id"], name, kind, time.time(), "github"))
            c.execute("INSERT OR REPLACE INTO kv VALUES(?,?,?)", (f"__meta__{name}", "github_repo", json.dumps({"repo": repo, "branch": branch, "pushed": None})))
        _log(u["id"], name, "imported from GitHub", f"{repo}@{branch} ({n} files)")
        return {"name": name, "files": n, "kind": kind}

    @router.get("/api/projects/{name}/github")
    def gh_link(name: str, u=Depends(user_dep)):
        with _db() as c: r = c.execute("SELECT v FROM kv WHERE project=? AND k='github_repo'", (f"__meta__{name}",)).fetchone()
        return json.loads(r["v"]) if r else {}

    app.include_router(router)


# ─── Admin setup page: paste OAuth keys without touching files ───
from fastapi.responses import HTMLResponse
from pydantic import BaseModel as _BM

def _is_admin(u):
    with _db() as c:
        first = c.execute("SELECT id FROM users ORDER BY id LIMIT 1").fetchone()
    return u and first and u["id"] == first["id"]

class _Keys(_BM):
    GITHUB_CLIENT_ID: str = ""; GITHUB_CLIENT_SECRET: str = ""; GOOGLE_CLIENT_ID: str = ""; GOOGLE_CLIENT_SECRET: str = ""

@router.get("/api/admin/oauth")
def admin_get(req: Request):
    u = _user(req)
    if not _is_admin(u): raise HTTPException(403, "Only the site owner (first account) can open setup")
    cur = {}
    if CFG_FILE.exists():
        try: cur = json.loads(CFG_FILE.read_text())
        except Exception: pass
    mask = lambda v: (v[:4] + "…" + v[-4:]) if v and len(v) > 10 else ("set" if v else "")
    return {"callback_github": f"{origin(req)}/api/auth/github/callback", "callback_google": f"{origin(req)}/api/auth/google/callback",
            "origin": origin(req), **{k: mask(cur.get(k) or os.environ.get(k) or "") for k in _Keys.model_fields}}

@router.post("/api/admin/oauth")
def admin_set(k: _Keys, req: Request):
    u = _user(req)
    if not _is_admin(u): raise HTTPException(403, "Only the site owner can change this")
    cur = {}
    if CFG_FILE.exists():
        try: cur = json.loads(CFG_FILE.read_text())
        except Exception: pass
    for name, val in k.model_dump().items():
        val = val.strip()
        if val: cur[name] = val
    DATA.mkdir(exist_ok=True); CFG_FILE.write_text(json.dumps(cur, indent=2))
    return {"ok": True, "providers": providers()}

@router.get("/setup", response_class=HTMLResponse)
def setup_page():
    return HTMLResponse((Path(__file__).parent / "static" / "setup.html").read_text(), headers={"Cache-Control": "no-store"})
