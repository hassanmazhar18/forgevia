"""Forgevia Assistant — offline, rule-based coding helper.
Generates components, explains errors, answers platform questions. No API key needed.
(Plug in any LLM API in `respond()` to make it fully generative.)"""
import re

SNIPPETS = {
 "navbar": ("Responsive navbar", """<nav class="fv-nav"><a class="brand" href="/">Brand</a><button class="burger" onclick="this.nextElementSibling.classList.toggle('open')">☰</button><ul><li><a href="#">Home</a></li><li><a href="#">About</a></li><li><a href="#">Contact</a></li></ul></nav>
<style>.fv-nav{display:flex;align-items:center;justify-content:space-between;padding:14px 5vw;background:#fff;border-bottom:1px solid #eee;position:sticky;top:0}.fv-nav .brand{font-weight:800;text-decoration:none;color:#111}.fv-nav ul{display:flex;gap:24px;list-style:none;margin:0;padding:0}.fv-nav a{color:#333;text-decoration:none}.burger{display:none;background:none;border:0;font-size:22px}@media(max-width:640px){.burger{display:block}.fv-nav ul{display:none;position:absolute;top:56px;left:0;right:0;background:#fff;flex-direction:column;padding:16px 5vw;gap:14px}.fv-nav ul.open{display:flex}}</style>"""),
 "hero": ("Hero section", """<section class="hero"><h1>Your headline that sells</h1><p>A supporting sentence that explains the value in one line.</p><a class="cta" href="#">Get started free</a></section>
<style>.hero{text-align:center;padding:16vh 6vw;background:radial-gradient(ellipse at top,#ede9fe,#fff 60%)}.hero h1{font-size:clamp(2.2rem,6vw,4rem);letter-spacing:-.03em;margin:0 0 16px}.hero p{font-size:1.2rem;color:#555;max-width:520px;margin:0 auto 28px}.cta{background:#7c5cff;color:#fff;padding:14px 28px;border-radius:10px;text-decoration:none;font-weight:600}</style>"""),
 "contact form": ("Contact form (submits to Forgevia Forms)", """<form action="/api/forms/PROJECT/contact" method="post" class="fv-form"><input name="name" placeholder="Your name" required><input name="email" type="email" placeholder="Email" required><textarea name="message" rows="4" placeholder="Message" required></textarea><button>Send message</button></form>
<style>.fv-form{display:grid;gap:12px;max-width:460px}.fv-form input,.fv-form textarea{padding:12px;border:1px solid #ddd;border-radius:8px;font:inherit}.fv-form button{padding:12px;background:#111;color:#fff;border:0;border-radius:8px;cursor:pointer}</style>
<!-- Submissions appear in Dashboard → Forms -->"""),
 "pricing": ("Pricing table", """<div class="pricing"><div><h3>Starter</h3><p class="p">$0</p><ul><li>1 project</li><li>Community</li></ul><a href="#">Choose</a></div><div class="hot"><h3>Pro</h3><p class="p">$12<span>/mo</span></p><ul><li>Unlimited</li><li>Custom domain</li><li>Priority support</li></ul><a href="#">Choose</a></div><div><h3>Team</h3><p class="p">$49<span>/mo</span></p><ul><li>5 seats</li><li>SSO</li></ul><a href="#">Choose</a></div></div>
<style>.pricing{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:20px;max-width:900px;margin:auto}.pricing>div{border:1px solid #e5e7eb;border-radius:14px;padding:24px;text-align:center}.pricing .hot{border-color:#7c5cff;box-shadow:0 10px 40px #7c5cff22}.pricing .p{font-size:2.4rem;font-weight:800;margin:8px 0}.pricing span{font-size:1rem;color:#999}.pricing ul{list-style:none;padding:0;color:#555}.pricing a{display:inline-block;background:#7c5cff;color:#fff;padding:10px 20px;border-radius:8px;text-decoration:none}</style>"""),
 "footer": ("Footer", """<footer class="fv-footer"><div><b>Brand</b><p>Made with care.</p></div><div><b>Product</b><a href="#">Features</a><a href="#">Pricing</a></div><div><b>Company</b><a href="#">About</a><a href="#">Contact</a></div><small>© 2026 Brand. All rights reserved.</small></footer>
<style>.fv-footer{display:grid;grid-template-columns:2fr 1fr 1fr;gap:24px;padding:48px 6vw 24px;background:#0f172a;color:#cbd5e1}.fv-footer a{display:block;color:#94a3b8;text-decoration:none;margin-top:8px}.fv-footer small{grid-column:1/-1;border-top:1px solid #1e293b;padding-top:16px;color:#64748b}@media(max-width:600px){.fv-footer{grid-template-columns:1fr}}</style>"""),
 "faq": ("FAQ accordion (with SEO schema)", """<section class="faq"><h2>FAQ</h2><details><summary>How does it work?</summary><p>Answer goes here.</p></details><details><summary>Is there a free plan?</summary><p>Yes.</p></details></section>
<script type="application/ld+json">{"@context":"https://schema.org","@type":"FAQPage","mainEntity":[{"@type":"Question","name":"How does it work?","acceptedAnswer":{"@type":"Answer","text":"Answer goes here."}},{"@type":"Question","name":"Is there a free plan?","acceptedAnswer":{"@type":"Answer","text":"Yes."}}]}</script>
<style>.faq{max-width:700px;margin:auto;padding:40px 20px}.faq details{border-bottom:1px solid #eee;padding:14px 0}.faq summary{cursor:pointer;font-weight:600;font-size:1.05rem}.faq p{color:#555;margin:10px 0 0}</style>"""),
 "testimonials": ("Testimonials grid", """<section class="testi"><blockquote>"Absolutely love it. Saved us weeks."<cite>— Sara K., Founder</cite></blockquote><blockquote>"The best tool in our stack."<cite>— Ali R., CTO</cite></blockquote><blockquote>"Fast, simple, reliable."<cite>— Maya L., Designer</cite></blockquote></section>
<style>.testi{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:20px;padding:40px 6vw}.testi blockquote{margin:0;padding:24px;background:#f8fafc;border-radius:14px;font-size:1.05rem}.testi cite{display:block;margin-top:12px;color:#777;font-style:normal;font-size:.9rem}</style>"""),
 "gallery": ("Image gallery", """<div class="gallery"><img src="https://picsum.photos/seed/1/600/400" alt="Photo 1" loading="lazy"><img src="https://picsum.photos/seed/2/600/400" alt="Photo 2" loading="lazy"><img src="https://picsum.photos/seed/3/600/400" alt="Photo 3" loading="lazy"><img src="https://picsum.photos/seed/4/600/400" alt="Photo 4" loading="lazy"></div>
<style>.gallery{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:12px;padding:20px}.gallery img{width:100%;aspect-ratio:3/2;object-fit:cover;border-radius:10px;transition:.2s}.gallery img:hover{transform:scale(1.03)}</style>"""),
 "dark mode": ("Dark mode toggle", """<button id="theme" onclick="document.documentElement.classList.toggle('dark');localStorage.theme=document.documentElement.classList.contains('dark')?'dark':'light'">🌓</button>
<script>if(localStorage.theme==='dark')document.documentElement.classList.add('dark')</script>
<style>:root{--bg:#fff;--fg:#111}:root.dark{--bg:#0b0d12;--fg:#e6e8ef}body{background:var(--bg);color:var(--fg);transition:.3s}#theme{position:fixed;bottom:20px;right:20px;border:0;border-radius:50%;width:44px;height:44px;font-size:20px;cursor:pointer}</style>"""),
 "modal": ("Modal dialog", """<button onclick="m.showModal()">Open modal</button>
<dialog id="m"><h3>Title</h3><p>Modal content.</p><button onclick="m.close()">Close</button></dialog>
<style>dialog{border:0;border-radius:14px;padding:28px;max-width:420px}dialog::backdrop{background:#0006;backdrop-filter:blur(3px)}</style>"""),
 "seo head": ("Complete SEO <head>", """<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Page Title — 50-60 chars, keyword first</title>
<meta name="description" content="A compelling 120-160 character description that includes your primary keyword and a reason to click.">
<link rel="canonical" href="https://yourdomain.com/this-page">
<meta property="og:type" content="website">
<meta property="og:title" content="Page Title">
<meta property="og:description" content="Same as description">
<meta property="og:image" content="https://yourdomain.com/og.jpg">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/favicon.ico">
<script type="application/ld+json">{"@context":"https://schema.org","@type":"WebSite","name":"Site Name","url":"https://yourdomain.com"}</script>"""),
 "fetch": ("Fetch JSON from an API", """async function load(){
  const res = await fetch('/api/hello');
  if(!res.ok) throw new Error('HTTP ' + res.status);
  const data = await res.json();
  console.log(data);
}
load().catch(console.error);"""),
 "kv": ("Use Forgevia KV storage from the browser", """// Simple persistent storage — no backend code needed
const KV = '/api/kv/PROJECT';
const get = k => fetch(`${KV}/${k}`).then(r => r.ok ? r.json() : null);
const set = (k, v) => fetch(`${KV}/${k}`, {method:'PUT', headers:{'Content-Type':'application/json'}, body: JSON.stringify(v)});
// usage:
// await set('likes', (await get('likes') || 0) + 1);"""),
 "python server": ("Minimal Python HTTP server", """import os
from http.server import HTTPServer, BaseHTTPRequestHandler
class H(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.send_header('Content-Type','text/html'); self.end_headers()
        self.wfile.write(b'<h1>Hello from Python</h1>')
HTTPServer(('0.0.0.0', int(os.environ.get('PORT', 8080))), H).serve_forever()"""),
 "scrape": ("Python scraper with BeautifulSoup", """import httpx
from bs4 import BeautifulSoup
html = httpx.get('https://example.com', follow_redirects=True).text
soup = BeautifulSoup(html, 'html.parser')
for a in soup.select('a[href]'):
    print(a.get_text(strip=True), a['href'])"""),
}

