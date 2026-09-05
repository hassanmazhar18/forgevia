# Forgevia
All-in-one web platform: build, deploy, SEO-audit, scrape, run code.

Runs anywhere with Docker (`Dockerfile`, port 8000) or directly: `pip install fastapi uvicorn beautifulsoup4 httpx python-multipart lxml && python -m uvicorn server:app --host 0.0.0.0 --port 8000`.

Optional env vars: `FV_DATA` (data dir), `FV_BACKUP_REPO` + `FV_BACKUP_TOKEN` (GitHub backup, see persist.py).
