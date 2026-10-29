"""CuboAI workshop — intentionally vulnerable LOCAL training application.

Never deploy this application or expose it on a public network.
"""
import hashlib
import hmac
import json
import secrets
import sqlite3
from http import cookies
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parent
DB = ROOT / "demo.sqlite3"
SESSIONS = {}
HOST, PORT = "127.0.0.1", 8765


def db():
    connection = sqlite3.connect(DB)
    connection.row_factory = sqlite3.Row
    return connection


def reset_demo():
    with db() as conn:
        conn.executescript("""
        DROP TABLE IF EXISTS grades;
        DROP TABLE IF EXISTS users;
        CREATE TABLE users(id INTEGER PRIMARY KEY, name TEXT, username TEXT UNIQUE, password_hash TEXT, role TEXT);
        CREATE TABLE grades(id INTEGER PRIMARY KEY, student_id INTEGER, course TEXT, score INTEGER);
        """)
        users = [(1, "Alex Rivera", "alex", "student"), (2, "Sam López", "sam", "student"), (3, "Taylor Admin", "admin", "admin")]
        for uid, name, username, role in users:
            password = hashlib.sha256((username + "123").encode()).hexdigest()  # TRAINING ONLY: weak password scheme
            conn.execute("INSERT INTO users VALUES(?,?,?,?,?)", (uid, name, username, password, role))
        conn.executemany("INSERT INTO grades(student_id,course,score) VALUES(?,?,?)", [
            (1, "AI Foundations", 92), (1, "Python with AI", 84),
            (2, "AI Foundations", 70), (2, "Python with AI", 96)])
    SESSIONS.clear()


HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>CuboAI Portal — Workshop</title>
<style>
:root{--bg:#0a0a0a;--panel:#141414;--panel-2:#1a1a1a;--line:#2a2a2a;--text:#f5f5f5;--muted:#a1a1a1;--faint:#6b6b6b;--accent:#ff8a2a;--accent-2:#ffb36b;--ok:#86d9ab;--err:#ff8f7a;--radius:16px}
*{box-sizing:border-box}
body{margin:0;min-height:100vh;background:var(--bg);color:var(--text);font:15px/1.55 ui-sans-serif,-apple-system,"Segoe UI",Inter,Helvetica,Arial,sans-serif;-webkit-font-smoothing:antialiased}
h1,h2,h3{font-family:"Iowan Old Style","Palatino Linotype",Palatino,Georgia,serif;font-weight:500;letter-spacing:-.01em;margin:0}
h1{font-size:clamp(30px,3.6vw,44px);line-height:1.1}
h2{font-size:24px}
h3{font-size:19px}
p{color:var(--muted);margin:0}
label{display:block;font-size:13px;color:var(--muted);margin:16px 0 6px;letter-spacing:.02em}
input{width:100%;background:#0b0b0b;color:var(--text);border:1px solid var(--line);border-radius:10px;padding:12px 14px;font:inherit;transition:border-color .2s,box-shadow .2s}
input:focus{outline:none;border-color:var(--accent);box-shadow:0 0 0 3px #ff8a2a33}
button{font:inherit;font-weight:600;cursor:pointer;border-radius:10px;border:0;padding:11px 18px;transition:transform .15s,background .2s,color .2s,border-color .2s}
button:active{transform:translateY(1px)}
.btn{background:var(--accent);color:#111111}
.btn:hover{background:var(--accent-2)}
.btn-ghost{background:transparent;color:var(--text);border:1px solid var(--line)}
.btn-ghost:hover{border-color:var(--accent);color:var(--accent-2)}
:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.mono{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:14px}
.eyebrow{font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:var(--accent);margin:0 0 10px}
.grid-bg{background-image:linear-gradient(#ff8a2a0f 1px,transparent 1px),linear-gradient(90deg,#ff8a2a0f 1px,transparent 1px);background-size:36px 36px}
.logo{display:flex;align-items:center;gap:10px;font-weight:700;letter-spacing:.2px;font-size:16px}
.logo b{color:var(--accent)}
.mark{width:26px;height:26px;border-radius:8px;background:linear-gradient(135deg,#ffb36b,var(--accent) 45%,#e0490f);box-shadow:inset 0 0 0 1px #ffffff26;flex:none}
.badge{font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:var(--accent-2);border:1px solid #ff8a2a55;padding:5px 10px;border-radius:999px;align-self:flex-start}
.err{color:var(--err);min-height:1.4em;margin-top:12px;font-size:14px}
.ok{color:var(--ok)}
.hint{font-size:13px;margin-top:18px;line-height:1.8}
.hint code{color:var(--accent-2);font-family:ui-monospace,Menlo,monospace;font-size:12.5px}

/* Login */
#login{min-height:100vh;display:grid;place-items:center;padding:32px 20px}
.auth{width:min(980px,100%);display:grid;grid-template-columns:1.1fr .9fr;border:1px solid var(--line);border-radius:22px;overflow:hidden;background:var(--panel);box-shadow:0 30px 80px #0008;animation:rise .6s ease both}
.auth-hero{padding:48px;background:linear-gradient(160deg,#1c1c1c,#141414 62%);border-right:1px solid var(--line);display:flex;flex-direction:column;justify-content:space-between;gap:40px;position:relative}
.auth-hero .grid-bg{position:absolute;inset:0;mask-image:linear-gradient(#000,transparent 75%);-webkit-mask-image:linear-gradient(#000,transparent 75%);pointer-events:none}
.auth-hero > *{position:relative}
.auth-hero p.lead{max-width:36ch;margin-top:16px}
.auth-form{padding:48px}
.auth-form form{margin-top:22px}
.auth-form .btn{width:100%;margin-top:22px}

/* Shell */
#dashboard{display:none}
.shell{display:grid;grid-template-columns:248px minmax(0,1fr);min-height:100vh}
.side{position:sticky;top:0;height:100vh;padding:26px 18px;border-right:1px solid var(--line);background:#0f0f0f;display:flex;flex-direction:column;gap:28px}
.nav{display:flex;flex-direction:column;gap:3px}
.nav-label{font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:var(--faint);padding:0 12px;margin-top:8px}
.nav a{display:flex;align-items:center;gap:12px;padding:10px 12px;border-radius:10px;color:var(--muted);text-decoration:none;font-weight:500;transition:background .2s,color .2s;white-space:nowrap}
.nav a::before{content:"";width:6px;height:6px;border-radius:50%;background:currentColor;opacity:.45;flex:none}
.nav a:hover{background:var(--panel-2);color:var(--text)}
.nav a[aria-current="true"]{background:#222222;color:var(--accent-2);box-shadow:inset 2px 0 0 var(--accent)}
.nav a[aria-current="true"]::before{opacity:1;background:var(--accent)}
.side-foot{margin-top:auto;border-top:1px solid var(--line);padding-top:18px}
.me{font-size:14px;color:var(--text)}
.me small{display:block;color:var(--muted);font-size:12.5px}
.content{padding:40px clamp(20px,4vw,56px) 90px;max-width:1120px;width:100%;min-width:0}
.block{margin-top:44px;scroll-margin-top:24px;animation:rise .5s ease both}
.block:first-child{margin-top:0}
.topline{display:flex;justify-content:space-between;align-items:flex-end;gap:12px 24px;flex-wrap:wrap;margin-top:8px}
.topline p{max-width:40ch}
.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-top:28px}
.stat{background:var(--panel);border:1px solid var(--line);border-radius:var(--radius);padding:22px 22px 20px;transition:transform .25s,border-color .25s}
.stat:hover{transform:translateY(-2px);border-color:#ff8a2a66}
.stat .label{font-size:13px;color:var(--muted)}
.stat strong{display:block;font-family:"Iowan Old Style","Palatino Linotype",Georgia,serif;font-size:36px;font-weight:500;margin-top:6px;line-height:1}
.stat strong em{font-style:normal;font-size:.45em;color:var(--accent-2);margin-left:4px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:var(--radius);padding:26px}
.courses{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:14px;margin-top:18px}
.course{transition:transform .25s,border-color .25s}
.course:hover{transform:translateY(-2px);border-color:#ff8a2a66}
.bar{height:8px;background:#262626;border-radius:99px;overflow:hidden;margin:18px 0 10px}
.bar i{display:block;height:100%;border-radius:inherit;background:linear-gradient(90deg,#e0490f,var(--accent),var(--accent-2));animation:grow 1.1s cubic-bezier(.2,.7,.2,1) both}
.row-meta{display:flex;justify-content:space-between;font-size:13px;color:var(--muted)}
.row-meta span:last-child{color:var(--text)}
.table-wrap{overflow-x:auto;margin-top:14px}
table{width:100%;border-collapse:collapse;min-width:320px}
th,td{text-align:left;padding:14px 12px;border-bottom:1px solid var(--line)}
th{font-size:12px;letter-spacing:.1em;text-transform:uppercase;color:var(--faint);font-weight:600}
td{color:var(--text)}
tbody tr{transition:background .2s}
tbody tr:hover{background:var(--panel-2)}
.row2{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:14px;align-items:end;margin-top:6px}
.row3{display:grid;grid-template-columns:1fr 1fr auto;gap:14px;align-items:end;margin-top:6px}
.row3 button,.row2 button{white-space:nowrap}
.admin{border:1px dashed #ff8a2a80;background:linear-gradient(180deg,#181818,var(--panel))}
#adminPanel{display:none}
#navAdmin{display:none}
.msg{min-height:1.4em;margin-top:12px;font-size:14px}

@keyframes rise{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:none}}
@keyframes grow{from{width:0}}

@media (max-width:900px){
 .shell{grid-template-columns:minmax(0,1fr)}
 .side{position:sticky;top:0;z-index:5;height:auto;flex-direction:row;align-items:center;gap:14px;padding:12px 16px;border-right:0;border-bottom:1px solid var(--line);background:#0f0f0ff2;backdrop-filter:blur(10px);-webkit-backdrop-filter:blur(10px)}
 .nav{flex-direction:row;overflow-x:auto;min-width:0;flex:1;gap:2px;scrollbar-width:none}
 .nav-label{display:none}
 .side-foot{border:0;padding:0;margin:0;flex:none;display:flex;align-items:center;gap:12px}
 .side-foot .me small{display:none}
 .side-foot button{padding:8px 12px;font-size:14px}
 .auth{grid-template-columns:1fr}
 .auth-hero{border-right:0;border-bottom:1px solid var(--line);padding:32px}
 .auth-form{padding:32px}
 .stats{grid-template-columns:1fr 1fr}
 .stats .stat:last-child{grid-column:1/-1}
}
@media (max-width:620px){
 .stats{grid-template-columns:1fr}
 .stats .stat:last-child{grid-column:auto}
 .row2,.row3{grid-template-columns:1fr}
 .row2 button,.row3 button{width:100%}
 .card{padding:20px}
 .side-foot .me{display:none}
}
@media (prefers-reduced-motion:reduce){*,*::before,*::after{animation:none!important;transition:none!important;scroll-behavior:auto!important}}
</style>
</head>
<body>
<section id="login">
 <div class="auth">
  <div class="auth-hero">
   <div class="grid-bg" aria-hidden="true"></div>
   <div class="logo"><span class="mark" aria-hidden="true"></span><span>Cubo<b>AI</b> Student Portal</span></div>
   <div>
    <p class="eyebrow">Beyond Vibe Coding</p>
    <h1>Your learning,<br>in one place.</h1>
    <p class="lead">Follow your courses, review your grades and keep your profile up to date.</p>
   </div>
   <span class="badge">Local training demo</span>
  </div>
  <div class="auth-form">
   <p class="eyebrow">Welcome back</p>
   <h2>Sign in</h2>
   <form onsubmit="event.preventDefault();login()">
    <label for="username">Username</label>
    <input id="username" name="username" autocomplete="username" value="alex">
    <label for="password">Password</label>
    <input id="password" name="password" type="password" autocomplete="current-password" value="alex123">
    <button class="btn" type="submit">Sign in</button>
   </form>
   <p id="loginMessage" class="err" role="alert"></p>
   <p class="hint">Demo accounts: <code>alex / alex123</code> · <code>sam / sam123</code> · <code>admin / admin123</code></p>
  </div>
 </div>
</section>

<section id="dashboard">
 <div class="shell">
  <aside class="side" aria-label="Student navigation">
   <div class="logo"><span class="mark" aria-hidden="true"></span><span>Cubo<b>AI</b></span></div>
   <nav class="nav" aria-label="Sections">
    <span class="nav-label">Learning</span>
    <a href="#overview">Overview</a>
    <a href="#courses">Courses</a>
    <a href="#transcript">Grades</a>
    <span class="nav-label">Account</span>
    <a href="#profile">Profile</a>
    <a href="#adminPanel" id="navAdmin">Instructor tools</a>
   </nav>
   <div class="side-foot">
    <div class="me"><span id="sideName">Student</span><small>Signed in</small></div>
    <button class="btn-ghost" style="width:100%;margin-top:12px" onclick="logout()">Sign out</button>
   </div>
  </aside>

  <main class="content">
   <section id="overview" class="block">
    <p class="eyebrow">Student dashboard</p>
    <div class="topline">
     <h1 id="welcome">Hello!</h1>
     <p>Your AI learning journey at a glance.</p>
    </div>
    <div class="stats">
     <div class="stat"><span class="label">Enrolled courses</span><strong>2</strong></div>
     <div class="stat"><span class="label">Completed lessons</span><strong>14</strong></div>
     <div class="stat"><span class="label">Learning streak</span><strong>7<em>days</em></strong></div>
    </div>
   </section>

   <section id="courses" class="block">
    <p class="eyebrow">Curriculum</p>
    <h2>Courses</h2>
    <p style="margin-top:6px">Progress bars reflect your current score in each course.</p>
    <div id="courseCards" class="courses"></div>
   </section>

   <section id="transcript" class="block card">
    <p class="eyebrow">Transcript</p>
    <h2>My grades</h2>
    <div class="table-wrap">
     <table>
      <thead><tr><th scope="col">Course</th><th scope="col">Score</th></tr></thead>
      <tbody id="grades"></tbody>
     </table>
    </div>
   </section>

   <section id="profile" class="block card">
    <p class="eyebrow">Account</p>
    <h2>Profile</h2>
    <p style="margin-top:6px">Manage your profile preferences.</p>
    <form class="row2" onsubmit="event.preventDefault();saveProfile()">
     <div>
      <label for="displayName">Display name</label>
      <input id="displayName" name="displayName" autocomplete="name">
     </div>
     <button class="btn" type="submit">Save changes</button>
    </form>
    <p id="saveMessage" class="msg" role="status"></p>
   </section>

   <section id="adminPanel" class="block card admin">
    <p class="eyebrow">Staff only</p>
    <h2>Instructor tools</h2>
    <p style="margin-top:6px">Update a student's score</p>
    <div class="row3">
     <div>
      <label for="gradeId">Grade record ID</label>
      <input id="gradeId" type="number" value="1">
     </div>
     <div>
      <label for="newScore">New score</label>
      <input id="newScore" type="number" value="100">
     </div>
     <button class="btn" type="button" onclick="updateGrade()">Update grade</button>
    </div>
    <p id="adminMessage" class="msg" role="status"></p>
   </section>
  </main>
 </div>
</section>

<script>
let me=null;
async function api(path,options={}) {const r=await fetch(path,{credentials:'same-origin',...options});const d=await r.json();if(!r.ok)throw Error(d.error||'Request failed');return d}
async function login(){try{me=await api('/api/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:username.value,password:password.value})});loginMessage.textContent='';show()}catch(e){loginMessage.textContent=e.message}}
function escapeText(s){return String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
function courseCard(x){const s=Number(x.score);return `<article class="card course"><p class="eyebrow">Course</p><h3>${escapeText(x.course)}</h3><div class="bar" role="progressbar" aria-label="${escapeText(x.course)} progress" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${s}"><i style="width:${s}%"></i></div><div class="row-meta"><span>Progress</span><span class="mono">${s}%</span></div></article>`}
async function show(){document.getElementById('login').style.display='none';dashboard.style.display='block';welcome.textContent='Hello, '+me.name;sideName.textContent=me.name;displayName.value=me.name;adminPanel.style.display=me.role==='admin'?'block':'none';navAdmin.style.display=me.role==='admin'?'block':'none';let rows=await api('/api/grades?student_id='+me.id);grades.innerHTML=rows.map(x=>`<tr><td>${escapeText(x.course)}</td><td class="mono">${Number(x.score)}%</td></tr>`).join('');courseCards.innerHTML=rows.map(courseCard).join('')}
async function saveProfile(){// WORKSHOP BUG: a convincing button with no persistence
 saveMessage.textContent='✓ Changes saved successfully';saveMessage.className='msg ok'}
async function updateGrade(){try{await api('/api/grades/update',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({grade_id:Number(gradeId.value),score:Number(newScore.value)})});adminMessage.textContent='Grade updated';adminMessage.className='msg ok'}catch(e){adminMessage.textContent=e.message;adminMessage.className='msg err'}}
async function logout(){await api('/api/logout',{method:'POST'});me=null;dashboard.style.display='none';document.getElementById('login').style.display='block'}
const links=[...document.querySelectorAll('.nav a')];
const spy=new IntersectionObserver(entries=>entries.forEach(e=>{if(e.isIntersecting)links.forEach(a=>a.setAttribute('aria-current',String(a.getAttribute('href')==='#'+e.target.id)))}),{rootMargin:'-35% 0px -55% 0px'});
document.querySelectorAll('#dashboard section').forEach(s=>spy.observe(s));
</script>
</body>
</html>"""


class Handler(BaseHTTPRequestHandler):
    def response(self, status, content, content_type="application/json", cookie=None):
        raw = content.encode() if isinstance(content, str) else content
        self.send_response(status)
        self.send_header("Content-Type", content_type + "; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        if cookie:
            self.send_header("Set-Cookie", cookie)
        self.end_headers()
        self.wfile.write(raw)

    def send_json(self, status, data, cookie=None):
        self.response(status, json.dumps(data), cookie=cookie)

    def user(self):
        parsed = cookies.SimpleCookie()
        try:
            parsed.load(self.headers.get("Cookie", ""))
        except cookies.CookieError:
            return None
        token = parsed.get("sid")
        uid = SESSIONS.get(token.value) if token else None
        if uid is None:
            return None
        with db() as conn:
            row = conn.execute("SELECT id,name,role FROM users WHERE id=?", (uid,)).fetchone()
            return dict(row) if row else None

    def read_body(self):
        length = int(self.headers.get("Content-Length", "0"))
        if length > 10000:
            raise ValueError("Payload too large")
        return json.loads(self.rfile.read(length))

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/":
            return self.response(200, HTML, "text/html")
        user = self.user()
        if not user:
            return self.send_json(401, {"error": "Sign in first"})
        if parsed.path == "/api/grades":
            # WORKSHOP BUG 1: IDOR / broken object-level authorization
            student_id = parse_qs(parsed.query).get("student_id", [str(user["id"])])[0]
            try:
                with db() as conn:
                    rows = conn.execute("SELECT id,student_id,course,score FROM grades WHERE student_id=?", (int(student_id),)).fetchall()
                    return self.send_json(200, [dict(row) for row in rows])
            except ValueError:
                return self.send_json(400, {"error": "Invalid student ID"})
        self.send_json(404, {"error": "Not found"})

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/logout":
            cookie = cookies.SimpleCookie()
            cookie.load(self.headers.get("Cookie", ""))
            token = cookie.get("sid")
            if token:
                SESSIONS.pop(token.value, None)
            return self.send_json(200, {"ok": True}, "sid=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0")
        try:
            payload = self.read_body()
        except (ValueError, json.JSONDecodeError):
            return self.send_json(400, {"error": "Invalid JSON"})
        if parsed.path == "/api/login":
            username, password = str(payload.get("username", "")), str(payload.get("password", ""))
            hashed = hashlib.sha256(password.encode()).hexdigest()
            with db() as conn:
                row = conn.execute("SELECT id,name,role,password_hash FROM users WHERE username=?", (username,)).fetchone()
            if not row or not hmac.compare_digest(row["password_hash"], hashed):
                return self.send_json(401, {"error": "Invalid credentials"})
            token = secrets.token_urlsafe(24)
            SESSIONS[token] = row["id"]
            return self.send_json(200, {"id": row["id"], "name": row["name"], "role": row["role"]}, f"sid={token}; HttpOnly; SameSite=Strict; Path=/")
        user = self.user()
        if not user:
            return self.send_json(401, {"error": "Sign in first"})
        if parsed.path == "/api/grades/update":
            # WORKSHOP BUG 2: UI hides admin tool, API doesn't enforce admin role
            try:
                grade_id, score = int(payload["grade_id"]), int(payload["score"])
            except (ValueError, TypeError, KeyError):
                return self.send_json(400, {"error": "Invalid input"})
            # WORKSHOP BUG 3: invalid scores (negative, >100) are accepted
            with db() as conn:
                result = conn.execute("UPDATE grades SET score=? WHERE id=?", (score, grade_id))
            return self.send_json(200, {"updated": result.rowcount})
        self.send_json(404, {"error": "Not found"})


if __name__ == "__main__":
    import sys
    if "--reset" in sys.argv or not DB.exists():
        reset_demo()
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"CuboAI workshop running at http://{HOST}:{PORT}")
    print("LOCAL ONLY — never deploy this intentionally vulnerable demo.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped")
    finally:
        server.server_close()
