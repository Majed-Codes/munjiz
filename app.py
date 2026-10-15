import streamlit as st

st.set_page_config(page_title="Munjiz · Expo 2030 Riyadh", page_icon="✅", layout="wide")

from munjiz.users import PAGES, from_token, session_token  # noqa: E402
from views.common import expo_footer, expo_header, inject_css, user_bar  # noqa: E402

# Two sides, one ticket between them. Each role only gets the pages it may open.
ALL_PAGES = {
    "participant": st.Page("views/participant.py", title="Participant app", icon="📱", url_path="participant"),
    "staff": st.Page("views/staff.py", title="Desk console", icon="🗂️", url_path="desk"),
    "supervisor": st.Page("views/supervisor.py", title="SLA & escalations", icon="🚨", url_path="supervisor"),
    "tracker": st.Page("views/tracker.py", title="Ticket tracker", icon="🎫", url_path="tracker"),
    "dashboard": st.Page("views/dashboard.py", title="Organiser dashboard", icon="📊", url_path="dashboard"),
    "rules": st.Page("views/rules_admin.py", title="Desk rules", icon="⚖️", url_path="rules"),
}

user = st.session_state.get("user")
if user is None and (user := from_token(st.query_params.get("s"))):  # browser refresh: stay signed in
    st.session_state.user = user
if user is None:
    page = st.navigation([st.Page("views/signin.py", title="Sign in", icon="🔐", default=True)], position="hidden")
else:
    st.query_params["s"] = session_token(user)
    allowed = [ALL_PAGES[name] for name in PAGES[user["role"]]]
    page = st.navigation(allowed, position="top" if len(allowed) > 1 else "hidden")

inject_css()
expo_header()
user_bar()
page.run()
expo_footer()
