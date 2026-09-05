"""Seed Forgevia with realistic demo users, projects, traffic, forms & monitors.
Run:  python3 seed.py          (safe to re-run; skips existing users)
"""
import random, time, sqlite3, shutil, json, hashlib, secrets
from pathlib import Path
from server import db, hashpw, PROJECTS, SITES, TEMPLATES, publish as _publish, INJECT
from datetime import datetime

random.seed(7)
PEOPLE = [
 ("Ayesha Khan","ayesha@example.com","landing","ayesha-labs"),("Bilal Ahmed","bilal@example.com","portfolio","bilal-design"),
 ("Sara Malik","sara@example.com","blog","sara-writes"),("Hamza Iqbal","hamza@example.com","shop","hamza-store"),
 ("Zainab Raza","zainab@example.com","docs","zainab-docs"),("Omar Farooq","omar@example.com","restaurant","omar-kitchen"),
 ("Fatima Noor","fatima@example.com","landing","fatima-app"),("Ali Hassan","ali@example.com","flask","ali-api"),
 ("Maryam Shah","maryam@example.com","coming-soon","maryam-launch"),("Usman Tariq","usman@example.com","node","usman-service"),
 ("Hira Baig","hira@example.com","portfolio","hira-photo"),("Daniyal Butt","daniyal@example.com","blog","daniyal-dev"),
 ("Noor Fatima","noor@example.com","shop","noor-boutique"),("Saad Qureshi","saad@example.com","landing","saad-saas"),
 ("Laiba Mir","laiba@example.com","docs","laiba-guides"),("Taha Siddiqui","taha@example.com","restaurant","taha-cafe"),
 ("Rabia Aslam","rabia@example.com","blog","rabia-notes"),("Ahmed Raza","ahmed@example.com","portfolio","ahmed-folio"),
 ("Mahnoor Ali","mahnoor@example.com","landing","mahnoor-studio"),("Zayan Sheikh","zayan@example.com","coming-soon","zayan-soon"),
]
REFS = ["https://google.com/","https://twitter.com/","https://linkedin.com/","https://news.ycombinator.com/","","","https://facebook.com/","https://reddit.com/","https://producthunt.com/","https://bing.com/"]
UAS = ["Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/128 Safari/537.36","Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) Mobile/15E148 Safari/604.1","Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) Safari/605.1.15","Mozilla/5.0 (Linux; Android 14) Chrome/128 Mobile Safari/537.36","Mozilla/5.0 (Windows NT 10.0) Firefox/129.0","Mozilla/5.0 (iPad; CPU OS 17_0) Safari/604.1","Mozilla/5.0 (X11; Linux x86_64) Edg/128"]
PATHS = ["/","/","/","/","/about.html","/post-1.html","/#pricing","/#features","/contact"]

def main():
    made = 0
    with db() as c:
        for name, email, tpl, proj in PEOPLE:
            if c.execute("SELECT 1 FROM users WHERE email=?", (email,)).fetchone(): continue
            created = time.time() - random.randint(5, 120) * 86400
            uid = c.execute("INSERT INTO users(email,name,pw,plan,created) VALUES(?,?,?,?,?)", (email, name, hashpw("demo123"), random.choice(["free","free","pro","pro","team"]), created)).lastrowid
            d = PROJECTS / proj
            if not d.exists():
                d.mkdir()
                for f, content in TEMPLATES[tpl]["files"].items():
                    fp = d / f; fp.parent.mkdir(parents=True, exist_ok=True); fp.write_text(content.replace("{{NAME}}", proj))
            pub = created + random.randint(1, 3) * 86400
            c.execute("INSERT OR IGNORE INTO projects(uid,name,kind,created,template,published,seo_title,seo_desc) VALUES(?,?,?,?,?,?,?,?)",
                      (uid, proj, TEMPLATES[tpl].get("kind","static"), created, tpl, pub, f"{name.split()[0]}'s {TEMPLATES[tpl]['name']}", TEMPLATES[tpl]["desc"]))
            # publish static copy
            if TEMPLATES[tpl].get("kind","static") == "static":
                dst = SITES / proj
                if dst.exists(): shutil.rmtree(dst)
                shutil.copytree(d, dst)
                for f in dst.rglob("*.html"): f.write_text(f.read_text().replace("</body>", (INJECT % proj) + "</body>"))
            # traffic: popularity curve
            weight = random.choice([30, 80, 150, 300, 600, 1200, 2500, 4000])
            for _ in range(weight):
                ts = pub + random.random() * (time.time() - pub)
                ip = f"{random.randint(1,223)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"
                c.execute("INSERT INTO hits(project,path,ref,ua,ip,ts) VALUES(?,?,?,?,?,?)", (proj, random.choice(PATHS), random.choice(REFS), random.choice(UAS), ip, ts))
            # forms
            for _ in range(random.randint(0, 12)):
                c.execute("INSERT INTO forms(project,form,data,ts) VALUES(?,?,?,?)", (proj, random.choice(["contact","signup","waitlist"]), json.dumps({"email": f"visitor{random.randint(1,999)}@mail.com", "message": random.choice(["Love this!","How much for a team plan?","Can I get a demo?","Great work"])}), pub + random.random() * (time.time() - pub)))
            # versions
            for i in range(random.randint(1, 6)):
                c.execute("INSERT INTO versions(project,label,created,path) VALUES(?,?,?,?)", (proj, "publish", pub + i * 86400 * 3, str(d)))
            # activity
            for act, det in (("created", f"from template {tpl}"), ("published", "1 pages"), ("seo audit", f"/sites/{proj}/")):
                c.execute("INSERT INTO activity(uid,project,action,detail,ts) VALUES(?,?,?,?,?)", (uid, proj, act, det, pub + random.random() * 86400))
            # monitors for some
            if random.random() < 0.5:
                up = random.randint(200, 800); down = random.randint(0, 5)
                mid = c.execute("INSERT INTO monitors(uid,url,interval,last_status,last_ms,last_check,up_count,down_count,created) VALUES(?,?,?,?,?,?,?,?,?)", (uid, f"http://localhost:8000/sites/{proj}/", 300, 200, random.randint(40, 400), time.time() - 120, up, down, pub)).lastrowid
                for i in range(60):
                    c.execute("INSERT INTO monitor_log(mid,status,ms,ts) VALUES(?,?,?,?)", (mid, 200 if random.random() > 0.03 else 503, random.randint(30, 600), time.time() - (60 - i) * 300))
            made += 1
    print(f"Seeded {made} users/projects. Login for any: <email> / demo123")

if __name__ == "__main__": main()
