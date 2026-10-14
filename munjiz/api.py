"""Munjiz REST API: what n8n and desk systems call.

Run: uvicorn munjiz.api:app --host 0.0.0.0 --port 8000
Write endpoints need the header `X-Munjiz-Token: <MUNJIZ_API_TOKEN>` when a token is configured.

/mock/desks/* stands in for each desk's own system (gate booking, accreditation, utilities). In a pilot,
n8n would call the real systems instead and nothing in Munjiz would change.

Built on Starlette (already a Streamlit dependency), so it needs no extra install.
"""
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from . import config, tickets
from .db import connect, row

DESK_SYSTEM = {"logistics": "GATE", "security": "ACC", "facilities": "UTL"}


def error(status: int, detail: str) -> JSONResponse:
    return JSONResponse({"detail": detail}, status_code=status)


def authorised(request: Request) -> bool:
    return not config.API_TOKEN or request.headers.get("x-munjiz-token") == config.API_TOKEN


async def body_json(request: Request) -> dict | None:
    try:
        data = await request.json()
    except ValueError:
        return None
    return data if isinstance(data, dict) else None


async def health(request: Request):
    return JSONResponse({"ok": True, "n8n": bool(config.N8N_WEBHOOK_URL), "clock": config.now().isoformat()})


async def list_tickets(request: Request):
    return JSONResponse(tickets.list_tickets())


async def get_ticket(request: Request):
    ticket = tickets.get_ticket(request.path_params["ticket_id"])
    return JSONResponse(ticket) if ticket else error(404, f"No ticket {request.path_params['ticket_id']}")


async def pending(request: Request):
    """Used by the n8n SLA watchdog to find parts waiting too long."""
    try:
        minutes = float(request.query_params.get("older_than_minutes", 0))
    except ValueError:
        return error(422, "older_than_minutes must be a number")
    items = tickets.pending_older_than(minutes)
    return JSONResponse({"count": len(items), "items": items})


async def decide(request: Request):
    """A desk approves or rejects its part, from the staff console, n8n, or the desk's own system."""
    if not authorised(request):
        return error(401, "Missing or wrong X-Munjiz-Token header")
    data = await body_json(request)
    if data is None or not isinstance(data.get("approve"), bool) or not data.get("staff"):
        return error(422, 'Send JSON like {"approve": true, "staff": "logistics.officer", "reason": ""}')
    try:
        ticket = tickets.decide(request.path_params["sub_id"], data["approve"], str(data["staff"]),
                                str(data.get("reason") or ""))
    except ValueError as exc:
        return error(409, str(exc))
    return JSONResponse({"ticket_id": ticket["id"], "ticket_status": ticket["status"],
                         "subs": {s["id"]: s["status"] for s in ticket["subs"]}})


async def desk_inbox(request: Request):
    """Mock desk system: receives its part from n8n and returns its own reference number."""
    desk = request.path_params["desk"]
    if desk not in DESK_SYSTEM:
        return error(404, f"Unknown desk {desk}")
    if request.method == "GET":
        with connect() as conn:
            rows = conn.execute("SELECT id, ticket_id, status, desk_ref FROM sub_requests"
                                " WHERE desk=? AND desk_ref IS NOT NULL ORDER BY rowid DESC", (desk,))
            return JSONResponse([row(r) for r in rows])
    if not authorised(request):
        return error(401, "Missing or wrong X-Munjiz-Token header")
    data = await body_json(request)
    if data is None or not data.get("sub_id"):
        return error(422, 'Send JSON like {"sub_id": "LOG-1001", "ticket_id": "MNJ-1001"}')
    desk_ref = f"{DESK_SYSTEM[desk]}-{str(data['sub_id']).split('-')[-1]}"
    try:
        receipt = tickets.record_desk_receipt(desk, data["sub_id"], desk_ref)
    except ValueError as exc:
        return error(404, str(exc))
    return JSONResponse({"accepted": True, **receipt})


app = Starlette(routes=[
    Route("/health", health),
    Route("/api/tickets", list_tickets),
    Route("/api/tickets/{ticket_id}", get_ticket),
    Route("/api/subrequests/pending", pending),
    Route("/api/subrequests/{sub_id}/decision", decide, methods=["POST"]),
    Route("/mock/desks/{desk}/inbox", desk_inbox, methods=["GET", "POST"]),
])
