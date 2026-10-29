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


HTML = """<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>CuboAI Portal — Workshop</title><style>
*{box-sizing:border-box}body{margin:0;background:#0a1221;color:#ecf5ff;font:16px system-ui,Segoe UI,Arial}header{display:flex;justify-content:space-between;align-items:center;padding:22px max(22px,calc((100vw - 920px)/2));border-bottom:1px solid #26364d;background:#111e31}.brand{font-weight:800;letter-spacing:.3px}.brand span{color:#66e2b0}.badge{font-size:12px;background:#244c42;color:#80f5c5;padding:5px 10px;border-radius:20px}main{max-width:920px;margin:42px auto;padding:0 22px}h1{font-size:35px;margin-bottom:8px}p{color:#9cb0c7}.panel{border:1px solid #29405b;border-radius:18px;background:#142238;padding:25px;margin:22px 0;box-shadow:0 16px 36px #0002}input{background:#0b1729;color:white;border:1px solid #3a5572;padding:12px;border-radius:8px;width:100%;margin:6px 0 14px}button{background:#61e5af;color:#092319;border:0;border-radius:9px;padding:11px 18px;font-weight:700;cursor:pointer}button.secondary{background:#293b55;color:#fff;margin-left:8px}.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:13px}.stat{background:#1a3150;padding:20px;border-radius:12px}.stat strong{display:block;font-size:27px;margin:5px 0}table{width:100%;border-collapse:collapse}th,td{text-align:left;padding:14px;border-bottom:1px solid #2d4160}th{color:#91abc3}small{color:#9db1c8}.err{color:#ff9b9b}.ok{color:#67f2b4}#dashboard,#adminPanel{display:none}@media(max-width:620px){.grid{grid-template-columns:1fr}h1{font-size:28px}}
</style><header><div class="brand">◈ Cubo<span>AI</span> / Student Portal</div><span class="badge">LOCAL TRAINING DEMO</span></header>
<main><section id="login"><h1>Welcome back 👋</h1><p>Your personalized learning space.</p><div class="panel" style="max-width:450px"><h2>Sign in</h2><label>Username</label><input id="username" value="alex"><label>Password</label><input id="password" type="password" value="alex123"><button onclick="login()">Sign in</button><p id="loginMessage" class="err"></p><small>Demo accounts: alex/alex123 · sam/sam123 · admin/admin123</small></div></section>
<section id="dashboard"><h1 id="welcome">Hello!</h1><p>Your AI learning journey at a glance.</p><div class="grid"><div class="stat">Enrolled courses<strong>2</strong></div><div class="stat">Completed lessons<strong>14</strong></div><div class="stat">Learning streak<strong>7 days</strong></div></div><div class="panel"><h2>My grades</h2><table><thead><tr><th>Course</th><th>Score</th></tr></thead><tbody id="grades"></tbody></table></div><div class="panel"><h2>Profile</h2><label>Display name</label><input id="displayName"><button onclick="saveProfile()">Save changes</button><p id="saveMessage"></p><small>Manage your profile preferences.</small></div><div id="adminPanel" class="panel"><h2>Instructor tools</h2><p>Update a student's score</p><label>Grade record ID</label><input id="gradeId" type="number" value="1"><label>New score</label><input id="newScore" type="number" value="100"><button onclick="updateGrade()">Update grade</button><p id="adminMessage"></p></div><button class="secondary" onclick="logout()">Sign out</button></section></main>
<script>
let me=null;
async function api(path,options={}) {const r=await fetch(path,{credentials:'same-origin',...options});const d=await r.json();if(!r.ok)throw Error(d.error||'Request failed');return d}
async function login(){try{me=await api('/api/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:username.value,password:password.value})});loginMessage.textContent='';show()}catch(e){loginMessage.textContent=e.message}}
async function show(){document.getElementById('login').style.display='none';dashboard.style.display='block';welcome.textContent='Hello, '+me.name+' 👋';displayName.value=me.name;adminPanel.style.display=me.role==='admin'?'block':'none';let rows=await api('/api/grades?student_id='+me.id);grades.innerHTML=rows.map(x=>`<tr><td>${escapeText(x.course)}</td><td>${x.score}%</td></tr>`).join('')}
function escapeText(s){return String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
async function saveProfile(){// WORKSHOP BUG: a convincing button with no persistence
 saveMessage.textContent='✓ Changes saved successfully';saveMessage.className='ok'}
async function updateGrade(){try{await api('/api/grades/update',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({grade_id:Number(gradeId.value),score:Number(newScore.value)})});adminMessage.textContent='Grade updated'}catch(e){adminMessage.textContent=e.message}}
async function logout(){await api('/api/logout',{method:'POST'});me=null;dashboard.style.display='none';document.getElementById('login').style.display='block'}
</script></html>"""


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
