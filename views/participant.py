"""Munjiz as a feature inside the Expo 2030 Riyadh mobile app (concept mock-up), with a live agent trace.

The phone is a hand-built mobile UI (components/phone/index.html) talking to this page through Streamlit's
component bridge: it sends "send" / "confirm" / "new" events, and this page sends back the conversation,
desk cards and live ticket.
"""
import html
from datetime import datetime

import streamlit as st

from munjiz import config, expo, tickets
from munjiz.agent import run_turn
from munjiz.i18n import detect_lang, fmt_dt, t
from munjiz.rules import load_rules
from views.common import STATUS, desk_cards, desk_title, duration, md_bold, rule_count
from views.phone_component import phone

DEMO = [
    ("① Request", "I need to bring display equipment into our pavilion tomorrow at 10 pm. Two workers will come with the truck, and the screens need extra power."),
    ("② Answer", "Plate is ABC 1234. Workers: Ahmed Ali, ID 1023456789 and John Smith, passport P1234567. The screens need 40 kW."),
    ("① طلب", "أحتاج إدخال معدات عرض إلى جناحنا بكرة الساعة 10 مساءً. بيجي عاملين مع الشاحنة، والشاشات تحتاج كهرباء إضافية."),
    ("② رد", "لوحة الشاحنة أ ب ج 1234. العمال: محمد العتيبي هوية 1023456789، وخالد الشمري هوية 2098765432. والشاشات تحتاج 40 كيلوواط."),
    ("Rule demo", "We're bringing furniture by truck tomorrow at 3 pm, plate ABC 1234."),
]
YES = {"yes", "y", "confirm", "submit", "ok", "نعم", "اي", "ايوه", "أيوه", "تمام", "أكد", "ارسل", "أرسل"}
INTRO = {"summary": "summary_intro", "followup": "followup_intro", "problems": "problems_intro"}
CARD_STATE = {"ok": {"en": "✓ Ready", "ar": "✓ جاهز"}, "missing": {"en": "Needs info", "ar": "ينقصه معلومات"},
              "blocked": {"en": "Rule", "ar": "مخالفة قاعدة"}}

ss = st.session_state
for key, default in {"conv": [], "result": None, "ticket_id": None, "started_at": None, "force": None,
                     "last_event": None, "pavilion": next(iter(expo.PARTICIPANTS)), "contact": expo.ROLES[2],
                     "backend": config.BACKEND}.items():
    ss.setdefault(key, default)


# --- Conversation state ---------------------------------------------------------------------------
def lang() -> str:
    return ss.result.language if ss.result else "en"


def reset():
    ss.conv, ss.result, ss.ticket_id, ss.started_at = [], None, None, None
    ss.force = {"screen": "chat", "nonce": datetime.now().timestamp()}


def submit():
    if not (ss.result and ss.result.ready) or ss.ticket_id:
        return
    ss.ticket_id = tickets.submit(ss.result, ss.pavilion, ss.contact, ss.conv, started_at=ss.started_at)
    ss.conv.append({"role": "assistant", "content": t("submitted", lang(), ticket=ss.ticket_id), "lang": lang(),
                    "kind": "submitted"})


def handle(message: str):
    if ss.ticket_id:
        return
    if ss.result and ss.result.ready and message.strip().lower() in YES:
        submit()
        return
    ss.started_at = ss.started_at or config.now()
    ss.conv.append({"role": "user", "content": message, "lang": detect_lang(message)})
    try:
        result = run_turn(ss.conv, ss.pavilion, backend=ss.backend)
    except Exception as exc:  # Claude unreachable on stage: fall back to the offline parser
        st.toast(f"Claude unavailable ({type(exc).__name__}); using offline parser", icon="⚠️")
        result = run_turn(ss.conv, ss.pavilion, backend="local")
    ss.result = result
    cards = desk_cards(result)
    kind = ("summary" if result.ready else "followup" if any(c["missing"] for c in cards)
            else "problems" if cards else "plain")
    ss.conv.append({"role": "assistant", "content": result.reply, "lang": result.language, "kind": kind,
                    "cards": cards})


def send_demo(msg: str):
    handle(msg)
    ss.force = {"screen": "chat", "nonce": datetime.now().timestamp()}