ERRORS = [
 (r"SyntaxError.*unexpected token|Unexpected token", "JavaScript syntax error. Check for a missing bracket, comma, or quote near the line mentioned. Common cause: a `}` or `)` left unclosed above that line."),
 (r"is not defined|ReferenceError", "You're using a variable or function before it's declared, or it's misspelled. Check spelling and make sure the `<script>` that defines it loads first."),
 (r"Cannot read propert(y|ies) of (undefined|null)", "You're accessing `.something` on a value that is undefined/null. Usually an element lookup failed (`document.getElementById` returned null — check the id) or data hasn't loaded yet (await it)."),
 (r"IndentationError", "Python indentation problem. Use 4 spaces consistently and make sure block bodies (after `:`) are indented."),
 (r"ModuleNotFoundError: No module named '(\w+)'", "Python package `{1}` isn't installed. Add it to `requirements.txt` (one per line) and Publish again — Forgevia installs it automatically."),
 (r"Cannot find module '([^']+)'", "Node package `{1}` is missing. Add it to `package.json` dependencies and Publish — Forgevia runs `npm install`."),
 (r"EADDRINUSE|Address already in use", "Port already in use. Make sure your server listens on `process.env.PORT` / `os.environ['PORT']`, not a hard-coded number."),
 (r"CORS|Access-Control-Allow-Origin", "Cross-origin request blocked. Call the API from the same origin (use a relative URL like `/api/...`) or add `Access-Control-Allow-Origin` headers on the server."),
 (r"404", "Resource not found. Check the file path/spelling and that the file is inside your project and was published."),
 (r"502|not responding", "Your app crashed or isn't listening on the right port. Open Deploy → Logs. Ensure the server binds `0.0.0.0` and uses the `PORT` env var."),
 (r"TypeError.*not a function", "You're calling something that isn't a function. Check the spelling of the method and that the object is what you think it is (`console.log(typeof x)`)."),
 (r"KeyError: '?(\w+)'?", "Python dict has no key `{1}`. Use `.get('{1}')` for a safe lookup or check the key name."),
 (r"NameError: name '(\w+)'", "Python: `{1}` isn't defined. Define it before use or check the spelling/import."),
]

