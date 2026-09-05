"""Forgevia one-click launcher for Windows.
Installs requirements, starts the server, opens a free public HTTPS tunnel and shows the URL."""
import os, sys, subprocess, time, re, threading, urllib.request, webbrowser, zipfile, io, json, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
PORT = int(os.environ.get("PORT", "8000"))
TUN = ROOT / "windows" / "cloudflared.exe"
STATE = ROOT / "windows" / "state.json"
os.chdir(ROOT)

def say(msg): print(f"[Forgevia] {msg}", flush=True)

def ensure_deps():
    try:
        import fastapi, uvicorn, bs4, httpx, multipart, lxml  # noqa
    except ImportError:
        say("Installing requirements (one time, ~1 min)...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "fastapi", "uvicorn", "beautifulsoup4", "httpx", "python-multipart", "lxml"])

def ensure_node():
    try: subprocess.run(["node", "-v"], capture_output=True, check=True); return True
    except Exception:
        say("Node.js not found - JavaScript code running will be disabled (install from nodejs.org to enable)."); return False

def ensure_tunnel():
    if TUN.exists(): return
    say("Downloading tunnel client (one time, ~30 MB)...")
    url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
    urllib.request.urlretrieve(url, TUN)

def start_server():
    say(f"Starting Forgevia on port {PORT}...")
    env = {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}
    p = subprocess.Popen([sys.executable, "-X", "utf8", "-m", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", str(PORT)], cwd=ROOT, env=env)
    for _ in range(60):
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{PORT}/health", timeout=2); return p
        except Exception: time.sleep(1)
    raise SystemExit("Server did not start. Scroll up for the error.")

def start_tunnel():
    say("Opening public tunnel...")
    p = subprocess.Popen([str(TUN), "tunnel", "--url", f"http://127.0.0.1:{PORT}", "--no-autoupdate"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
    url = None
    for line in p.stdout:
        m = re.search(r"https://[a-z0-9-]+\.trycloudflare\.com", line)
        if m: url = m.group(0); break
    if not url: raise SystemExit("Tunnel failed to start. Check your internet connection and run again.")
    threading.Thread(target=lambda: [None for _ in p.stdout], daemon=True).start()
    return p, url

def main():
    os.system("title Forgevia - keep this window open")
    ensure_deps(); ensure_node(); ensure_tunnel()
    srv = start_server(); tun, url = start_tunnel()
    STATE.write_text(json.dumps({"url": url, "started": time.time()}))
    print("\n" + "=" * 64)
    print("  FORGEVIA IS LIVE ON THE INTERNET")
    print(f"  Public URL : {url}")
    print(f"  Local URL  : http://localhost:{PORT}")
    print("  Keep this window open. Close it to go offline.")
    print("=" * 64 + "\n")
    try: webbrowser.open(url)
    except Exception: pass
    try:
        while True:
            time.sleep(5)
            if srv.poll() is not None: say("Server stopped - restarting..."); srv = start_server()
            if tun.poll() is not None: say("Tunnel dropped - reconnecting..."); tun, url = start_tunnel(); print(f"  New public URL: {url}")
    except KeyboardInterrupt:
        pass
    finally:
        for p in (tun, srv):
            try: p.terminate()
            except Exception: pass

if __name__ == "__main__":
    main()
