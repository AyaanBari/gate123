"""
SQLite Database Manager for GATE CS CBT System
Handles users, auth, access codes, test attempts, analytics, admin, and full telemetry.
"""

import sqlite3
import os
import hashlib
import json
import time
from datetime import datetime, timezone

DB_PATH = os.environ.get(
    "EXAM_DB_PATH",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "exam_system.db"),
)
DEFAULT_ACCESS_CODE = "12G3A4T8WE"
ADMIN_EMAIL = "musicfusion123456@gmail.com"


def utc_timestamp():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def hash_pw(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_db()
    c = conn.cursor()

    # Core tables
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'student',
        has_access_code INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL,
        last_login TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS access_codes (
        code TEXT PRIMARY KEY,
        is_active INTEGER NOT NULL DEFAULT 1,
        created_at TEXT NOT NULL
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS test_attempts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT NOT NULL,
        test_id TEXT NOT NULL,
        test_title TEXT NOT NULL,
        subject TEXT NOT NULL,
        score REAL NOT NULL,
        total_marks REAL NOT NULL,
        accuracy REAL NOT NULL,
        time_taken_seconds INTEGER NOT NULL,
        attempted_date TEXT NOT NULL,
        responses_json TEXT,
        FOREIGN KEY (user_email) REFERENCES users (email)
    )''')

    # Telemetry tables
    c.execute('''CREATE TABLE IF NOT EXISTS login_events (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email  TEXT NOT NULL,
        event_type  TEXT NOT NULL,
        ip_address  TEXT,
        user_agent  TEXT,
        screen_res  TEXT,
        platform    TEXT,
        language    TEXT,
        timezone    TEXT,
        timestamp   TEXT NOT NULL
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS session_events (
        id               INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email       TEXT,
        session_id       TEXT NOT NULL,
        event_type       TEXT NOT NULL,
        duration_seconds INTEGER,
        pages_visited    TEXT,
        series_browsed   TEXT,
        ip_address       TEXT,
        timestamp        TEXT NOT NULL
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS question_telemetry (
        id             INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email     TEXT,
        test_id        TEXT NOT NULL,
        test_title     TEXT,
        question_index INTEGER NOT NULL,
        subject        TEXT,
        question_type  TEXT,
        marks          REAL,
        time_spent_sec INTEGER,
        answer_changes INTEGER DEFAULT 0,
        marked_review  INTEGER DEFAULT 0,
        was_revisited  INTEGER DEFAULT 0,
        final_answer   TEXT,
        is_correct     INTEGER DEFAULT 0,
        marks_awarded  REAL DEFAULT 0,
        is_attempted   INTEGER DEFAULT 0,
        test_mode      TEXT,
        recorded_at    TEXT NOT NULL
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS behavior_events (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email  TEXT,
        session_id  TEXT,
        event_type  TEXT NOT NULL,
        event_data  TEXT,
        ip_address  TEXT,
        timestamp   TEXT NOT NULL
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS site_access_events (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        ip_address   TEXT NOT NULL,
        request_path TEXT NOT NULL,
        user_agent   TEXT,
        timestamp    TEXT NOT NULL
    )''')

    for table in ("question_telemetry", "behavior_events"):
        columns = {row[1] for row in c.execute(f"PRAGMA table_info({table})")}
        if "ip_address" not in columns:
            c.execute(f"ALTER TABLE {table} ADD COLUMN ip_address TEXT")
    c.execute("CREATE INDEX IF NOT EXISTS idx_site_access_timestamp ON site_access_events(timestamp DESC)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_site_access_ip ON site_access_events(ip_address)")

    # Seed data
    c.execute('INSERT OR IGNORE INTO access_codes (code, is_active, created_at) VALUES (?, 1, ?)',
              (DEFAULT_ACCESS_CODE, utc_timestamp()))

    c.execute('SELECT id FROM users WHERE email = ?', (ADMIN_EMAIL,))
    if not c.fetchone():
        c.execute('''INSERT INTO users (email, name, password_hash, role, has_access_code, created_at)
                     VALUES (?, 'Administrator', ?, 'admin', 1, ?)''',
                  (ADMIN_EMAIL, hash_pw("admin123"), utc_timestamp()))

    conn.commit()
    conn.close()
    print("Database initialized at", DB_PATH)


# ─── Auth ─────────────────────────────────────────────────────────────────────

def register_user(email, name, password):
    email = email.lower().strip()
    conn = get_db(); c = conn.cursor()
    c.execute('SELECT id FROM users WHERE email = ?', (email,))
    if c.fetchone():
        conn.close(); return False, "User with this email already exists"
    role = 'admin' if email == ADMIN_EMAIL else 'student'
    has_access = 1 if email == ADMIN_EMAIL else 0
    now = utc_timestamp()
    c.execute('''INSERT INTO users (email, name, password_hash, role, has_access_code, created_at, last_login)
                 VALUES (?,?,?,?,?,?,?)''',
              (email, name.strip(), hash_pw(password), role, has_access, now, now))
    conn.commit(); conn.close()
    return True, {"email": email, "name": name, "role": role, "has_access_code": has_access}


def login_user(email, password):
    email = email.lower().strip()
    conn = get_db(); c = conn.cursor()
    c.execute('SELECT * FROM users WHERE email = ?', (email,))
    user = c.fetchone()
    if not user:
        conn.close(); return False, "Account not found with this email"
    if user['password_hash'] != hash_pw(password):
        conn.close(); return False, "Invalid password"
    now = utc_timestamp()
    c.execute('UPDATE users SET last_login = ? WHERE email = ?', (now, email))
    conn.commit()
    data = {"id": user["id"], "email": user["email"], "name": user["name"],
            "role": user["role"], "has_access_code": bool(user["has_access_code"])}
    conn.close(); return True, data


def verify_and_unlock_code(email, code):
    email = email.lower().strip(); code = code.strip().upper()
    conn = get_db(); c = conn.cursor()
    c.execute('SELECT id FROM users WHERE email = ?', (email,))
    if not c.fetchone():
        conn.close(); return False, "You must be logged in to redeem an access code."
    c.execute('SELECT * FROM access_codes WHERE code = ? AND is_active = 1', (code,))
    if not c.fetchone():
        conn.close(); return False, "Invalid or expired access code. Contact musicfusion123456@gmail.com"
    c.execute('UPDATE users SET has_access_code = 1 WHERE email = ?', (email,))
    conn.commit(); conn.close()
    return True, "Full access successfully unlocked!"


# ─── Test Attempts ────────────────────────────────────────────────────────────

def save_attempt(email, attempt_data):
    email = email.lower().strip()
    conn = get_db(); c = conn.cursor()
    now = utc_timestamp()
    c.execute('''INSERT INTO test_attempts
        (user_email,test_id,test_title,subject,score,total_marks,accuracy,time_taken_seconds,attempted_date,responses_json)
        VALUES (?,?,?,?,?,?,?,?,?,?)''',
        (email, attempt_data.get('testId',''), attempt_data.get('testTitle',''),
         attempt_data.get('subject','General'), float(attempt_data.get('score',0)),
         float(attempt_data.get('totalMarks',100)), float(attempt_data.get('accuracy',0)),
         int(attempt_data.get('timeSpent',0)), now,
         json.dumps(attempt_data.get('responses',{}))))
    conn.commit(); conn.close()
    return True, "Saved"


# ─── Analytics ────────────────────────────────────────────────────────────────

def get_user_analytics(email):
    email = email.lower().strip()
    conn = get_db(); c = conn.cursor()
    c.execute('SELECT * FROM test_attempts WHERE user_email = ? ORDER BY id DESC', (email,))
    attempts = [dict(r) for r in c.fetchall()]
    n = len(attempts)
    if n == 0:
        conn.close()
        return {"totalTests": 0, "avgScorePct": 0, "avgAccuracy": 0,
                "totalTimeHours": 0, "subjectMastery": {}, "recentAttempts": []}
    avg_score_pct = round(sum((a['score']/(a['total_marks'] or 1))*100 for a in attempts)/n, 1)
    avg_accuracy  = round(sum(a['accuracy'] for a in attempts)/n, 1)
    total_mins    = sum(a['time_taken_seconds'] for a in attempts)/60.0
    subj_map = {}
    for a in attempts:
        s = a['subject']
        if s not in subj_map:
            subj_map[s] = {"tests":0,"totalScore":0,"totalMarks":0,"totalAccuracy":0}
        subj_map[s]["tests"]       += 1
        subj_map[s]["totalScore"]  += a["score"]
        subj_map[s]["totalMarks"]  += a["total_marks"]
        subj_map[s]["totalAccuracy"] += a["accuracy"]
    mastery = {}
    for s, d in subj_map.items():
        pct = (d["totalScore"]/(d["totalMarks"] or 1))*100
        acc = d["totalAccuracy"]/d["tests"]
        mastery[s] = {"testsCount": d["tests"], "scorePct": round(pct,1), "accuracy": round(acc,1),
                      "status": "Strong" if acc>=70 else ("Average" if acc>=45 else "Needs Work")}
    conn.close()
    return {"totalTests": n, "avgScorePct": avg_score_pct, "avgAccuracy": avg_accuracy,
            "totalTimeMinutes": round(total_mins,1), "subjectMastery": mastery,
            "recentAttempts": attempts[:15]}


def get_admin_data():
    conn = get_db(); c = conn.cursor()
    c.execute('SELECT COUNT(*) as n FROM users');        total_users    = c.fetchone()['n']
    c.execute('SELECT COUNT(*) as n FROM users WHERE has_access_code=1'); unlocked = c.fetchone()['n']
    c.execute('SELECT COUNT(*) as n, AVG(accuracy) as aa FROM test_attempts')
    row = c.fetchone(); total_attempts = row['n']; global_acc = round(row['aa'] or 0, 1)
    c.execute('''SELECT u.id,u.email,u.name,u.role,u.has_access_code,u.created_at,u.last_login,
                        COUNT(t.id) as tests_taken, AVG(t.score) as avg_score, AVG(t.accuracy) as avg_accuracy
                 FROM users u LEFT JOIN test_attempts t ON u.email=t.user_email
                 GROUP BY u.email ORDER BY u.id DESC''')
    users = [{"id":r["id"],"email":r["email"],"name":r["name"],"role":r["role"],
              "has_access": bool(r["has_access_code"]),
              "created_at": r["created_at"], "last_login": r["last_login"] or "Never",
              "tests_taken": r["tests_taken"],
              "avg_score": round(r["avg_score"] or 0, 1),
              "avg_accuracy": round(r["avg_accuracy"] or 0, 1)} for r in c.fetchall()]
    conn.close()
    return {"totalUsers": total_users, "unlockedUsers": unlocked,
            "totalAttempts": total_attempts, "globalAccuracy": global_acc,
            "defaultAccessCode": DEFAULT_ACCESS_CODE, "adminEmail": ADMIN_EMAIL, "users": users}


def toggle_user_access(email, grant=True):
    conn = get_db(); c = conn.cursor()
    c.execute('UPDATE users SET has_access_code=? WHERE email=?', (1 if grant else 0, email.lower().strip()))
    conn.commit(); conn.close(); return True


# ─── Telemetry Write ─────────────────────────────────────────────────────────

def log_login_event(email, event_type, ip='', user_agent='', screen_res='',
                    platform='', language='', timezone=''):
    conn = get_db(); c = conn.cursor()
    c.execute('''INSERT INTO login_events
        (user_email,event_type,ip_address,user_agent,screen_res,platform,language,timezone,timestamp)
        VALUES(?,?,?,?,?,?,?,?,?)''',
        (email.lower().strip(), event_type, ip, user_agent, screen_res,
         platform, language, timezone, utc_timestamp()))
    conn.commit(); conn.close()


def log_session_event(email, session_id, event_type, duration=None,
                      pages=None, series=None, ip=''):
    conn = get_db(); c = conn.cursor()
    c.execute('''INSERT INTO session_events
        (user_email,session_id,event_type,duration_seconds,pages_visited,series_browsed,ip_address,timestamp)
        VALUES(?,?,?,?,?,?,?,?)''',
        ((email or 'guest').lower().strip(), session_id, event_type, duration,
         json.dumps(pages) if pages else None, json.dumps(series) if series else None,
         ip, utc_timestamp()))
    conn.commit(); conn.close()


def log_site_access(ip, request_path, user_agent=''):
    if not ip:
        return
    conn = get_db(); c = conn.cursor()
    c.execute('''INSERT INTO site_access_events (ip_address,request_path,user_agent,timestamp)
                 VALUES(?,?,?,?)''',
              (ip, request_path[:500], user_agent[:500], utc_timestamp()))
    conn.commit(); conn.close()


def save_question_telemetry(email, rows, ip=''):
    if not rows: return
    conn = get_db(); c = conn.cursor()
    now = utc_timestamp()
    for q in rows:
        c.execute('''INSERT INTO question_telemetry
            (user_email,test_id,test_title,question_index,subject,question_type,marks,
             time_spent_sec,answer_changes,marked_review,was_revisited,final_answer,
             is_correct,marks_awarded,is_attempted,test_mode,ip_address,recorded_at)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
            (email.lower().strip(), q.get('testId',''), q.get('testTitle',''),
             int(q.get('questionIndex',0)), q.get('subject',''), q.get('type','MCQ'),
             float(q.get('marks',1)), int(q.get('timeSpent',0)),
             int(q.get('answerChanges',0)),
             1 if q.get('markedReview') else 0, 1 if q.get('wasRevisited') else 0,
             str(q.get('finalAnswer','')), 1 if q.get('isCorrect') else 0,
             float(q.get('marksAwarded',0)), 1 if q.get('isAttempted') else 0,
             q.get('testMode','exam'), ip, now))
    conn.commit(); conn.close()


def log_behavior_event(email, session_id, event_type, event_data=None, ip=''):
    conn = get_db(); c = conn.cursor()
    c.execute('''INSERT INTO behavior_events (user_email,session_id,event_type,event_data,ip_address,timestamp)
                 VALUES(?,?,?,?,?,?)''',
              ((email or 'guest').lower().strip(), session_id or '', event_type,
               json.dumps(event_data) if event_data else None,
               ip, utc_timestamp()))
    conn.commit(); conn.close()


# ─── Telemetry Read ───────────────────────────────────────────────────────────

def get_telemetry_dashboard(admin_email):
    if admin_email.lower().strip() != ADMIN_EMAIL:
        return {"error": "Unauthorized"}
    conn = get_db(); c = conn.cursor()

    def q(sql, p=()):
        c.execute(sql, p); return [dict(r) for r in c.fetchall()]

    def q1(sql, p=()):
        c.execute(sql, p); r = c.fetchone(); return dict(r) if r else {}

    data = {
        "activeUsers24h": q1("SELECT COUNT(DISTINCT user_email) as c FROM login_events WHERE event_type='login' AND timestamp>=datetime('now','-1 day')").get('c',0),
        "activeUsers7d":  q1("SELECT COUNT(DISTINCT user_email) as c FROM login_events WHERE event_type='login' AND timestamp>=datetime('now','-7 days')").get('c',0),
        "totalSessions":  q1("SELECT COUNT(*) as c FROM session_events WHERE event_type='start'").get('c',0),
        "avgSessionMins": q1("SELECT ROUND(AVG(duration_seconds)/60.0,1) as v FROM session_events WHERE event_type='end' AND duration_seconds IS NOT NULL").get('v',0) or 0,
        "recentLogins": q("SELECT user_email,event_type,ip_address,platform,screen_res,user_agent,timezone,timestamp FROM login_events ORDER BY id DESC LIMIT 60"),
        "recentSiteAccess": q("SELECT ip_address,request_path,user_agent,timestamp FROM site_access_events ORDER BY id DESC LIMIT 100"),
        "hardestQuestions": q("""
            SELECT test_id,test_title,question_index,subject,question_type,marks,
                   COUNT(*) as seen_by, ROUND(AVG(time_spent_sec),1) as avg_sec,
                   SUM(answer_changes) as total_changes, SUM(marked_review) as times_marked,
                   SUM(is_correct) as correct_n, SUM(is_attempted) as attempted_n,
                   ROUND(100.0*SUM(is_correct)/MAX(SUM(is_attempted),1),1) as acc_pct
            FROM question_telemetry GROUP BY test_id,question_index
            HAVING seen_by>=1 ORDER BY acc_pct ASC,avg_sec DESC LIMIT 25"""),
        "slowestQuestions": q("""
            SELECT test_id,test_title,question_index,subject,question_type,
                   COUNT(*) as seen_by, ROUND(AVG(time_spent_sec),1) as avg_sec,
                   SUM(marked_review) as times_marked,
                   ROUND(100.0*SUM(is_correct)/MAX(SUM(is_attempted),1),1) as acc_pct
            FROM question_telemetry GROUP BY test_id,question_index ORDER BY avg_sec DESC LIMIT 20"""),
        "mostSkipped": q("""
            SELECT test_id,test_title,question_index,subject,COUNT(*) as total_seen,
                   SUM(CASE WHEN is_attempted=0 THEN 1 ELSE 0 END) as skip_n,
                   ROUND(100.0*SUM(CASE WHEN is_attempted=0 THEN 1 ELSE 0 END)/COUNT(*),1) as skip_pct
            FROM question_telemetry GROUP BY test_id,question_index
            HAVING total_seen>=2 ORDER BY skip_pct DESC LIMIT 20"""),
        "studentStruggle": q("""
            SELECT user_email, COUNT(*) as total_qs,
                   ROUND(AVG(time_spent_sec),1) as avg_sec_per_q,
                   SUM(answer_changes) as total_changes,
                   SUM(marked_review) as total_marked,
                   ROUND(100.0*SUM(is_correct)/MAX(SUM(is_attempted),1),1) as acc_pct
            FROM question_telemetry GROUP BY user_email ORDER BY avg_sec_per_q DESC LIMIT 20"""),
        "subjectDifficulty": q("""
            SELECT subject, COUNT(*) as total_qs, ROUND(AVG(time_spent_sec),1) as avg_sec,
                   ROUND(100.0*SUM(is_correct)/MAX(SUM(is_attempted),1),1) as acc_pct,
                   SUM(marked_review) as times_marked
            FROM question_telemetry WHERE subject!='' GROUP BY subject ORDER BY acc_pct ASC"""),
        "platformBreakdown": q("SELECT platform, COUNT(*) as cnt FROM login_events WHERE platform IS NOT NULL AND platform!='' GROUP BY platform ORDER BY cnt DESC"),
        "loginByHour": q("SELECT strftime('%H',timestamp) as hr,COUNT(*) as cnt FROM login_events WHERE event_type='login' GROUP BY hr ORDER BY hr"),
        "behaviorSummary": q("SELECT event_type,COUNT(*) as cnt FROM behavior_events GROUP BY event_type ORDER BY cnt DESC"),
    }
    conn.close()
    return data


def get_student_telemetry_detail(admin_email, student_email):
    if admin_email.lower().strip() != ADMIN_EMAIL:
        return {"error": "Unauthorized"}
    email = student_email.lower().strip()
    conn = get_db(); c = conn.cursor()
    c.execute('SELECT * FROM login_events WHERE user_email=? ORDER BY id DESC LIMIT 40', (email,))
    logins = [dict(r) for r in c.fetchall()]
    c.execute('SELECT * FROM session_events WHERE user_email=? ORDER BY id DESC LIMIT 20', (email,))
    sessions = [dict(r) for r in c.fetchall()]
    c.execute('''SELECT test_id,test_title,question_index,subject,question_type,
                        time_spent_sec,answer_changes,marked_review,is_correct,
                        marks_awarded,is_attempted,recorded_at
                 FROM question_telemetry WHERE user_email=?
                 ORDER BY recorded_at DESC,question_index ASC LIMIT 200''', (email,))
    qs = [dict(r) for r in c.fetchall()]
    c.execute('SELECT event_type,event_data,ip_address,timestamp FROM behavior_events WHERE user_email=? ORDER BY id DESC LIMIT 60', (email,))
    behaviors = [dict(r) for r in c.fetchall()]
    conn.close()
    return {"logins": logins, "sessions": sessions, "questions": qs, "behaviors": behaviors}


if __name__ == '__main__':
    init_db()
