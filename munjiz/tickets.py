"""Mock desk services: submit one ticket fanned out to desks, desk staff approve or reject."""
import json
from datetime import datetime

from . import config
from . import events
from .agent import AgentResult, describe
from .db import connect, log, row
from .rules import DeskCheck, load_rules

DESK_PREFIX = {"logistics": "LOG", "security": "SEC", "facilities": "FAC"}


def _next_ticket_id(conn) -> str:
    n = conn.execute("SELECT COUNT(*) FROM tickets").fetchone()[0]
    return f"MNJ-{1001 + n}"


def submit(result: AgentResult, pavilion: str, contact: str, conversation: list[dict],
           started_at: datetime | None = None, now: datetime | None = None) -> str:
    if not result.ready:
        raise ValueError("request is not complete")
    now = now or config.now()
    followups = sum(1 for m in conversation if m["role"] == "assistant") - 1
    first_user = next(m["content"] for m in conversation if m["role"] == "user")
    with connect() as conn:
        tid = _next_ticket_id(conn)
        conn.execute(
            "INSERT INTO tickets (id, pavilion, contact, language, request_text, conversation, status, followups,"
            " started_at, created_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (tid, pavilion, contact, result.language, first_user, json.dumps(conversation, ensure_ascii=False),
             "in_review", max(followups, 0), (started_at or now).isoformat(), now.isoformat()))
        log(conn, "ticket_submitted", now.isoformat(), tid, desks=list(result.checks))
        for desk, check in result.checks.items():
            sid = f"{DESK_PREFIX[desk]}-{tid[4:]}"
            notes = [i.message for i in check.notes]
            conn.execute(
                "INSERT INTO sub_requests (id, ticket_id, desk, payload, assigned, notes, status) VALUES (?,?,?,?,?,?,?)",
                (sid, tid, desk, json.dumps(check.payload, ensure_ascii=False),
                 json.dumps(check.assigned, ensure_ascii=False), json.dumps(notes, ensure_ascii=False), "pending"))
            log(conn, "sent_to_desk", now.isoformat(), tid, sid, desk=desk)
    events.emit("ticket_submitted", _ticket_event(get_ticket(tid)))
    return tid


def _plain(markdown: str) -> str:
    return markdown.replace("**", "")


def _ticket_event(ticket: dict) -> dict:
    """What n8n needs to route each part: desk, a human-readable summary, the raw fields, and callback URLs."""
    rules = load_rules()
    return {
        "ticket_id": ticket["id"], "pavilion": ticket["pavilion"], "contact": ticket["contact"],
        "language": ticket["language"], "request_text": ticket["request_text"], "created_at": ticket["created_at"],
        "sub_requests": [{
            "id": s["id"], "desk": s["desk"], "desk_title": rules[s["desk"]]["title"]["en"],
            "summary": _plain(describe(DeskCheck(desk=s["desk"], payload=s["payload"], assigned=s["assigned"]), "en")),
            "payload": s["payload"], "notes": [n["en"] for n in s["notes"]],
            "decision_url": f"{config.PUBLIC_API_URL}/api/subrequests/{s['id']}/decision",
        } for s in ticket["subs"]],
    }


