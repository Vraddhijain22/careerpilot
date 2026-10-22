import sqlite3
from contextlib import contextmanager
from app.config import db_path

@contextmanager
def connect():
    conn = sqlite3.connect(str(db_path()), timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 10000")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with connect() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS profile (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            resume_text TEXT NOT NULL DEFAULT '',
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        INSERT OR IGNORE INTO profile (id, resume_text) VALUES (1, '');
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT NOT NULL,
            role TEXT NOT NULL,
            job_url TEXT NOT NULL DEFAULT '',
            job_description TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'Interested',
            match_score INTEGER,
            notes TEXT NOT NULL DEFAULT '',
            follow_up_date TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS drafts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            application_id INTEGER,
            draft_type TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(application_id) REFERENCES applications(id) ON DELETE SET NULL
        );
        CREATE TABLE IF NOT EXISTS interview_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            application_id INTEGER,
            question TEXT NOT NULL,
            answer TEXT NOT NULL DEFAULT '',
            feedback TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(application_id) REFERENCES applications(id) ON DELETE SET NULL
        );
        """)


def save_resume(text: str):
    with connect() as db:
        db.execute("UPDATE profile SET resume_text=?, updated_at=CURRENT_TIMESTAMP WHERE id=1", (text,))


def get_resume() -> str:
    with connect() as db:
        row = db.execute("SELECT resume_text FROM profile WHERE id=1").fetchone()
        return row["resume_text"] if row else ""


def add_application(company, role, job_url="", job_description="", status="Interested", notes="", follow_up_date="") -> int:
    with connect() as db:
        cur = db.execute("""INSERT INTO applications
            (company, role, job_url, job_description, status, notes, follow_up_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (company.strip(), role.strip(), job_url.strip(), job_description.strip(), status, notes.strip(), follow_up_date))
        return int(cur.lastrowid)


def list_applications():
    with connect() as db:
        rows = db.execute("SELECT * FROM applications ORDER BY updated_at DESC, id DESC").fetchall()
        return [dict(r) for r in rows]


def get_application(app_id: int):
    with connect() as db:
        row = db.execute("SELECT * FROM applications WHERE id=?", (app_id,)).fetchone()
        return dict(row) if row else None


def update_application(app_id: int, **fields):
    allowed = {"company", "role", "job_url", "job_description", "status", "match_score", "notes", "follow_up_date"}
    values = {k: v for k, v in fields.items() if k in allowed}
    if not values:
        return
    assignments = ", ".join(f"{k}=?" for k in values)
    with connect() as db:
        db.execute(f"UPDATE applications SET {assignments}, updated_at=CURRENT_TIMESTAMP WHERE id=?", (*values.values(), app_id))


def save_draft(application_id, draft_type, content):
    with connect() as db:
        cur = db.execute("INSERT INTO drafts (application_id, draft_type, content) VALUES (?, ?, ?)", (application_id, draft_type, content))
        return int(cur.lastrowid)


def list_drafts():
    with connect() as db:
        return [dict(r) for r in db.execute("SELECT * FROM drafts ORDER BY id DESC").fetchall()]


def save_interview(application_id, question, answer, feedback):
    with connect() as db:
        cur = db.execute("INSERT INTO interview_sessions (application_id, question, answer, feedback) VALUES (?, ?, ?, ?)", (application_id, question, answer, feedback))
        return int(cur.lastrowid)


def list_interviews():
    with connect() as db:
        return [dict(r) for r in db.execute("SELECT * FROM interview_sessions ORDER BY id DESC").fetchall()]