FAQ = [
 (r"publish|deploy|go live|live url", "**Publishing:** click the 🚀 **Publish** button in the editor. Static sites go live instantly at `/sites/<project>/`. Python/Node apps are started automatically and proxied to the same URL. Every publish creates a restorable snapshot under **Versions**."),
 (r"custom domain|own domain|dns", "**Custom domains:** Project → Settings → Domains → add your domain. You'll get DNS records (CNAME/A + a TXT verification token). Add them at your registrar, then click *Verify*. Propagation takes 5 min–24 h."),
 (r"form|submission|contact", "**Forms:** point any `<form>` to `action=\"/api/forms/<project>/<form-name>\" method=\"post\"`. Submissions land in the **Forms** tab, no backend code needed. Add `<input type=hidden name=_next value=\"/thanks.html\">` to redirect after submit."),
 (r"database|store data|persist|kv", "**Storage:** every project has a built-in KV store — `GET/PUT/DELETE /api/kv/<project>/<key>` with JSON bodies. Works from browser JS or your Python/Node backend. Type `kv` for a snippet."),
 (r"seo|rank|google", "**SEO:** use **SEO → Audit** for a 25-point report, **Crawl** to scan a whole site, **Keywords** for ideas, **Generate** for meta tags/schema, and **Auto-fix** to patch missing tags across all your HTML files automatically."),
 (r"scrap|extract|crawl data", "**Scraper:** paste a URL, pick a mode (text, links, images, tables, emails, JSON-LD, markdown…) or use CSS selectors. Define *fields* for structured rows (e.g. `title: h2 a`, `link: h2 a@href`). Multi-page with a next-button selector. Export JSON/CSV."),
 (r"python|flask|node|backend|api|server", "**Backend apps:** create a project from the *Python* or *Node.js* template. Your server must listen on `$PORT` (bind `0.0.0.0`). Dependencies from `requirements.txt` / `package.json` install on publish. Logs are in **Deploy**."),
 (r"password|private|protect", "**Password-protect** a site under Project → Settings. Visitors get a lock screen before viewing."),
 (r"analytics|visitors|traffic", "**Analytics** are built in and privacy-friendly (no cookies). Published sites get a tiny beacon; view page views, uniques, referrers, devices under the **Analytics** tab. Add a Google Analytics ID in Settings to also send data there."),
 (r"version|history|undo|restore|rollback", "**Versions:** every publish and manual snapshot is saved (last 30). Open **Versions** to restore any of them with one click."),
 (r"monitor|uptime|down", "**Uptime monitor:** add any URL under **Monitor**. Forgevia pings it every 5 minutes and records status, response time and uptime %."),
 (r"upload|image|file", "**Uploads:** drag files onto the file tree or use the ⬆ button. Images, fonts, PDFs — anything. Reference them by relative path."),
 (r"template", "**Templates:** Landing, Portfolio, Blog, Docs, Restaurant, Store, Coming-soon, Python API, Node API. Choose one when creating a project; everything is editable."),
 (r"shortcut|hotkey", "**Shortcuts:** `Ctrl+S` save · `Ctrl+P` quick-open file · `Ctrl+Shift+P` publish · `Ctrl+\\`` terminal · `Ctrl+B` toggle sidebar · `Ctrl+/` comment."),
 (r"^(hi|hello|hey)\b", "Hey! I'm the Forgevia assistant. Ask me to **generate** components (`navbar`, `hero`, `pricing`, `contact form`, `faq`, `gallery`, `dark mode`, `seo head`…), **explain an error** (paste it), or ask **how to** do anything on the platform."),
]

