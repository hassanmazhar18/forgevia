"""Free-tier persistence: keeps data/ safe across restarts by syncing it to a private GitHub repo.
Enable with env vars: FV_BACKUP_REPO="username/forgevia-data"  FV_BACKUP_TOKEN="ghp_..." (repo scope).
Restores on boot (if the local data dir is empty) and pushes a snapshot every FV_BACKUP_MINUTES (default 10)."""
import os, io, time, threading, tarfile, base64, json, hashlib
import httpx

REPO = os.environ.get("FV_BACKUP_REPO"); TOKEN = os.environ.get("FV_BACKUP_TOKEN")
EVERY = int(os.environ.get("FV_BACKUP_MINUTES", "10")) * 60
API = "https://api.github.com"
_last = {"hash": None}

def _hdr(): return {"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github+json"}
def enabled(): return bool(REPO and TOKEN)

def _snapshot(data):
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as t:
        for name in ("forgevia.db", "projects", "sites", "versions", "uploads"):
            p = data / name
            if p.exists(): t.add(p, arcname=name)
    return buf.getvalue()

def backup(data):
    if not enabled(): return False
    blob = _snapshot(data); h = hashlib.md5(blob).hexdigest()
    if h == _last["hash"]: return True
    if len(blob) > 95 * 1024 * 1024: print("persist: snapshot >95MB, skipping"); return False
    path = "backup.tar.gz"
    with httpx.Client(timeout=120) as c:
        r = c.get(f"{API}/repos/{REPO}/contents/{path}", headers=_hdr()); sha = r.json().get("sha") if r.status_code == 200 else None
        body = {"message": f"forgevia backup {time.strftime('%Y-%m-%d %H:%M:%S')}", "content": base64.b64encode(blob).decode()}
        if sha: body["sha"] = sha
        r = c.put(f"{API}/repos/{REPO}/contents/{path}", headers=_hdr(), json=body)
        ok = r.status_code in (200, 201)
        print("persist: backup", "ok" if ok else f"failed {r.status_code} {r.text[:120]}")
        if ok: _last["hash"] = h
        return ok

def restore(data):
    if not enabled(): return False
    if (data / "forgevia.db").exists() and (data / "forgevia.db").stat().st_size > 0:
        print("persist: local data present, skipping restore"); return False
    with httpx.Client(timeout=120, follow_redirects=True) as c:
        r = c.get(f"{API}/repos/{REPO}/contents/backup.tar.gz", headers={**_hdr(), "Accept": "application/vnd.github.raw"})
        if r.status_code != 200: print("persist: no backup to restore", r.status_code); return False
        with tarfile.open(fileobj=io.BytesIO(r.content), mode="r:gz") as t: t.extractall(data)
    print("persist: restored from backup"); return True

def start_backup_loop(data):
    if not enabled(): print("persist: not configured (set FV_BACKUP_REPO + FV_BACKUP_TOKEN)"); return
    def loop():
        while True:
            time.sleep(EVERY)
            try: backup(data)
            except Exception as e: print("persist error:", e)
    threading.Thread(target=loop, daemon=True).start()
    print(f"persist: enabled → {REPO} every {EVERY//60} min")
