# Deploy Forgevia to Google Cloud — step by step

Cost: ~US$7–13/month (e2-small VM). New Google accounts get $300 free credit.

## Step 1 — Buy a domain (10 min)
Namecheap / Cloudflare / GoDaddy → e.g. `forgevia.io` (was free at last check). Cost ≈ $10–35/yr.

## Step 2 — Create the Google Cloud VM (10 min)
1. Go to https://console.cloud.google.com → create a project ("forgevia") → enable billing.
2. Menu → **Compute Engine → VM instances → Create instance**
   - Name: `forgevia`
   - Region: `asia-south1` (Mumbai) — closest to Pakistan
   - Machine: **e2-small** (2 vCPU, 2 GB) — e2-medium if you expect many users
   - Boot disk: **Ubuntu 24.04 LTS**, 30 GB
   - Firewall: tick **Allow HTTP** and **Allow HTTPS**
   - Create.
3. VM instances → click the ⋮ next to the External IP → **Reserve static IP** (so it never changes). Copy the IP.

## Step 3 — Point your domain at the VM (5 min, then wait)
At your registrar's DNS page add:
| Type | Name | Value |
|---|---|---|
| A | @ | your VM IP |
| A | www | your VM IP |
| A | * | your VM IP (lets user sites get subdomains later) |
Propagation: 5 min – 1 hour. Check with https://dnschecker.org.

## Step 4 — Upload Forgevia to the VM (5 min)
Download the `forgevia` folder from this workspace as a zip. Then in the Google console click **SSH** next to the VM (opens a browser terminal) → use the ⚙ **Upload file** button to upload `forgevia.zip`. Then:
```
sudo apt-get install -y unzip && unzip -o forgevia.zip -d ~/ && cd ~/forgevia
```
(Alternative: push the folder to a private GitHub repo and `git clone` it on the VM.)

## Step 5 — Install (one command, ~5 min)
```
sudo bash deploy/install.sh yourdomain.com you@email.com
```
This installs Python/Node/nginx, creates the sandbox user, starts Forgevia as a system service (auto-restart, starts on reboot), configures nginx and gets a **free HTTPS certificate** (auto-renews).

## Step 6 — Open https://yourdomain.com 🎉
- Sign in with your owner account (has2255000@gmail.com).
- Go to `/setup` to add GitHub/Google login keys (optional).
- Cookies work normally on a real domain, so users stay logged in.

## Step 7 — Get on Google Search
1. https://search.google.com/search-console → Add property → your domain → verify via the DNS TXT record they give you.
2. Submit sitemap: `https://yourdomain.com/sitemap.xml`.
3. Use Forgevia's own **SEO → Audit** on your landing page and fix what it flags.
4. Google Business Profile + a few backlinks (Product Hunt, Reddit, LinkedIn post) speed up indexing.

## Maintenance
| Task | Command (in VM SSH) |
|---|---|
| Status | `systemctl status forgevia` |
| Live logs | `journalctl -u forgevia -f` |
| Restart | `sudo systemctl restart forgevia` |
| Update code | upload new zip / `git pull` → `sudo systemctl restart forgevia` |
| Backup | `tar czf backup.tgz /opt/forgevia/src/data /opt/forgevia/src/projects` (do this daily; Google **snapshot schedule** on the disk also works) |