# --- What the phone shows -------------------------------------------------------------------------
def phone_message(m: dict) -> dict:
    lang_, kind = m.get("lang", "en"), m.get("kind", "plain")
    out = {"role": "user" if m["role"] == "user" else "bot", "text": m["content"], "dir": "rtl" if lang_ == "ar" else "ltr"}
    if m["role"] != "user" and m.get("cards") and kind in INTRO:
        rules = load_rules()
        out["intro"] = t(INTRO[kind], lang_)
        out["outro"] = t("summary_outro", lang_) if kind == "summary" else ""
        out["cards"] = [{
            "icon": rules[c["desk"]]["icon"], "title": rules[c["desk"]]["title"][lang_], "state": c["state"],
            "state_label": CARD_STATE[c["state"]][lang_], "notes": c["notes"],
            "body": md_bold(c["detail"]) if c["state"] == "ok"
            else "<br>".join("• " + html.escape(x) for x in c["missing"] + c["problems"]),
        } for c in m["cards"]]
    return out


def phone_ticket(ticket: dict) -> dict:
    lang_ = ticket["language"] or "en"
    ar = lang_ == "ar"
    rules = load_rules()
    created = datetime.fromisoformat(ticket["created_at"])
    started = datetime.fromisoformat(ticket["started_at"] or ticket["created_at"])
    end = datetime.fromisoformat(ticket["closed_at"]) if ticket["closed_at"] else config.now()
    approved = sum(s["status"] == "approved" for s in ticket["subs"])
    subs = []
    for s in ticket["subs"]:
        if s["status"] == "pending":
            who = f'{s["id"]} · ' + (f'{s["desk_ref"]} · ' if s.get("desk_ref") else "") + (
                "بانتظار مراجعة الموظف" if ar else "waiting for desk review")
        else:
            who = f'{s["id"]} · {s["decided_by"]} · {fmt_dt(s["decided_at"], lang_)}'
            if s.get("reason"):
                who += f' · {s["reason"]}'
        subs.append({"id": s["id"], "icon": rules[s["desk"]]["icon"], "title": rules[s["desk"]]["title"][lang_],
                     "status": s["status"], "label": STATUS[s["status"]][lang_], "who": who})
    foot = (f"⏱ {duration((created - started).total_seconds(), lang_)} " + ("حتى الإرسال" if ar else "to submit")
            + " · " + (("أُنجز خلال " if ar else "done in ") if ticket["closed_at"] else ("مفتوحة منذ " if ar else "open for "))
            + duration((end - created).total_seconds(), lang_)
            + f" · {approved}/{len(subs)} " + ("موافقات" if ar else "approved"))
    done = ""
    if ticket["status"] == "completed":
        done = "تمت موافقة جميع الجهات. طلبك منجز." if ar else "All desks approved. Your request is done."
    return {"id": ticket["id"], "status": ticket["status"], "label": STATUS[ticket["status"]][lang_],
            "dir": "rtl" if ar else "ltr", "one": "تذكرة واحدة" if ar else "ONE TICKET", "subs": subs,
            "foot": foot, "done": done}


def phone_data() -> dict:
    now = config.now()
    mine = [tickets.get_ticket(x["id"]) for x in tickets.list_tickets() if x["pavilion"] == ss.pavilion]
    mine = [m for m in mine if m]
    current = tickets.get_ticket(ss.ticket_id) if ss.ticket_id else None
    n_desks = len(ss.result.checks) if ss.result else 0
    confirm = (f"تأكيد وإرسال إلى {n_desks} جهات" if lang() == "ar" else f"Confirm & send to {n_desks} desks")
    name = ss.pavilion.replace(" (example)", "")
    return {
        "clock": f"{now:%H:%M}", "expo_day": expo.expo_day(now) or "—", "days": expo.DAYS,
        "pavilion": name, "pavilion_type": expo.PARTICIPANTS[ss.pavilion], "role": ss.contact,
        "initials": "".join(w[0] for w in name.split()[:2]).upper(),
        "messages": [phone_message(m) for m in ss.conv],
        "ready": bool(ss.result and ss.result.ready and not ss.ticket_id), "confirm_label": confirm,
        "ticket": phone_ticket(current) if current else None,
        "tickets": [{"id": tk["id"], "status": tk["status"], "label": STATUS[tk["status"]]["en"],
                     "text": tk["request_text"], "subs": [s["status"] for s in tk["subs"]]} for tk in mine],
        "all_tickets": {tk["id"]: phone_ticket(tk) for tk in mine},
        "open_count": sum(tk["status"] != "completed" for tk in mine),
        "force": ss.force,
    }


phone_col, panel = st.columns([1, 1.15], gap="large")

with phone_col:
    @st.fragment(run_every="2s")
    def phone_fragment():
        event = phone(data=phone_data(), key="munjiz_phone", default=None)
        if event and event.get("nonce") != ss.last_event:
            ss.last_event = event["nonce"]
            if event["action"] == "send":
                handle(event["text"])
            elif event["action"] == "confirm":
                submit()
            elif event["action"] == "new":
                reset()
            st.rerun()  # whole page, so the agent trace updates at once

    phone_fragment()

