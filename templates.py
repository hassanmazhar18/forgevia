"""Starter templates for Forgevia projects."""

_HEAD = """<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta name="twitter:card" content="summary_large_image">
<link rel="stylesheet" href="style.css">"""

def head(t, d): return _HEAD.format(title=t, desc=d)

TEMPLATES = {
 "blank": {"name": "Blank", "desc": "Empty HTML/CSS/JS starter", "icon": "📄", "cat": "Basic", "kind": "static", "files": {
  "index.html": f"""<!DOCTYPE html>
<html lang="en">
<head>
{head("{{NAME}}", "A new site built with Forgevia.")}
</head>
<body>
  <main>
    <h1>Hello, world 👋</h1>
    <p>Your site <b>{{{{NAME}}}}</b> is ready. Edit <code>index.html</code>, then hit <b>Publish</b>.</p>
  </main>
  <script src="app.js"></script>
</body>
</html>""",
  "style.css": ":root{--acc:#7c5cff}*{box-sizing:border-box}body{font-family:system-ui,sans-serif;margin:0;min-height:100vh;display:grid;place-items:center;background:#0b0d12;color:#e6e8ef}main{text-align:center;padding:2rem}h1{font-size:3rem;background:linear-gradient(90deg,var(--acc),#22d3ee);-webkit-background-clip:text;color:transparent}code{background:#1b2030;padding:2px 6px;border-radius:4px}",
  "app.js": "console.log('Forgevia site ready');"}},

 "landing": {"name": "SaaS Landing", "desc": "Hero, features, pricing, CTA, contact form", "icon": "🚀", "cat": "Business", "kind": "static", "files": {
  "index.html": f"""<!DOCTYPE html>
<html lang="en">
<head>
{head("{{NAME}} — Launch faster", "The modern way to build your product. Try {{NAME}} free.")}
</head>
<body>
<nav><a class="logo" href="#">{{{{NAME}}}}</a><div><a href="#features">Features</a><a href="#pricing">Pricing</a><a class="btn" href="#cta">Get started</a></div></nav>
<header class="hero">
  <h1>Build something people love</h1>
  <p>{{{{NAME}}}} helps teams ship faster with less effort. No credit card required.</p>
  <a class="btn big" href="#cta">Start free trial</a>
  <small>Trusted by 2,000+ teams</small>
</header>
<section id="features" class="grid">
  <div><span>⚡</span><h3>Blazing fast</h3><p>Optimised for speed from day one.</p></div>
  <div><span>🔒</span><h3>Secure by default</h3><p>Enterprise-grade security built in.</p></div>
  <div><span>📈</span><h3>Grows with you</h3><p>From side project to unicorn.</p></div>
</section>
<section id="pricing">
  <h2>Simple pricing</h2>
  <div class="grid">
    <div class="plan"><h3>Free</h3><p class="price">$0</p><ul><li>1 project</li><li>Community support</li></ul><a class="btn" href="#cta">Choose</a></div>
    <div class="plan hot"><h3>Pro</h3><p class="price">$12<span>/mo</span></p><ul><li>Unlimited projects</li><li>Priority support</li><li>Custom domain</li></ul><a class="btn" href="#cta">Choose</a></div>
    <div class="plan"><h3>Team</h3><p class="price">$49<span>/mo</span></p><ul><li>Everything in Pro</li><li>5 seats</li><li>SSO</li></ul><a class="btn" href="#cta">Choose</a></div>
  </div>
</section>
<section id="cta" class="cta">
  <h2>Ready to start?</h2>
  <form action="/api/forms/{{{{NAME}}}}/signup" method="post">
    <input name="email" type="email" placeholder="you@company.com" required><button class="btn">Join waitlist</button>
  </form>
  <small>Submissions appear in your Forgevia dashboard → Forms</small>
</section>
<footer>© 2026 {{{{NAME}}}} · Built with Forgevia</footer>
</body>
</html>""",
  "style.css": """*{box-sizing:border-box;margin:0}body{font-family:Inter,system-ui,sans-serif;color:#0f172a;line-height:1.6}
nav{display:flex;justify-content:space-between;align-items:center;padding:18px 6vw;position:sticky;top:0;background:#fffc;backdrop-filter:blur(10px);border-bottom:1px solid #eee}
nav a{color:#334155;text-decoration:none;margin-left:22px}.logo{font-weight:800;font-size:20px;margin:0!important;color:#7c5cff!important}
.btn{background:#7c5cff;color:#fff!important;padding:10px 20px;border-radius:10px;font-weight:600;border:0;cursor:pointer;text-decoration:none;display:inline-block}.btn.big{padding:16px 32px;font-size:18px}
.hero{text-align:center;padding:14vh 6vw 10vh;background:radial-gradient(ellipse at top,#ede9fe,#fff 60%)}.hero h1{font-size:clamp(2.4rem,6vw,4.5rem);letter-spacing:-.03em;line-height:1.05}.hero p{font-size:1.25rem;color:#475569;margin:20px auto 32px;max-width:560px}.hero small{display:block;margin-top:20px;color:#94a3b8}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:24px;padding:60px 6vw;max-width:1100px;margin:auto}.grid>div{padding:28px;border:1px solid #e2e8f0;border-radius:16px}.grid span{font-size:32px}.grid h3{margin:12px 0 6px}
#pricing{text-align:center;background:#f8fafc;padding:60px 0}#pricing h2{font-size:2.2rem}.plan{background:#fff}.plan.hot{border-color:#7c5cff;box-shadow:0 10px 40px #7c5cff22}.price{font-size:2.5rem;font-weight:800;margin:10px 0}.price span{font-size:1rem;color:#94a3b8}.plan ul{list-style:none;padding:0;margin:16px 0;color:#475569}
.cta{text-align:center;padding:80px 6vw}.cta form{display:flex;gap:10px;justify-content:center;margin:24px 0 10px;flex-wrap:wrap}.cta input{padding:14px 18px;border:1px solid #cbd5e1;border-radius:10px;font-size:16px;width:300px}
footer{text-align:center;padding:30px;color:#94a3b8;border-top:1px solid #eee}"""}},

 "portfolio": {"name": "Portfolio", "desc": "Personal site with projects & contact", "icon": "🎨", "cat": "Personal", "kind": "static", "files": {
  "index.html": f"""<!DOCTYPE html>
<html lang="en">
<head>
{head("Your Name — Designer & Developer", "Portfolio of Your Name: selected work, about, and contact.")}
</head>
<body>
<header><h1>Hi, I'm <span>Your Name</span>.</h1><p>I design and build delightful digital products.</p><a href="#work">See my work ↓</a></header>
<section id="work">
  <h2>Selected work</h2>
  <div class="cards">
    <article><img src="https://picsum.photos/seed/a/600/400" alt="Project one preview" loading="lazy"><h3>Project One</h3><p>Brand + web for a fintech startup.</p></article>
    <article><img src="https://picsum.photos/seed/b/600/400" alt="Project two preview" loading="lazy"><h3>Project Two</h3><p>Mobile app for meal planning.</p></article>
    <article><img src="https://picsum.photos/seed/c/600/400" alt="Project three preview" loading="lazy"><h3>Project Three</h3><p>Dashboard for logistics.</p></article>
  </div>
</section>
<section id="about"><h2>About</h2><p>I've spent 6 years shipping products for startups and Fortune 500s alike. I care about craft, speed and accessibility.</p></section>
<section id="contact"><h2>Let's talk</h2>
  <form action="/api/forms/{{{{NAME}}}}/contact" method="post"><input name="name" placeholder="Name" required><input name="email" type="email" placeholder="Email" required><textarea name="message" placeholder="Message" rows="4" required></textarea><button>Send</button></form>
</section>
<footer>© 2026 Your Name</footer>
</body>
</html>""",
  "style.css": """*{box-sizing:border-box;margin:0}body{font-family:Georgia,serif;background:#faf9f6;color:#1a1a1a;line-height:1.7}
header{padding:20vh 8vw 12vh;max-width:900px}h1{font-size:clamp(2.5rem,7vw,5rem);line-height:1;letter-spacing:-.02em}h1 span{color:#c2410c;font-style:italic}header p{font-size:1.4rem;margin:24px 0;color:#555}header a{color:#c2410c}
section{padding:60px 8vw;max-width:1100px}h2{font-size:2rem;margin-bottom:28px}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:32px}article img{width:100%;border-radius:8px;aspect-ratio:3/2;object-fit:cover}article h3{margin:14px 0 4px}article p{color:#666}
form{display:grid;gap:12px;max-width:480px}input,textarea{padding:14px;border:1px solid #ddd;border-radius:6px;font:inherit;background:#fff}button{padding:14px;background:#1a1a1a;color:#fff;border:0;border-radius:6px;font:inherit;cursor:pointer}
footer{padding:40px 8vw;color:#999;border-top:1px solid #eee}"""}},

 "blog": {"name": "Blog", "desc": "Clean multi-page blog with SEO schema", "icon": "✍️", "cat": "Content", "kind": "static", "files": {
  "index.html": f"""<!DOCTYPE html>
<html lang="en">
<head>
{head("{{NAME}} — Blog", "Thoughts on design, code and the web.")}
<script type="application/ld+json">{{"@context":"https://schema.org","@type":"Blog","name":"{{{{NAME}}}}"}}</script>
</head>
<body>
<header><a href="index.html">{{{{NAME}}}}</a><nav><a href="index.html">Posts</a><a href="about.html">About</a></nav></header>
<main>
  <article><time>Sep 4, 2026</time><h2><a href="post-1.html">Why I built this blog with Forgevia</a></h2><p>A short story about shipping fast and owning your platform…</p></article>
  <article><time>Aug 28, 2026</time><h2><a href="post-1.html">10 SEO basics every developer should know</a></h2><p>Titles, descriptions, headings, speed — the fundamentals that still matter.</p></article>
</main>
<footer>© 2026 {{{{NAME}}}}</footer>
</body>
</html>""",
  "post-1.html": f"""<!DOCTYPE html>
<html lang="en">
<head>
{head("Why I built this blog with Forgevia", "A short story about shipping fast and owning your platform.")}
<script type="application/ld+json">{{"@context":"https://schema.org","@type":"Article","headline":"Why I built this blog with Forgevia","datePublished":"2026-09-04"}}</script>
</head>
<body>
<header><a href="index.html">{{{{NAME}}}}</a><nav><a href="index.html">Posts</a><a href="about.html">About</a></nav></header>
<main class="post">
  <time>Sep 4, 2026</time><h1>Why I built this blog with Forgevia</h1>
  <p>I wanted a place to write that I fully control, loads instantly, and ranks well. Here is how it went.</p>
  <h2>Setup took five minutes</h2><p>Pick the blog template, edit a few files, press publish. Done.</p>
  <h2>SEO out of the box</h2><p>Every page ships with proper meta tags, Open Graph, structured data, a sitemap and robots.txt.</p>
  <h2>What's next</h2><p>More posts. Maybe a newsletter. Definitely more coffee.</p>
</main>
<footer>© 2026 {{{{NAME}}}}</footer>
</body>
</html>""",
  "about.html": f"""<!DOCTYPE html>
<html lang="en">
<head>
{head("About — {{NAME}}", "Who writes this blog and why.")}
</head>
<body>
<header><a href="index.html">{{{{NAME}}}}</a><nav><a href="index.html">Posts</a><a href="about.html">About</a></nav></header>
<main class="post"><h1>About</h1><p>I'm a developer who writes about building for the web. This site is hosted on Forgevia.</p></main>
<footer>© 2026 {{{{NAME}}}}</footer>
</body>
</html>""",
  "style.css": """*{box-sizing:border-box;margin:0}body{font-family:-apple-system,system-ui,sans-serif;max-width:700px;margin:0 auto;padding:0 20px;color:#222;line-height:1.75}
header{display:flex;justify-content:space-between;align-items:center;padding:28px 0;border-bottom:1px solid #eee;margin-bottom:40px}header>a{font-weight:800;font-size:22px;color:#111;text-decoration:none}nav a{margin-left:18px;color:#666;text-decoration:none}
article{margin-bottom:44px}time{color:#999;font-size:14px}article h2{margin:6px 0 8px;font-size:1.5rem}article a{color:#111;text-decoration:none}article a:hover{color:#7c5cff}article p{color:#555}
.post h1{font-size:2.4rem;line-height:1.15;margin:8px 0 24px}.post h2{margin:32px 0 8px}.post p{margin-bottom:16px;font-size:1.08rem}
footer{padding:40px 0;color:#aaa;border-top:1px solid #eee;margin-top:60px;font-size:14px}"""}},

 "restaurant": {"name": "Restaurant", "desc": "Menu, hours, location, reservations", "icon": "🍽️", "cat": "Business", "kind": "static", "files": {
  "index.html": f"""<!DOCTYPE html>
<html lang="en">
<head>
{head("{{NAME}} — Fresh, local, delicious", "Book a table at {{NAME}}. Seasonal menu, open daily.")}
<script type="application/ld+json">{{"@context":"https://schema.org","@type":"Restaurant","name":"{{{{NAME}}}}","servesCuisine":"Modern","priceRange":"$$","address":{{"@type":"PostalAddress","streetAddress":"12 Main St","addressLocality":"Lahore"}},"openingHours":"Mo-Su 11:00-23:00"}}</script>
</head>
<body>
<header class="hero"><h1>{{{{NAME}}}}</h1><p>Seasonal food · Warm room · Open every day 11am–11pm</p><a class="btn" href="#book">Reserve a table</a></header>
<section id="menu"><h2>Menu</h2>
  <div class="menu">
    <div><h3>Starters</h3><p>Burrata, peach, basil <b>$14</b></p><p>Charred corn soup <b>$11</b></p></div>
    <div><h3>Mains</h3><p>Grilled sea bass, lemon butter <b>$28</b></p><p>Slow lamb shoulder <b>$32</b></p><p>Wild mushroom risotto <b>$22</b></p></div>
    <div><h3>Desserts</h3><p>Cardamom crème brûlée <b>$10</b></p><p>Chocolate torte <b>$11</b></p></div>
  </div>
</section>
<section id="book"><h2>Reserve</h2>
  <form action="/api/forms/{{{{NAME}}}}/reservation" method="post"><input name="name" placeholder="Name" required><input name="phone" placeholder="Phone" required><input name="date" type="date" required><input name="guests" type="number" min="1" max="12" placeholder="Guests" required><button class="btn">Book now</button></form>
</section>
<footer>12 Main St, Lahore · +92 300 0000000 · © {{{{NAME}}}}</footer>
</body>
</html>""",
  "style.css": """*{box-sizing:border-box;margin:0}body{font-family:Georgia,serif;background:#fffaf3;color:#2b1d0e;line-height:1.7}
.hero{text-align:center;padding:22vh 6vw;background:linear-gradient(#0008,#0008),url(https://picsum.photos/seed/food/1600/900) center/cover;color:#fff}.hero h1{font-size:clamp(3rem,8vw,6rem);letter-spacing:.05em}.hero p{font-size:1.2rem;margin:18px 0 30px}
.btn{background:#c2410c;color:#fff;padding:14px 28px;border-radius:4px;text-decoration:none;border:0;font:inherit;cursor:pointer;display:inline-block}
section{padding:70px 6vw;max-width:1000px;margin:auto}h2{text-align:center;font-size:2.4rem;margin-bottom:36px}.menu{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:40px}.menu h3{border-bottom:2px solid #c2410c;display:inline-block;margin-bottom:12px}.menu p{display:flex;justify-content:space-between;border-bottom:1px dotted #ccc;padding:8px 0}
form{display:grid;grid-template-columns:1fr 1fr;gap:14px;max-width:560px;margin:auto}input{padding:14px;border:1px solid #d6c8b5;border-radius:4px;font:inherit;background:#fff}form .btn{grid-column:1/-1}
footer{text-align:center;padding:36px;color:#8a7560;border-top:1px solid #eadfce}"""}},

 "docs": {"name": "Documentation", "desc": "Sidebar docs site with search", "icon": "📚", "cat": "Content", "kind": "static", "files": {
  "index.html": f"""<!DOCTYPE html>
<html lang="en">
<head>
{head("{{NAME}} Docs", "Documentation for {{NAME}}: getting started, guides and API reference.")}
</head>
<body>
<aside><a class="logo" href="#">{{{{NAME}}}} <small>docs</small></a><input id="q" placeholder="Search docs…"><nav><a href="#start">Getting started</a><a href="#install">Installation</a><a href="#config">Configuration</a><a href="#api">API reference</a><a href="#faq">FAQ</a></nav></aside>
<main>
  <h1 id="start">Getting started</h1><p>Welcome to the {{{{NAME}}}} documentation. This guide gets you productive in five minutes.</p>
  <h2 id="install">Installation</h2><pre><code>npm install {{{{NAME}}}}</code></pre>
  <h2 id="config">Configuration</h2><p>Create a <code>config.json</code>:</p><pre><code>{{ "name": "{{{{NAME}}}}", "debug": false }}</code></pre>
  <h2 id="api">API reference</h2><table><tr><th>Method</th><th>Description</th></tr><tr><td><code>init()</code></td><td>Initialise the client</td></tr><tr><td><code>run(opts)</code></td><td>Execute with options</td></tr></table>
  <h2 id="faq">FAQ</h2><details><summary>Is it free?</summary><p>Yes, for personal use.</p></details><details><summary>Where do I report bugs?</summary><p>Open an issue on GitHub.</p></details>
</main>
<script>q.oninput=e=>{{const v=e.target.value.toLowerCase();document.querySelectorAll('main h1,main h2,main p,main pre,main details').forEach(el=>el.style.display=!v||el.textContent.toLowerCase().includes(v)?'':'none')}}</script>
</body>
</html>""",
  "style.css": """*{box-sizing:border-box;margin:0}body{font-family:system-ui,sans-serif;display:flex;min-height:100vh;color:#1e293b;line-height:1.7}
aside{width:260px;background:#f8fafc;border-right:1px solid #e2e8f0;padding:24px;position:sticky;top:0;height:100vh}.logo{font-weight:800;font-size:20px;color:#0f172a;text-decoration:none;display:block;margin-bottom:16px}.logo small{color:#7c5cff}
#q{width:100%;padding:8px 10px;border:1px solid #cbd5e1;border-radius:6px;margin-bottom:16px}nav a{display:block;padding:6px 10px;color:#475569;text-decoration:none;border-radius:6px}nav a:hover{background:#e2e8f0}
main{flex:1;padding:48px 6vw;max-width:820px}h1{font-size:2.4rem;margin-bottom:12px}h2{margin:40px 0 10px;padding-top:10px;border-top:1px solid #eee}pre{background:#0f172a;color:#e2e8f0;padding:16px;border-radius:8px;overflow:auto;margin:12px 0}code{font-family:ui-monospace,monospace;font-size:.92em}p code{background:#f1f5f9;padding:1px 6px;border-radius:4px}
table{border-collapse:collapse;width:100%;margin:12px 0}td,th{border:1px solid #e2e8f0;padding:10px;text-align:left}th{background:#f8fafc}details{margin:8px 0;padding:10px 14px;border:1px solid #e2e8f0;border-radius:8px}summary{cursor:pointer;font-weight:600}
@media(max-width:700px){body{flex-direction:column}aside{width:100%;height:auto;position:static}}"""}},

 "shop": {"name": "Store", "desc": "Product grid with cart (localStorage)", "icon": "🛍️", "cat": "Business", "kind": "static", "files": {
  "index.html": f"""<!DOCTYPE html>
<html lang="en">
<head>
{head("{{NAME}} — Shop", "Shop the {{NAME}} collection. Free shipping over $50.")}
</head>
<body>
<nav><b>{{{{NAME}}}}</b><button id="cartBtn">🛒 <span id="count">0</span></button></nav>
<header><h1>New season, new favourites</h1><p>Free shipping on orders over $50</p></header>
<main id="grid"></main>
<dialog id="cart"><h2>Your cart</h2><div id="items"></div><p id="total"></p><form action="/api/forms/{{{{NAME}}}}/order" method="post" id="orderForm"><input name="email" type="email" placeholder="Email for receipt" required><input type="hidden" name="items" id="itemsField"><button>Checkout</button></form><button onclick="cart.close()" class="ghost">Close</button></dialog>
<footer>© 2026 {{{{NAME}}}}</footer>
<script src="app.js"></script>
</body>
</html>""",
  "app.js": """const products=[{id:1,name:"Canvas Tote",price:24,img:"https://picsum.photos/seed/p1/500/500"},{id:2,name:"Ceramic Mug",price:18,img:"https://picsum.photos/seed/p2/500/500"},{id:3,name:"Linen Shirt",price:58,img:"https://picsum.photos/seed/p3/500/500"},{id:4,name:"Notebook Set",price:14,img:"https://picsum.photos/seed/p4/500/500"},{id:5,name:"Desk Lamp",price:72,img:"https://picsum.photos/seed/p5/500/500"},{id:6,name:"Wool Beanie",price:22,img:"https://picsum.photos/seed/p6/500/500"}];
let cart=JSON.parse(localStorage.cart||"[]");
grid.innerHTML=products.map(p=>`<article><img src="${p.img}" alt="${p.name}" loading="lazy"><h3>${p.name}</h3><p>$${p.price}</p><button onclick="add(${p.id})">Add to cart</button></article>`).join("");
function add(id){cart.push(id);save()}function rm(i){cart.splice(i,1);save()}
function save(){localStorage.cart=JSON.stringify(cart);count.textContent=cart.length;render()}
function render(){const it=cart.map(id=>products.find(p=>p.id===id));items.innerHTML=it.map((p,i)=>`<div>${p.name} — $${p.price} <a href="#" onclick="rm(${i});return false">✕</a></div>`).join("")||"<p>Cart is empty</p>";total.textContent="Total: $"+it.reduce((s,p)=>s+p.price,0);itemsField.value=it.map(p=>p.name).join(", ")}
cartBtn.onclick=()=>{render();document.getElementById("cart").showModal()};save();""",
  "style.css": """*{box-sizing:border-box;margin:0}body{font-family:system-ui,sans-serif;color:#111;line-height:1.5}
nav{display:flex;justify-content:space-between;align-items:center;padding:16px 5vw;border-bottom:1px solid #eee;position:sticky;top:0;background:#fff}nav b{font-size:20px}nav button{border:1px solid #ddd;background:#fff;padding:8px 14px;border-radius:20px;cursor:pointer}
header{text-align:center;padding:60px 5vw;background:#f5f5f4}header h1{font-size:2.6rem}
main{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:28px;padding:50px 5vw;max-width:1200px;margin:auto}article img{width:100%;aspect-ratio:1;object-fit:cover;border-radius:10px}article h3{margin:12px 0 2px;font-weight:600}article p{color:#666}article button{margin-top:8px;width:100%;padding:10px;background:#111;color:#fff;border:0;border-radius:8px;cursor:pointer}
dialog{border:0;border-radius:14px;padding:28px;width:min(420px,90vw)}dialog::backdrop{background:#0006}#items div{display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid #eee}#total{font-weight:700;margin:14px 0}dialog form{display:grid;gap:8px}dialog input{padding:10px;border:1px solid #ddd;border-radius:6px}dialog button{padding:10px;background:#111;color:#fff;border:0;border-radius:6px;cursor:pointer}.ghost{background:none!important;color:#666!important;margin-top:6px}
footer{text-align:center;padding:30px;color:#999;border-top:1px solid #eee}"""}},

 "flask": {"name": "Python (Flask) API", "desc": "Backend app with routes + KV storage", "icon": "🐍", "cat": "Apps", "kind": "python", "files": {
  "main.py": '''"""Forgevia Python app. Listens on $PORT. Uses Forgevia KV for storage."""
import os, json, urllib.request
from http.server import HTTPServer, BaseHTTPRequestHandler

PROJECT = os.environ.get("FORGEVIA_PROJECT", "{{NAME}}")
KV = "http://127.0.0.1:8000/api/kv/" + PROJECT

def kv_get(k, default=None):
    try: return json.load(urllib.request.urlopen(KV + "/" + k))
    except Exception: return default
def kv_set(k, v):
    req = urllib.request.Request(KV + "/" + k, data=json.dumps(v).encode(), method="PUT", headers={"Content-Type": "application/json"})
    urllib.request.urlopen(req)

class H(BaseHTTPRequestHandler):
    def send(self, body, code=200, ct="application/json"):
        b = body.encode() if isinstance(body, str) else json.dumps(body).encode()
        self.send_response(code); self.send_header("Content-Type", ct); self.send_header("Content-Length", len(b)); self.end_headers(); self.wfile.write(b)
    def do_GET(self):
        if self.path == "/": 
            visits = (kv_get("visits", 0) or 0) + 1; kv_set("visits", visits)
            self.send(f"<h1>🐍 {PROJECT} is live!</h1><p>Visit #{visits} (persisted in Forgevia KV)</p><p>Try <a href='/api/hello'>/api/hello</a> or <a href='/api/time'>/api/time</a></p>", ct="text/html")
        elif self.path == "/api/hello": self.send({"message": "Hello from Forgevia!", "project": PROJECT})
        elif self.path == "/api/time":
            import datetime; self.send({"now": datetime.datetime.utcnow().isoformat()})
        else: self.send({"error": "not found"}, 404)
    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0)); body = self.rfile.read(n).decode()
        self.send({"echo": body})

port = int(os.environ.get("PORT", 8080))
print(f"Serving on {port}", flush=True)
HTTPServer(("0.0.0.0", port), H).serve_forever()
''',
  "requirements.txt": "# add packages here, one per line\n",
  "README.md": "# {{NAME}}\n\nPython app hosted on Forgevia. Edit `main.py` and click **Publish** to deploy.\n\n- Listens on `$PORT`\n- Persist data with the KV API: `/api/kv/{{NAME}}/<key>`\n"}},

 "node": {"name": "Node.js API", "desc": "Express-free HTTP server with JSON routes", "icon": "🟢", "cat": "Apps", "kind": "node", "files": {
  "index.js": '''// Forgevia Node app — listens on process.env.PORT
const http = require("http");
const PROJECT = process.env.FORGEVIA_PROJECT || "{{NAME}}";
let hits = 0;
const routes = {
  "/": () => [`<h1>🟢 ${PROJECT} is live on Node ${process.version}</h1><p>Hits this session: ${++hits}</p><p>Try <a href="/api/hello">/api/hello</a></p>`, "text/html"],
  "/api/hello": () => [JSON.stringify({ message: "Hello from Forgevia!", project: PROJECT }), "application/json"],
  "/api/time": () => [JSON.stringify({ now: new Date().toISOString() }), "application/json"],
};
http.createServer((req, res) => {
  const r = routes[req.url.split("?")[0]];
  if (!r) { res.writeHead(404, {"Content-Type": "application/json"}); return res.end('{"error":"not found"}'); }
  const [body, ct] = r(); res.writeHead(200, { "Content-Type": ct }); res.end(body);
}).listen(process.env.PORT || 8080, () => console.log("listening", process.env.PORT));
''',
  "package.json": '{\n  "name": "{{NAME}}",\n  "version": "1.0.0",\n  "main": "index.js",\n  "scripts": { "start": "node index.js" }\n}\n'}},

 "coming-soon": {"name": "Coming Soon", "desc": "Countdown + email capture", "icon": "⏳", "cat": "Basic", "kind": "static", "files": {
  "index.html": f"""<!DOCTYPE html>
<html lang="en">
<head>
{head("{{NAME}} — Coming soon", "Something big is launching. Get notified.")}
</head>
<body>
<main>
  <h1>{{{{NAME}}}}</h1><p>We're launching soon. Be the first to know.</p>
  <div id="cd"></div>
  <form action="/api/forms/{{{{NAME}}}}/waitlist" method="post"><input name="email" type="email" placeholder="Enter your email" required><button>Notify me</button></form>
</main>
<script>const t=Date.now()+30*864e5;setInterval(()=>{{const d=t-Date.now();cd.innerHTML=[[864e5,'days'],[36e5,'hours'],[6e4,'min'],[1e3,'sec']].map(([m,l],i,a)=>`<div><b>${{Math.floor(d%(i?a[i-1][0]:1e18)/m)}}</b><small>${{l}}</small></div>`).join('')}},1000)</script>
</body>
</html>""",
  "style.css": """*{box-sizing:border-box;margin:0}body{font-family:system-ui,sans-serif;min-height:100vh;display:grid;place-items:center;background:linear-gradient(135deg,#0f172a,#312e81);color:#fff;text-align:center;padding:20px}
h1{font-size:clamp(2.5rem,8vw,5rem);letter-spacing:-.03em}p{color:#c7d2fe;margin:14px 0 36px;font-size:1.2rem}
#cd{display:flex;gap:18px;justify-content:center;margin-bottom:40px}#cd div{background:#ffffff14;padding:16px 20px;border-radius:12px;min-width:80px}#cd b{display:block;font-size:2.2rem}#cd small{color:#a5b4fc}
form{display:flex;gap:8px;justify-content:center;flex-wrap:wrap}input{padding:14px 18px;border-radius:10px;border:0;width:280px;font-size:16px}button{padding:14px 22px;border-radius:10px;border:0;background:#7c5cff;color:#fff;font-weight:600;cursor:pointer;font-size:16px}"""}},
}