def respond(prompt: str, context: str = "", file: str = ""):
    p = prompt.strip(); pl = p.lower()
    # error explanation
    for pat, msg in ERRORS:
        m = re.search(pat, p, re.I)
        if m:
            for i, g in enumerate(m.groups(), 1): msg = msg.replace("{%d}" % i, g or "")
            return {"type": "explain", "text": "🔍 **Error diagnosis**\n\n" + msg}
    # snippet generation
    for key, (title, code) in SNIPPETS.items():
        if key in pl or all(w in pl for w in key.split()):
            return {"type": "code", "title": title, "code": code, "text": f"Here's a **{title}**. Click *Insert* to add it at your cursor, or *Copy*."}
    if re.search(r"\b(make|create|generate|build|add|write)\b", pl):
        return {"type": "text", "text": "I can generate these right now: " + ", ".join(f"`{k}`" for k in SNIPPETS) + ".\n\nTell me which one, e.g. *“add a pricing table”*."}
    # explain selected code
    if context and re.search(r"explain|what does|what is this", pl):
        lines = context.count("\n") + 1; kinds = []
        if "<" in context and ">" in context: kinds.append("HTML markup")
        if "{" in context and ":" in context and ";" in context: kinds.append("CSS rules")
        if re.search(r"\b(function|const|let|=>)\b", context): kinds.append("JavaScript")
        if re.search(r"\bdef |import |print\(", context): kinds.append("Python")
        fns = re.findall(r"function\s+(\w+)|def\s+(\w+)|const\s+(\w+)\s*=", context)
        names = [n for t in fns for n in t if n]
        return {"type": "text", "text": f"This selection is {lines} line(s) of {' + '.join(kinds) or 'code'}." + (f" It defines: `{'`, `'.join(names[:8])}`." if names else "") + "\n\nPaste a specific error or ask about a line and I'll go deeper."}
    for pat, msg in FAQ:
        if re.search(pat, pl): return {"type": "text", "text": msg}
    return {"type": "text", "text": "I can help with:\n• **Generate** UI: navbar, hero, pricing, contact form, FAQ, footer, testimonials, gallery, modal, dark mode, SEO head\n• **Explain errors** — paste any error message\n• **How-to** questions about publishing, domains, forms, storage, SEO, scraping, analytics\n\nWhat would you like?"}
