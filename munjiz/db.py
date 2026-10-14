"""SQLite store for tickets, desk sub-requests and the event log. Mock desk services read and write here."""
import json
import sqlite3
from contextlib import contextmanager

from . import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS tickets (
    id TEXT PRIMARY KEY,
    pavilion TEXT NOT NULL,
    contact TEXT,
    language TEXT,
    request_text TEXT,
    conversation TEXT,
    status TEXT NOT NULL,             -- in_review | completed | action_needed
    followups INTEGER DEFAULT 0,      -- agent follow-up questions before confirmation
    started_at TEXT,                  -- participant's first message
    created_at TEXT NOT NULL,         -- submitted
    closed_at TEXT
);
CREATE TABLE IF NOT EXISTS sub_requests (
    id TEXT PRIMARY KEY,
    ticket_id TEXT NOT NULL REFERENCES tickets(id),
    desk TEXT NOT NULL,
    payload TEXT NOT NULL,
    assigned TEXT NOT NULL,
    notes TEXT NOT NULL,
    status TEXT NOT NULL,             -- pending | approved | rejected
    decided_by TEXT,
    decided_at TEXT,
    reason TEXT,
    desk_ref TEXT                     -- reference from the desk's own system (via n8n)
);
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id TEXT,
    sub_id TEXT,
    type TEXT NOT NULL,
    at TEXT NOT NULL,
    detail TEXT
);
CREATE TABLE IF NOT EXISTS hist_requests (
    request_id TEXT PRIMARY KEY,
    participant_type TEXT, pavilion TEXT, request_type TEXT, desks TEXT, submitted_at TEXT,
    legacy_hours REAL, munjiz_hours REAL,
    legacy_first_time INTEGER, munjiz_first_time INTEGER,
    legacy_participant_minutes REAL, munjiz_participant_minutes REAL,
    legacy_forms INTEGER
);
CREATE TABLE IF NOT EXISTS hist_steps (
    request_id TEXT, desk TEXT, process TEXT, wait_hours REAL, reworked INTEGER
);
"""


@contextmanager
def connect():
    config.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(config.DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(SCHEMA)
    cols = {r[1] for r in conn.execute("PRAGMA table_info(sub_requests)")}
    if "desk_ref" not in cols:  # databases created before the n8n integration
        conn.execute("ALTER TABLE sub_requests ADD COLUMN desk_ref TEXT")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def log(conn, type_: str, at: str, ticket_id=None, sub_id=None, **detail):
    conn.execute("INSERT INTO events (ticket_id, sub_id, type, at, detail) VALUES (?,?,?,?,?)",
                 (ticket_id, sub_id, type_, at, json.dumps(detail, ensure_ascii=False)))


def row(r: sqlite3.Row) -> dict:
    d = dict(r)
    for k in ("payload", "assigned", "notes", "conversation", "detail"):
        if isinstance(d.get(k), str):
            d[k] = json.loads(d[k])
    return d
