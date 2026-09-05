# Put Forgevia online for FREE (no credit card) — about 10 minutes

Host: **Hugging Face Spaces** (free forever: 2 CPU, 16 GB RAM, HTTPS URL, no card).
Your public address will be `https://<your-name>-forgevia.hf.space`.

Everything technical is already done and packaged in `forgevia-upload.zip`. You only click.

---
## Part A — create the free accounts (3 min)
1. **GitHub** → https://github.com/signup (free). This will safely store your users' data.
2. **Hugging Face** → https://huggingface.co/join (free). This runs the website.
   Confirm both emails.

## Part B — a private backup repo on GitHub (2 min)
Free hosts wipe the disk on restart; Forgevia auto-saves everything here every 10 min and restores on boot.
1. https://github.com/new → Repository name: `forgevia-data` → tick **Private** → **Create repository**.
2. Get a token: https://github.com/settings/tokens/new
   - Note: `forgevia` · Expiration: **No expiration** · tick the **`repo`** box → **Generate token**.
   - **Copy the token (starts with `ghp_`)** — you'll paste it in Part D.

## Part C — create the Space (2 min)
1. https://huggingface.co/new-space
   - Space name: `forgevia`
   - License: any · **SDK: Docker** → **Blank** · Hardware: **CPU basic (free)** · **Public**
   - **Create Space**.
2. Click the **Files** tab → **Add file → Upload files**.
3. Unzip `forgevia-upload.zip` on your computer and drag **everything inside the `forgevia` folder** (server.py, Dockerfile, README.md, static/, …) into the upload box → **Commit changes to main**.
   The Space starts building (2–4 minutes). Watch the **Logs** tab.

## Part D — connect the backup (1 min)
Space → **Settings** → **Variables and secrets** → **New secret** (twice):
| Name | Value |
|---|---|
| `FV_BACKUP_REPO` | `your-github-username/forgevia-data` |
| `FV_BACKUP_TOKEN` | the `ghp_…` token from Part B |
Then **Settings → Factory reboot** (top of settings). Logs should show `persist: enabled`.

## Part E — you're live 🎉
1. Open `https://<your-name>-forgevia.hf.space`.
2. Sign in with **has2255000@gmail.com / your password** (the owner account is included in the first boot; change the password from Account).
3. Share the link. Real users can sign up, build, deploy sites, run SEO audits — all free.

---
## Free custom domain (optional, later)
- Free subdomains: https://freedns.afraid.org or https://www.duckdns.org → CNAME to your Space, or
- Use **Cloudflare** (free) in front when you buy a real domain (~$10/yr) later.

## Updating Forgevia later
Upload the changed files in the Space's **Files** tab → it rebuilds automatically. Data is safe in GitHub.

## Limits of the free tier (honest list)
- Space **sleeps after 48 h without visitors**; first visit after that takes ~30 s to wake. (Add a free uptime pinger such as https://uptimerobot.com hitting `/health` every 5 min to keep it awake.)
- Backup snapshot must stay under ~95 MB (thousands of normal websites fit). When you outgrow it, move to a $5 VPS using `deploy/install.sh`.
- No custom domain directly on the Space — use the Cloudflare option above.
