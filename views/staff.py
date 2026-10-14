import streamlit as st

from munjiz import config, tickets
from munjiz.agent import desk_title
from munjiz.rules import check_desk, load_rules
from views.common import ago, describe_sub, page_header, pill

REJECT_REASONS = ["ID could not be verified", "Slot unavailable, please pick another time",
                  "Capacity exceeded", "Missing documents"]

page_header("Back office · desk staff", "Desk console",
            "Each desk sees only its part of the ticket, already checked against its rules. The agent prepares; "
            "a person approves.")

desk = st.segmented_control("Desk", config.DESKS, default="logistics", format_func=lambda d: desk_title(d, "en"),
                            key="staff_desk") or "logistics"
staff = st.text_input("Signed in as", f"{desk}.officer", key=f"staff_{desk}")


def decide(sub_id: str, approve: bool, reason: str = ""):
    try:
        tickets.decide(sub_id, approve, staff, reason)
    except ValueError:
        return  # already decided (double click or another officer)
    st.toast(f"{sub_id} {'approved' if approve else 'rejected'}", icon="✅" if approve else "❌")


@st.fragment(run_every="3s")
def queue():
    pending = tickets.desk_queue(desk)
    st.subheader(f"Pending ({len(pending)})")
    if not pending:
        st.caption("Nothing waiting. New sub-requests appear here as soon as a participant confirms.")
    for sub in pending:
        with st.container(border=True):
            st.markdown(f"**{sub['id']}** · ticket `{sub['ticket_id']}` · {sub['pavilion']} · "
                        f"submitted {ago(sub['created_at'])}")
            st.markdown(describe_sub(sub))

            recheck = check_desk(desk, sub["payload"], config.now())
            n_checks = len(load_rules()[desk]["checks"]) + len(load_rules()[desk]["required"])
            if recheck.ok:
                st.markdown(f"🛡️ Rule check: **passed** ({n_checks} checks)")
            if sub.get("desk_ref"):
                st.markdown(f"🔗 Routed by n8n to the desk system · ref `{sub['desk_ref']}`")
            else:
                st.warning("Rule check now fails: " + "; ".join(i.message["en"] for i in recheck.blocking))
            for note in sub["notes"]:
                st.info(note["en"], icon="ℹ️")

            others = [s for s in tickets.get_ticket(sub["ticket_id"])["subs"] if s["desk"] != desk]
            st.markdown("Other desks on this ticket: " + " &nbsp; ".join(
                f"{desk_title(s['desk'], 'en')} {pill(s['status'])}" for s in others), unsafe_allow_html=True)
            with st.expander("Participant's original words"):
                st.write(sub["request_text"])

            c1, c2, c3 = st.columns([1, 2, 1])
            c1.button("Approve", key=f"ok_{sub['id']}", type="primary", on_click=decide, args=(sub["id"], True),
                      width="stretch")
            reason = c2.selectbox("Reason", REJECT_REASONS, key=f"why_{sub['id']}", label_visibility="collapsed")
            c3.button("Reject", key=f"no_{sub['id']}", on_click=decide, args=(sub["id"], False, reason),
                      width="stretch")

    done = tickets.desk_queue(desk, "approved") + tickets.desk_queue(desk, "rejected")
    if done:
        st.subheader("Recently decided")
        for sub in sorted(done, key=lambda s: s["decided_at"], reverse=True)[:8]:
            st.markdown(f"`{sub['id']}` {sub['pavilion']} &nbsp; {pill(sub['status'])} &nbsp; "
                        f"by {sub['decided_by']} {ago(sub['decided_at'])}" + (f" · {sub['reason']}" if sub["reason"] else ""),
                        unsafe_allow_html=True)


queue()
