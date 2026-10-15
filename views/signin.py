"""Sign in: the participant side (pavilion code) or the Expo Admin side (staff account + PIN)."""
import streamlit as st

from munjiz import users
from munjiz.agent import desk_title

ADMIN_HINT = {
    users.DESK_STAFF: "Sees only their desk's parts, already checked. Approves, requests a change or rejects.",
    users.SUPERVISOR: "Sees SLA reminders and escalations across desks. Reassigns or decides on a desk's behalf.",
    users.ORGANISER: "Sees the dashboard, every ticket's event log, and changes desk rules without code.",
}


def enter(user: dict | None):
    if user is None:
        st.error("That code didn't match. Check the demo accounts below.")
        return
    st.session_state.clear()
    st.session_state.user = user
    st.rerun()


PHONE_ICON = ('<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" '
              'stroke-linecap="round" stroke-linejoin="round"><rect x="6" y="2.5" width="12" height="19" rx="3"/>'
              '<path d="M10.5 18.5h3"/><path d="m9.5 10.5 1.8 1.8 3.4-3.6"/></svg>')
DESK_ICON = ('<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" '
             'stroke-linecap="round" stroke-linejoin="round"><path d="M12 2.8 19.5 6v5.6c0 4.6-3.2 8.2-7.5 9.6-4.3-1.4-7.5-5-7.5-9.6V6z"/>'
             '<path d="m8.8 12 2.2 2.2 4.3-4.4"/></svg>')


def door(kind: str, icon: str, eyebrow: str, title: str, text: str):
    st.markdown(f'<div class="door-hd"><div class="door-ic {kind}">{icon}</div><div><div class="door-eye">{eyebrow}</div>'
                f'<div class="door-t">{title}</div></div></div><p class="door-p">{text}</p>', unsafe_allow_html=True)


st.markdown('<div class="signin-hero"><div class="eyebrow-x">Expo 2030 Riyadh · Challenge 5.5 · Sign in to Munjiz</div>'
            '<div class="hero-line">One request. One ticket. <span class="g">Done.</span></div>'
            '<div class="hero-ar">طلب واحد. تذكرة واحدة. منجز.</div>'
            '<div class="hero-sub">Two sides, one ticket between them. <b>Pavilion teams ask; Expo Admin staff decide.</b> '
            'Each side only sees what it needs.</div></div>', unsafe_allow_html=True)

left, right = st.columns(2, gap="large")

with left:
    with st.container(border=True, key="door_participant"):
        door("p", PHONE_ICON, "Door 1 · Pavilion teams", "Participant",
             "Pavilion teams and their contractors. Sign in with your pavilion code.")
        with st.form("participant_form", border=False):
            code = st.text_input("Pavilion code", placeholder="e.g. FRA-2030")
            if st.form_submit_button("Sign in as participant", type="primary", width="stretch"):
                enter(users.sign_in_with_pavilion_code(code))
        st.caption("**Demo accounts (prototype)** · one-click sign-in")
        with st.container(horizontal=True):
            for pavilion, pcode in users.PAVILION_CODES.items():
                if st.button(pavilion.replace(" (example)", "").replace(" Pavilion", ""), key=f"q_{pcode}"):
                    enter(users.sign_in_with_pavilion_code(pcode))

with right:
    with st.container(border=True, key="door_admin"):
        door("a", DESK_ICON, "Door 2 · Expo Admin", "Expo Admin", "Desk staff, supervisors and organisers.")
        staff = [u for u in users.all_users() if u["role"] != users.PARTICIPANT]

        def label(uid: str) -> str:
            u = next(x for x in staff if x["id"] == uid)
            where = desk_title(u["desk"], "en") if u["desk"] else users.ROLE_LABEL[u["role"]].split(" · ")[1].title()
            return f"{u['name']} · {where}"

        with st.form("admin_form", border=False):
            uid = st.selectbox("Account", [u["id"] for u in staff], format_func=label)
            pin = st.text_input("PIN", type="password")
            if st.form_submit_button("Sign in to Expo Admin", type="primary", width="stretch"):
                enter(users.sign_in(uid, pin))
        st.caption("**Demo accounts (prototype)** · one-click sign-in")
        with st.container(horizontal=True):
            for uid in ("logistics.officer", "security.officer", "facilities.officer", "ops.supervisor", "expo.organiser"):
                u = next(x for x in staff if x["id"] == uid)
                short = desk_title(u["desk"], "en").split(" ", 1)[1].split(" &")[0] if u["desk"] else u["role"].title()
                if st.button(short, key=f"q_{uid}", help=ADMIN_HINT[u["role"]]):
                    enter(users.sign_in(uid, users.STAFF_PIN))

with st.expander("Demo accounts (prototype) · codes and PINs"):
    st.markdown(
        "**Participants** sign in with their pavilion code: "
        + " · ".join(f"`{c}` {p.replace(' (example)', '')}" for p, c in users.PAVILION_CODES.items())
        + f"\n\n**Expo Admin** accounts all use the demo PIN `{users.STAFF_PIN}`: "
        + " · ".join(f"`{u['id']}`" for u in users.all_users() if u["role"] != users.PARTICIPANT)
        + "\n\nThese are prototype accounts. A pilot would use the Expo's single sign-on, or the digital ID "
          "from challenge 5.2.")
    st.caption("Tip for the demo: open the participant in one browser window and Expo Admin in another. "
               "Each window keeps its own sign-in.")
