import html
import re
from datetime import datetime

import streamlit as st

from munjiz import config, expo
from munjiz.agent import AgentResult, desk_title, describe, locked_text, pick
from munjiz.i18n import fmt_dt
from munjiz.rules import DeskCheck, load_cross_desk, load_rules, rule_count  # noqa: F401

GREEN, GREEN_2, INK, MUTED, LINE = "#0B6B4F", "#12805F", "#111827", "#6B7280", "#E5E7EB"

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@400;600;700&display=swap');
.block-container { padding-top: 2.6rem !important; padding-bottom: 2rem !important; max-width: 1240px; }
.rtl, .rtl * { direction: rtl; text-align: right; font-family: 'IBM Plex Sans Arabic', sans-serif; }
[data-testid="stMetric"] { background:#fff; border:1px solid #E5E7EB; border-radius:14px; padding:12px 14px; }

/* Product header */
.brandbar { display:flex; flex-wrap:wrap; align-items:center; justify-content:space-between; gap:10px 18px;
  background: radial-gradient(120% 140% at 0% 0%, #12805F 0%, #0B6B4F 45%, #084A37 100%);
  color:#fff; padding:10px 16px; border-radius:16px; margin-bottom:0.8rem; box-shadow:0 10px 30px rgba(11,107,79,0.25); }
.brandbar .mark { width:42px; height:42px; border-radius:12px; background:#fff; color:#0B6B4F; display:grid;
  place-items:center; font-weight:800; font-size:1.35rem; box-shadow: inset 0 0 0 2px rgba(11,107,79,0.15); }
.brandbar .left { display:flex; align-items:center; gap:12px; }
.brandbar .name { font-size:1.35rem; font-weight:800; line-height:1.1; }
.brandbar .name .ar { font-family:'IBM Plex Sans Arabic', sans-serif; font-weight:700; opacity:0.95; }
.brandbar .sub { font-size:0.8rem; color:#CDEFE2; letter-spacing:0.02em; }
.brandbar .right { display:flex; flex-wrap:wrap; gap:8px; align-items:center; font-size:0.78rem; }
.brandbar .chip { background:rgba(255,255,255,0.14); border:1px solid rgba(255,255,255,0.2); padding:4px 10px;
  border-radius:999px; white-space:nowrap; }

.pill { display:inline-block; padding:2px 10px; border-radius:999px; font-size:0.74rem; font-weight:700; white-space:nowrap; }
.pill.pending { background:#FEF3C7; color:#92400E; }
.pill.approved, .pill.completed { background:#D1FAE5; color:#065F46; }
.pill.rejected, .pill.action_needed { background:#FEE2E2; color:#991B1B; }
.pill.changes_requested, .pill.partially_approved { background:#FFEDD5; color:#9A3412; }
.pill.in_review { background:#E0F2FE; color:#075985; }
.pill.sla-on_time { background:#F3F4F6; color:#374151; } .pill.sla-overdue { background:#FEF3C7; color:#92400E; }
.pill.sla-escalate { background:#FEE2E2; color:#991B1B; }

/* Signed-in bar */
.userbar { display:flex; align-items:center; gap:8px; font-size:0.85rem; color:#374151; justify-content:flex-end; padding-top:6px; }
.userbar .side { font-size:0.7rem; font-weight:800; letter-spacing:0.08em; text-transform:uppercase; padding:3px 9px; border-radius:999px; }
.userbar .side.participant { background:#E0F2FE; color:#075985; } .userbar .side.admin { background:#0B6B4F; color:#fff; }
.signin-card { border:1px solid #E5E7EB; border-radius:18px; padding:18px 20px 8px; background:#fff; height:100%; }
.signin-card h3 { margin:0 0 4px !important; } .signin-card p { color:#4B5563; font-size:0.92rem; }
.conflict-box { border:1px solid #FDBA74; background:#FFF7ED; border-radius:12px; padding:8px 12px; margin:6px 0; font-size:0.9rem; }

/* Presenter side */
.hero-line { font-size:2.3rem; font-weight:800; line-height:1.05; color:#111827; margin:0.2rem 0 0.3rem; letter-spacing:-0.02em; }
.hero-line .g { color:#0B6B4F; }
.hero-ar { font-family:'IBM Plex Sans Arabic', sans-serif; font-size:1.1rem; color:#0B6B4F; font-weight:700; direction:rtl; text-align:left; }
.hero-sub { color:#4B5563; font-size:0.95rem; margin:0.4rem 0 0.8rem; }
.trace { border:1px solid #E5E7EB; border-radius:18px; padding:14px 16px 6px; background:#fff; }
.trace h4 { margin:0 0 8px; font-size:0.8rem; letter-spacing:0.12em; color:#6B7280; text-transform:uppercase; }
.step { display:flex; gap:12px; padding:0 0 12px; position:relative; }
.step .dot { flex:0 0 26px; height:26px; border-radius:50%; display:grid; place-items:center; font-size:0.8rem;
  font-weight:800; background:#F3F4F6; color:#9CA3AF; border:2px solid #E5E7EB; z-index:1; }
.step:not(:last-child)::before { content:""; position:absolute; left:12px; top:26px; bottom:0; width:2px; background:#E5E7EB; }
.step.done .dot { background:#0B6B4F; color:#fff; border-color:#0B6B4F; }
.step.done:not(:last-child)::before { background:#0B6B4F; }
.step.active .dot { background:#fff; color:#0B6B4F; border-color:#0B6B4F; box-shadow:0 0 0 4px rgba(11,107,79,0.15); }
.step .t { font-weight:700; color:#111827; font-size:0.95rem; }
.step.pending .t { color:#9CA3AF; }
.step .d { font-size:0.82rem; color:#6B7280; }
.step .chips { margin-top:4px; display:flex; flex-wrap:wrap; gap:4px; }
.step .chips span { font-size:0.72rem; background:#ECFDF5; color:#065F46; border-radius:999px; padding:2px 8px; }
.st-key-demo button { border-radius:999px !important; }

/* Desk cards inside the chat */
.desk { border:1px solid #E5E7EB; border-radius:12px; padding:8px 10px; margin:6px 0; background:#fff; }
.desk .hd { display:flex; align-items:center; gap:6px; font-weight:800; font-size:0.82rem; color:#0F172A; }
.desk .hd .st { margin-left:auto; font-size:0.68rem; font-weight:800; padding:2px 8px; border-radius:999px; }
.rtl .desk .hd .st { margin-left:0; margin-right:auto; }
.desk.ok { border-color:#A7F3D0; background:#F0FDF7; } .desk.ok .st { background:#D1FAE5; color:#065F46; }
.desk.missing { border-color:#FDE68A; background:#FFFBEB; } .desk.missing .st { background:#FEF3C7; color:#92400E; }
.desk.blocked { border-color:#FECACA; background:#FEF2F2; } .desk.blocked .st { background:#FEE2E2; color:#991B1B; }
.desk.conflict { border-color:#FDBA74; background:#FFF7ED; } .desk.conflict .st { background:#FFEDD5; color:#9A3412; }
.desk .bd { font-size:0.8rem; color:#374151; margin-top:4px; line-height:1.35; }
.desk .note { font-size:0.74rem; color:#1D4ED8; margin-top:3px; }
.intro { font-size:0.88rem; color:#0F172A; }

/* Ticket inside the phone */
.tk { background:#fff; border:1px solid #E5E7EB; border-radius:16px; padding:12px; margin-top:6px;
  box-shadow:0 6px 16px rgba(15,23,42,0.06); }
.tk .top { display:flex; align-items:center; justify-content:space-between; }
.tk .id { font-weight:800; font-size:1rem; color:#0F172A; }
.tk .lbl { font-size:0.66rem; letter-spacing:0.12em; color:#6B7280; font-weight:700; }
.tk .bar { display:flex; gap:4px; margin:10px 0 8px; }
.tk .bar span { flex:1; height:6px; border-radius:999px; background:#E5E7EB; transition: background 0.4s; }
.tk .bar span.approved { background:#0B6B4F; } .tk .bar span.rejected { background:#DC2626; }
.tk .bar span.changes_requested { background:#F97316; }
.tk .row { display:flex; align-items:center; gap:8px; padding:5px 0; border-top:1px solid #F3F4F6; font-size:0.8rem; }
.tk .row .who { font-size:0.68rem; color:#6B7280; }
.tk .row .pill { margin-left:auto; }
.rtl .tk .row .pill { margin-left:0; margin-right:auto; }
.tk .foot { font-size:0.74rem; color:#4B5563; margin-top:6px; }
.tk .done { margin-top:8px; background:#0B6B4F; color:#fff; border-radius:10px; padding:8px 10px; font-weight:700;
  font-size:0.82rem; animation: pop 0.5s ease-out; }
@keyframes pop { from { transform: scale(0.96); opacity: 0; } to { transform: scale(1); opacity: 1; } }

/* Page header + KPI cards */
.ph .eyebrow { font-size:0.74rem; letter-spacing:0.14em; color:#0B6B4F; font-weight:800; text-transform:uppercase; }
.ph h1 { font-size:2rem !important; font-weight:800 !important; margin:0 !important; padding:0 !important; color:#111827; }
.ph p { color:#4B5563; margin:0.2rem 0 0.8rem; }
.kpis { display:grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap:12px; margin:0.6rem 0 1rem; }
.kpi { background:#fff; border:1px solid #E5E7EB; border-radius:16px; padding:14px 16px; }
.kpi .l { font-size:0.8rem; color:#6B7280; font-weight:600; }
.kpi .v { font-size:2rem; font-weight:800; color:#0B6B4F; line-height:1.1; margin-top:2px; }
.kpi .w { font-size:0.8rem; color:#6B7280; margin-top:2px; }
.kpi .w s { color:#9CA3AF; }
.kpi .c { display:inline-block; margin-top:6px; font-size:0.74rem; font-weight:800; color:#065F46; background:#D1FAE5;
  padding:2px 8px; border-radius:999px; }
.kpi.plain .v { color:#111827; }
.expo-footer { color:#6B7280; font-size:0.74rem; border-top:1px solid rgba(128,128,128,0.25); margin-top:2rem; padding-top:0.6rem; }
.sim-banner { background:#FFF7ED; border:1px solid #FDBA74; color:#9A3412; padding:8px 12px; border-radius:10px; font-size:0.9rem; }
</style>
"""

STATUS = {
    "pending": {"en": "Pending", "ar": "قيد المراجعة"},
    "approved": {"en": "Approved", "ar": "تمت الموافقة"},
    "rejected": {"en": "Rejected", "ar": "مرفوض"},
    "in_review": {"en": "In review", "ar": "قيد المراجعة"},
    "completed": {"en": "Done", "ar": "منجز"},
    "action_needed": {"en": "Action needed", "ar": "يحتاج إجراء"},
    "changes_requested": {"en": "Change requested", "ar": "مطلوب تعديل"},
    "partially_approved": {"en": "Partially approved", "ar": "موافقة جزئية"},
}


def inject_css():
    st.markdown(CSS, unsafe_allow_html=True)


def expo_header():
    """Product header: Munjiz brand, Expo context and the (simulated) Expo clock."""
    now = config.now()
    phase = expo.phase(now)
    day = f"Expo day {expo.expo_day(now)} of {expo.DAYS}" if phase == "operations" else expo.PHASE_LABEL[phase]["en"]
    sim = " · simulated" if config.CLOCK == "expo" else ""
    user = st.session_state.get("user")
    side = ("Expo Admin console" if user and user["role"] != "participant" else
            "Participant app" if user else "Participant request agent")
    st.markdown(
        '<div class="brandbar"><div class="left"><div class="mark">✓</div><div>'
        '<div class="name">Munjiz <span class="ar">· منجز</span></div>'
        f'<div class="sub">{side} · Expo 2030 Riyadh · Challenge 5.5</div></div></div>'
        '<div class="right"><span class="chip">1 Oct 2030 – 31 Mar 2031</span>'
        f'<span class="chip">🕒 {day} · {now:%a %d %b, %H:%M}{sim}</span></div></div>', unsafe_allow_html=True)


def expo_footer():
    st.markdown(
        '<div class="expo-footer">Munjiz is a hackathon prototype for Expo 2030 Riyadh challenge 5.5 and is not an '
        'official Expo service; the phone is a concept mock-up of the Expo app. Desk rules, gates, plots and dashboard '
        'data are simulated. Event facts: '
        + " · ".join(f'<a href="{url}" target="_blank">{label}</a>' for label, url in expo.SOURCES)
        + "</div>", unsafe_allow_html=True)


def page_header(eyebrow: str, title: str, sub: str):
    st.markdown(f'<div class="ph"><div class="eyebrow">{eyebrow}</div><h1>{title}</h1><p>{sub}</p></div>',
                unsafe_allow_html=True)


def kpi_cards(items: list[dict]):
    """items: {label, value, was?, change?, plain?}"""
    cards = "".join(
        f'<div class="kpi{" plain" if k.get("plain") else ""}"><div class="l">{k["label"]}</div><div class="v">{k["value"]}</div>'
        + (f'<div class="w">today <s>{k["was"]}</s></div>' if k.get("was") else "")
        + (f'<div class="c">{k["change"]}</div>' if k.get("change") else "") + "</div>" for k in items)
    st.markdown(f'<div class="kpis">{cards}</div>', unsafe_allow_html=True)


def text(md: str, lang: str = "en"):
    if lang == "ar":
        st.markdown(f'<div class="rtl">\n\n{md}\n\n</div>', unsafe_allow_html=True)
    else:
        st.markdown(md)


def pill(status: str, lang: str = "en") -> str:
    return f'<span class="pill {status}">{STATUS[status][lang]}</span>'


def ago(iso: str) -> str:
    secs = int((config.now() - datetime.fromisoformat(iso)).total_seconds())
    return duration(secs) + " ago"


def duration(secs: float, lang: str = "en") -> str:
    secs = max(int(secs), 0)
    s, m, h = ("ث", "د", "س") if lang == "ar" else ("s", "min", "h")
    if secs < 60:
        return f"{secs} {s}"
    if secs < 3600:
        return f"{secs // 60} {m} {secs % 60:02d} {s}"
    return f"{secs // 3600} {h} {secs % 3600 // 60:02d} {m}"


def md_plain(s: str) -> str:
    return s.replace("**", "")


def md_bold(s: str) -> str:
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", html.escape(s, quote=False))


def describe_sub(sub: dict, lang: str = "en") -> str:
    return describe(DeskCheck(desk=sub["desk"], payload=sub["payload"], assigned=sub["assigned"]), lang)


DESK_STATE = {
    "ok": {"en": "✓ Ready", "ar": "✓ جاهز"},
    "missing": {"en": "Needs info", "ar": "ينقصه معلومات"},
    "blocked": {"en": "Rule", "ar": "مخالفة قاعدة"},
    "conflict": {"en": "Clash between desks", "ar": "تعارض بين الجهات"},
}


def desk_cards(result: AgentResult) -> list[dict]:
    """Snapshot of each desk's sub-request for the chat: state plus what's missing or what will be booked.
    A last card shows clashes between desks (the cross-desk check), with the suggested fix."""
    lang, cards = result.language, []
    for desk, check in result.checks.items():
        count = check.payload.get("worker_count")
        missing = [i.message[lang] + (f" ({count} {'عمال' if lang == 'ar' else 'workers'})"
                                      if i.field == "workers" and count else "")
                   for i in check.blocking if i.kind == "missing"]
        problems = [i.message[lang] for i in check.blocking if i.kind == "rule"]
        state = "blocked" if problems else "missing" if missing else "ok"
        cards.append({"desk": desk, "state": state, "missing": missing, "problems": problems,
                      "notes": [i.message[lang] for i in check.notes],
                      "detail": describe(check, lang) if check.ok else ""})
    for card in cards:
        rules = load_rules()[card["desk"]]
        card.update(icon=rules["icon"], title=rules["title"][lang])
    clashes = result.blocking_conflicts
    if clashes:
        cross = load_cross_desk()
        locked = [locked_text(c, result.locked, lang) for c in clashes]
        cards.append({"desk": "cross_desk", "state": "conflict", "missing": [], "notes": [],
                      "problems": [c.message[lang] for c in clashes] + [md_plain(x) for x in locked if x],
                      "fixes": [c.fix[lang] for c, lock in zip(clashes, locked) if c.fix and not lock],
                      "icon": cross["icon"], "title": cross["title"][lang], "detail": ""})
    for card in cards:
        card.setdefault("fixes", [])
        card["notes"] += [c.message[lang] for c in result.conflicts if not c.blocking and card["desk"] in c.desks]
    return cards


def render_desk_cards(cards: list[dict], lang: str) -> str:
    out = []
    for c in cards:
        if c["state"] == "ok":
            body = md_bold(c["detail"])
        else:
            body = "<br>".join("• " + html.escape(x) for x in c["missing"] + c["problems"])
        notes = "".join(f'<div class="note">ℹ️ {html.escape(n)}</div>' for n in c["notes"])
        fixes = "".join(f'<div class="note">✅ {html.escape(f)}</div>' for f in c.get("fixes", []))
        notes += fixes
        out.append(f'<div class="desk {c["state"]}"><div class="hd">{c["icon"]} {html.escape(c["title"])}'
                   f'<span class="st">{DESK_STATE[c["state"]][lang]}</span></div><div class="bd">{body}</div>{notes}</div>')
    return "".join(out)


def ticket_mini(ticket: dict, lang: str = "en"):
    """The single ticket as the participant sees it in the app: progress bar, one row per desk, timers."""
    ar = lang == "ar"
    created = datetime.fromisoformat(ticket["created_at"])
    started = datetime.fromisoformat(ticket["started_at"] or ticket["created_at"])
    end = datetime.fromisoformat(ticket["closed_at"]) if ticket["closed_at"] else config.now()
    approved = sum(s["status"] == "approved" for s in ticket["subs"])
    rows = "".join(
        f'<div class="row"><div><b>{desk_title(s["desk"], lang)}</b><div class="who">{s["id"]}'
        + (f' · {s["decided_by"]} · {fmt_dt(s["decided_at"], lang)}' if s["status"] != "pending" else "")
        + (f' · {html.escape(s["reason"])}' if s.get("reason") else "")
        + f'</div></div>{pill(s["status"], lang)}</div>' for s in ticket["subs"])
    bar = "".join(f'<span class="{s["status"]}"></span>' for s in ticket["subs"])
    foot = (f'⏱ {duration((created - started).total_seconds(), lang)} ' + ("حتى الإرسال" if ar else "to submit") + " · "
            + (("أُنجز خلال " if ar else "done in ") if ticket["closed_at"] else ("مفتوحة منذ " if ar else "open "))
            + duration((end - created).total_seconds(), lang)
            + f" · {approved}/{len(ticket['subs'])} " + ("موافقات" if ar else "desks approved"))
    done = ""
    if ticket["status"] == "completed":
        done = ('<div class="done">✓ ' + ("تمت موافقة جميع الجهات. طلبك منجز." if ar else
                "All desks approved. Your request is done.") + "</div>")
    st.markdown(
        f'<div class="{"rtl" if ar else ""}"><div class="tk"><div class="top"><div>'
        f'<div class="lbl">{"تذكرة واحدة" if ar else "ONE TICKET"}</div><div class="id">{ticket["id"]}</div></div>'
        f'{pill(ticket["status"], lang)}</div><div class="bar">{bar}</div>{rows}<div class="foot">{foot}</div>{done}</div></div>',
        unsafe_allow_html=True)


def ticket_card(ticket: dict, lang: str = "en"):
    """Wide ticket view for the tracker: one row per desk, live status, and the timers."""
    with st.container(border=True):
        st.markdown(f"### Ticket {ticket['id']} &nbsp; {pill(ticket['status'], lang)}", unsafe_allow_html=True)
        for sub in ticket["subs"]:
            line = f"<b>{desk_title(sub['desk'], lang)}</b> &nbsp; {pill(sub['status'], lang)} &nbsp; <code>{sub['id']}</code>"
            if (sub.get("version") or 1) > 1:
                line += f" &nbsp; v{sub['version']} (fixed by the participant)"
            if sub["status"] != "pending":
                line += f" &nbsp;·&nbsp; {sub['decided_by']} · {fmt_dt(sub['decided_at'], lang)}"
            if sub.get("reason"):
                line += f"<br>↳ {sub['reason']}"
            st.markdown(f'<div class="{"rtl" if lang == "ar" else ""}" style="margin:4px 0">{line}</div>',
                        unsafe_allow_html=True)
        created = datetime.fromisoformat(ticket["created_at"])
        started = datetime.fromisoformat(ticket["started_at"] or ticket["created_at"])
        end = datetime.fromisoformat(ticket["closed_at"]) if ticket["closed_at"] else config.now()
        cols = st.columns(3)
        cols[0].metric("Participant time to submit", duration((created - started).total_seconds()))
        cols[1].metric("Done in" if ticket["closed_at"] else "Open for", duration((end - created).total_seconds()))
        approved = sum(s["status"] == "approved" for s in ticket["subs"])
        cols[2].metric("Desks approved", f"{approved} / {len(ticket['subs'])}")


def sla_pill(info: dict) -> str:
    label = {"on_time": f"⏱ {info['waited_minutes']:.0f} of {info['review_minutes']} min",
             "overdue": f"⏰ Overdue · {info['waited_minutes']:.0f} min (target {info['review_minutes']})",
             "escalate": f"🚨 Escalated · {info['waited_minutes']:.0f} min"}[info["level"]]
    return f'<span class="pill sla-{info["level"]}">{label}</span>'


def user_bar():
    """Who is signed in, which side they are on, and sign-out."""
    from munjiz.users import ROLE_LABEL
    user = st.session_state.get("user")
    if not user:
        return
    side = "participant" if user["role"] == "participant" else "admin"
    left, right = st.columns([5, 1], vertical_alignment="center")
    where = "" if user.get("pavilion") else (load_rules()[user["desk"]]["title"]["en"] if user.get("desk") else "all desks")
    left.markdown(f'<div class="userbar"><span class="side {side}">{"Participant" if side == "participant" else "Expo Admin"}</span>'
                  f'<b>{html.escape(user["name"])}</b> · {ROLE_LABEL[user["role"]].split(" · ")[1]}'
                  + (f' · {html.escape(where)}' if where else "") + '</div>',
                  unsafe_allow_html=True)
    if right.button("Sign out", key="sign_out", width="stretch"):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.query_params.clear()
        st.rerun()


__all__ = ["page_header", "kpi_cards", "expo_header", "expo_footer", "inject_css", "text", "pill", "ago", "duration", "describe_sub",
           "ticket_card", "ticket_mini", "desk_cards", "render_desk_cards", "rule_count", "pick", "desk_title",
           "sla_pill", "user_bar"]