# --- Presenter side: the story and the live agent trace ------------------------------------------
with panel:
    st.markdown('<div class="hero-line">One request.<br>One ticket. <span class="g">Done.</span></div>'
                '<div class="hero-ar">طلب واحد. تذكرة واحدة. منجز.</div>'
                '<div class="hero-sub">Munjiz lives inside the Expo 2030 Riyadh app. A pavilion team asks once; '
                'the agent splits the request across the service desks, checks each desk\'s rules, and sends one '
                'ticket. Desk staff approve it. Watch it work:</div>', unsafe_allow_html=True)

    @st.fragment(run_every="2s")
    def trace():
        r, tid = ss.result, ss.ticket_id
        ticket = tickets.get_ticket(tid) if tid else None
        followups = sum(1 for m in ss.conv if m.get("kind") == "followup")
        user_msgs = [m for m in ss.conv if m["role"] == "user"]
        desks = list(r.checks) if r else []
        n_rules = sum(rule_count(d) for d in desks)
        missing = sum(len([i for i in c.blocking if i.kind == "missing"]) for c in r.checks.values()) if r else 0
        broken = sum(len([i for i in c.blocking if i.kind == "rule"]) for c in r.checks.values()) if r else 0
        approved = sum(s["status"] == "approved" for s in ticket["subs"]) if ticket else 0

        def step(state, title, detail="", chips=()):
            chip_html = "".join(f"<span>{html.escape(c)}</span>" for c in chips)
            mark = "✓" if state == "done" else "•"
            return (f'<div class="step {state}"><div class="dot">{mark}</div><div><div class="t">{title}</div>'
                    f'<div class="d">{detail}</div>' + (f'<div class="chips">{chip_html}</div>' if chips else "")
                    + "</div></div>")

        lang_name = {"en": "English", "ar": "Arabic"}.get(lang(), "")
        steps = [
            step("done" if user_msgs else "active", "Understands a plain-language request",
                 f"{lang_name} · {len(user_msgs)} message{'s' if len(user_msgs) != 1 else ''}" if user_msgs
                 else "Waiting for the participant's message"),
            step("done" if desks else "pending", "Splits it into one sub-request per desk",
                 f"{len(desks)} desks; shared details (time, pavilion) entered once" if desks else "",
                 [desk_title(d, "en") for d in desks]),
            step("done" if r and r.ready else "active" if r else "pending", "Checks each desk's rules in code",
                 (f"{n_rules} rules checked · all passed" if r.ready else
                  f"{n_rules} rules checked · {missing} detail{'s' if missing != 1 else ''} missing"
                  + (f" · {broken} rule{'s' if broken != 1 else ''} broken" if broken else "")) if r else ""),
            step("done" if r and r.ready else "active" if r else "pending", "Asks once for what's missing",
                 (f"{followups} follow-up question" + ("s" if followups != 1 else "") if r.ready
                  else "Waiting for the participant's answer") if r else ""),
            step("done" if tid else "active" if r and r.ready else "pending", "Participant confirms the summary",
                 "Confirmed" if tid else "Waiting for confirmation" if r and r.ready else ""),
            step("done" if tid else "pending", "Sends everything under one ticket",
                 (f"{tid} · {len(ticket['subs'])} desks notified at once"
                  + (f" · n8n routed {routed} to desk systems" if (routed := sum(1 for s in ticket['subs'] if s.get('desk_ref'))) else ""))
                 if ticket else "",
                 [s["desk_ref"] for s in ticket["subs"] if s.get("desk_ref")] if ticket else ()),
            step("done" if ticket and ticket["status"] == "completed" else "active" if ticket else "pending",
                 "Desk staff approve (a human always decides)",
                 f"{approved} of {len(ticket['subs'])} approved" if ticket else ""),
        ]
        st.markdown('<div class="trace"><h4>Agent trace · live</h4>' + "".join(steps) + "</div>",
                    unsafe_allow_html=True)

    trace()

    st.markdown("**Demo scripts** · sends the message into the app")
    with st.container(key="demo", horizontal=True):
        for label, msg in DEMO:
            st.button(label, key=f"demo_{label}", disabled=bool(ss.ticket_id), on_click=send_demo, args=(msg,))
        st.button("↺ New request", on_click=reset)

    with st.expander("Presenter settings"):
        st.selectbox("Signed-in participant", list(expo.PARTICIPANTS), key="pavilion", disabled=bool(ss.conv))
        st.caption(expo.PARTICIPANTS[ss.pavilion])
        st.selectbox("Role", expo.ROLES, key="contact")
        st.radio("Agent backend", ["local", "claude"], key="backend", horizontal=True,
                 format_func={"local": "Offline parser (free)", "claude": "Claude (API)"}.get)
