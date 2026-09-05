# Forgevia — Step-by-Step User Guide

Sign in → you land on **Home** (dashboard). The left sidebar has every section below.

---

## 1. Projects (Home)
A project = one website or app.

1. Click **New project**.
2. Give it a name (lowercase, e.g. `my-shop`). This becomes your URL: `/sites/my-shop/`.
3. Pick a **template** (blank, landing page, portfolio, blog, Flask/Python app, Node app, …).
4. Click **Create** → the editor opens.

Other ways to get a project in:
- **Import ZIP** — upload a zip of an existing site.
- **Account → Import from GitHub** — paste a repo URL.
- Open any project card → **⋯** → **Duplicate / Rename / Export ZIP / Delete**.

## 2. Editor (build your site)
- **File tree** (left): click a file to open; right-click / **+** to add, rename, delete or upload files.
- **Code area** (centre): edit HTML, CSS, JS, Python, etc. Autosaves.
- **Format** — tidies your code.
- **Preview** — see the page live on the right as you type.
- **Assist** — AI helper: describe what you want ("add a contact form", "make the header dark") and it writes/edits the code.
- **Terminal** — run commands, or press **Run** to execute Python/Node code and see output.
- **Publish** — one-click deploy (same as Deploy tab).
- Shortcuts: Ctrl+S save · Ctrl+P search files · Ctrl+Enter run.

## 3. Deploy (put it online)
1. Open **Deploy**.
2. Click **Publish now** → your site is live at `https://<your-domain>/sites/<project>/` in ~1 second.
3. **Copy** the link or click **QR** to share it.
4. Every publish creates a **Version** — restore any earlier one from the versions list.
5. **Unpublish** takes it offline; **Export ZIP** downloads everything.

For **dynamic apps** (Flask / Node servers):
- **App process → Start / Restart**. Forgevia runs your `app.py` / `server.js` in a sandbox.
- **Logs** shows live output; **Stop** halts it.

**Custom domain:** Deploy → Domains → add `www.yourbrand.com` → copy the DNS CNAME shown → add it at your registrar → **Verify**.

**Export to GitHub:** connect GitHub in Account, then push with a commit message.

## 4. SEO Suite
- **Audit** — paste any URL → score /100 plus a list of issues (title length, meta description, headings, images without alt, speed, security headers) with fixes.
- **Site crawl** — audits every page of a site at once and finds broken links / 404s.
- **Keywords** — enter a topic → keyword ideas with related searches.
- **Generator** — enter topic, keywords, brand, page type → generates title tag, meta description, headings and schema markup you can paste in.
- **Auto-fix** — pick one of your projects → Forgevia fixes common SEO problems in the code automatically.

## 5. Web Scraper
1. Enter a URL → **Inspect** to see the page's structure.
2. Enter a CSS selector (e.g. `h2`, `.price`, `a`) → **Scrape**.
3. Results shown in a table → download as **JSON** or **CSV**, or **Copy**.
Also: **Screenshot** captures a full-page image of any site.

## 6. Analytics
Select a published project → visits, **Top pages**, **Referrers**, **Devices**, **Browsers** over time. No setup needed — tracking is built into published sites.

## 7. Forms
Any HTML form on your site can post to `/api/forms/<project>/<form-name>`.
Submissions (contact forms, sign-ups, orders) appear here → export **CSV**.

## 8. Uptime Monitor
**Add monitor** → URL + interval. Forgevia pings it and shows up/down history and response time.

## 9. Toolbox
- **Domain availability** — type a name → see free TLDs (.com/.io/.app…) with buy links.
- **Page speed** — load-time test for any URL.
- **HTTP headers & security** — checks HTTPS, HSTS, CSP, etc.
- **DNS lookup** and **WHOIS**.
- **Share a snippet** — paste code → get a public link.
- **Playground** — run Python/JS instantly without a project.

## 10. Account
- Profile, **Sign out**.
- **Connections** — connect GitHub / Google.
- **Import from GitHub**.
- **Keyboard shortcuts** list.

---

## Typical first-time flow (5 minutes)
1. Home → **New project** → "landing page" template → Create
2. Editor → change the headline text → watch Preview update
3. **Publish** → copy the live link → open it
4. SEO → **Audit** your live link → apply suggestions (or **Auto-fix**)
5. Analytics → watch the visits arrive