def decide(sub_id: str, approve: bool, staff: str, reason: str = "", now: datetime | None = None) -> dict:
    now = (now or config.now()).isoformat()
    with connect() as conn:
        sub = conn.execute("SELECT * FROM sub_requests WHERE id=?", (sub_id,)).fetchone()
        if sub is None or sub["status"] != "pending":
            raise ValueError(f"{sub_id} is not pending")
        status = "approved" if approve else "rejected"
        conn.execute("UPDATE sub_requests SET status=?, decided_by=?, decided_at=?, reason=? WHERE id=?",
                     (status, staff, now, reason, sub_id))
        log(conn, status, now, sub["ticket_id"], sub_id, desk=sub["desk"], staff=staff, reason=reason)

        statuses = [r[0] for r in conn.execute("SELECT status FROM sub_requests WHERE ticket_id=?", (sub["ticket_id"],))]
        if "rejected" in statuses:
            conn.execute("UPDATE tickets SET status='action_needed' WHERE id=?", (sub["ticket_id"],))
        elif all(s == "approved" for s in statuses):
            conn.execute("UPDATE tickets SET status='completed', closed_at=? WHERE id=?", (now, sub["ticket_id"]))
            log(conn, "ticket_completed", now, sub["ticket_id"])
    ticket = get_ticket(sub["ticket_id"])
    events.emit("sub_decided", {"ticket_id": ticket["id"], "sub_id": sub_id, "desk": sub["desk"], "status": status,
                                "staff": staff, "reason": reason, "ticket_status": ticket["status"],
                                "pavilion": ticket["pavilion"], "language": ticket["language"]})
    if ticket["status"] == "completed":
        minutes = (datetime.fromisoformat(ticket["closed_at"]) - datetime.fromisoformat(ticket["created_at"])).total_seconds() / 60
        events.emit("ticket_completed", {"ticket_id": ticket["id"], "pavilion": ticket["pavilion"],
                                         "language": ticket["language"], "closed_at": ticket["closed_at"],
                                         "minutes_to_complete": round(minutes, 1)})
    return ticket


def record_desk_receipt(desk: str, sub_id: str, desk_ref: str, via: str = "n8n") -> dict:
    """A desk's own system confirms it received its part (called by the mock desk systems through n8n)."""
    with connect() as conn:
        sub = conn.execute("SELECT * FROM sub_requests WHERE id=?", (sub_id,)).fetchone()
        if sub is None or sub["desk"] != desk:
            raise ValueError(f"{sub_id} is not a {desk} sub-request")
        conn.execute("UPDATE sub_requests SET desk_ref=? WHERE id=?", (desk_ref, sub_id))
        log(conn, "received_by_desk_system", config.now().isoformat(), sub["ticket_id"], sub_id,
            desk=desk, desk_ref=desk_ref, via=via)
    return {"sub_id": sub_id, "desk": desk, "desk_ref": desk_ref}


def pending_older_than(minutes: float) -> list[dict]:
    cutoff = config.now().timestamp() - minutes * 60
    out = []
    for desk in config.DESKS:
        for sub in desk_queue(desk):
            waited = (config.now() - datetime.fromisoformat(sub["created_at"])).total_seconds() / 60
            if datetime.fromisoformat(sub["created_at"]).timestamp() <= cutoff:
                out.append({"id": sub["id"], "ticket_id": sub["ticket_id"], "desk": desk, "pavilion": sub["pavilion"],
                            "waiting_minutes": round(waited, 1)})
    return sorted(out, key=lambda x: -x["waiting_minutes"])


def get_ticket(ticket_id: str) -> dict | None:
    with connect() as conn:
        t = conn.execute("SELECT * FROM tickets WHERE id=?", (ticket_id,)).fetchone()
        if t is None:
            return None
        ticket = row(t)
        ticket["subs"] = [row(r) for r in conn.execute(
            "SELECT * FROM sub_requests WHERE ticket_id=? ORDER BY rowid", (ticket_id,))]
        ticket["events"] = [row(r) for r in conn.execute(
            "SELECT * FROM events WHERE ticket_id=? ORDER BY id", (ticket_id,))]
    return ticket


def list_tickets() -> list[dict]:
    with connect() as conn:
        return [row(r) for r in conn.execute("SELECT * FROM tickets ORDER BY created_at DESC")]


def desk_queue(desk: str, status: str = "pending") -> list[dict]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT s.*, t.pavilion, t.contact, t.created_at, t.request_text FROM sub_requests s"
            " JOIN tickets t ON t.id = s.ticket_id WHERE s.desk=? AND s.status=? ORDER BY t.created_at",
            (desk, status))
        return [row(r) for r in rows]


def reset_live():
    """Clear demo tickets; simulated history stays."""
    with connect() as conn:
        conn.executescript("DELETE FROM events; DELETE FROM sub_requests; DELETE FROM tickets;")
