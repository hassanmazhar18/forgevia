# Put Forgevia Online — FREE — Every Click Explained (Back4app edition)

Cost: **$0**, no credit card. Host: **Back4app Containers** (free plan: 1 container, HTTPS, deploy from GitHub — no card, ever).
Backup: **GitHub** (free) so users' data is never lost.

You already did: GitHub account ✅, `forgevia` repo with the code ✅, backup repo ✅ (`forgevia-data` or `forgevia-backup`), token `ghp_…` ✅.
If any of these is missing, see the end of this file.

Your site will be at: **https://forgevia-XXXX.b4a.run**

---

# PART A — Create the Back4app account (2 min)
1. Go to **https://www.back4app.com/** → click **Sign up** (top right).
2. Choose **Sign up with GitHub** → **Authorize**. (Or email + password, then confirm the email.)
3. If a short questionnaire appears (role, purpose), pick anything → Continue.
4. You land on the Back4app dashboard. ✅

# PART B — Create the container (5 min)
1. Click **NEW APP** (big button, top-left / centre).
2. Two cards appear: *Backend as a Service* and **Containers as a Service** → click **Containers as a Service**.
3. It says "Import a GitHub repo". Click **Install GitHub App** (opens GitHub) → choose your account → select **Only select repositories** → pick **forgevia** → **Install & Authorize**.
4. Back in Back4app, your `forgevia` repository appears in the list → click **Select**.
5. Configuration form:
   - **App name**: `forgevia`
   - **Branch**: `main`
   - **Root directory**: leave empty
   - **Auto-deploy**: on
   - **Port**: `8000`  ← important
   - **Health check path**: `/health`
   - **Environment variables** → click **Add** three times:

     | Name | Value |
     |---|---|
     | `PORT` | `8000` |
     | `FV_BACKUP_REPO` | `YOUR-GITHUB-USERNAME/forgevia-data` (use `forgevia-backup` if that's the name you created) |
     | `FV_BACKUP_TOKEN` | your `ghp_…` key |
   - **Plan**: **Free** (0.25 CPU, 256 MB).
6. Click **Create App** (or **Deploy**).
7. Wait 3–6 minutes. Status goes *Deploying* → **Ready**. The **Logs** tab will show `Uvicorn running on http://0.0.0.0:8000` and `persist: enabled → …`.
8. Your URL is at the top of the app page, e.g. `https://forgevia-abc123.b4a.run`. Click it. 🎉

# PART C — Sign in and take ownership (1 min)
1. Open the URL → **Start building** → **Sign in** with `has2255000@gmail.com` + your password.
2. **Account** → change your password to a new strong one.
3. Test: New project → Publish → open the live link. ✅

# PART D — Tell people (free)
- WhatsApp, Facebook groups, LinkedIn, Reddit (r/webdev, r/SideProject), X.
- Product Hunt: https://www.producthunt.com/posts/new
- Google Search Console: https://search.google.com/search-console → URL prefix → your address → verify → submit `sitemap.xml`.

---

## Free-plan notes (honest)
- 256 MB RAM: enough for Forgevia (it uses ~90 MB idle). Heavy code runs by many users at once may be slow; upgrade later ($5/mo) or move to a VPS with `deploy/install.sh` when you earn.
- The container may sleep when idle; the first visit after that takes ~20–40 s. Optional free fix: https://uptimerobot.com → monitor `https://YOUR-URL/health` every 5 min.
- Custom domain: Back4app allows one on the free plan → app **Settings → Custom domain** → add CNAME at your DNS provider (DuckDNS gives free subdomains).

## Updating Forgevia later
New zip from me → GitHub `forgevia` repo → **Add file → Upload files** → Commit. Back4app redeploys automatically. Data is safe in your backup repo.

## If something goes wrong
| What you see | Do |
|---|---|
| Build failed | App → **Logs / Build** → copy last 20 lines → paste to me. |
| "Unhealthy" | Check Port = 8000 and health path = /health. |
| Logs: `persist: not configured` | Variable names misspelled or missing. |
| Logs: `persist: backup failed 404` | `FV_BACKUP_REPO` must be exactly `username/repo-name`. |
| Logs: `persist: backup failed 401` | Token wrong → make a new one at github.com/settings/tokens/new (repo scope), update the variable, redeploy. |

## If you skipped an earlier step
- **Code repo:** github.com/new → name `forgevia` → Create → "uploading an existing file" → drag the contents of the extracted `forgevia` folder → Commit.
- **Backup repo:** github.com/new → name `forgevia-backup` → Private → Create.
- **Token:** github.com/settings/tokens/new → Note `forgevia` → No expiration → tick `repo` → Generate → copy `ghp_…`.
