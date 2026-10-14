import streamlit as st

st.set_page_config(page_title="Munjiz · Expo 2030 Riyadh", page_icon="✅", layout="wide")

from views.common import expo_footer, expo_header, inject_css  # noqa: E402

page = st.navigation([
    st.Page("views/participant.py", title="Participant app", icon="📱", default=True),
    st.Page("views/staff.py", title="Desk console", icon="🗂️"),
    st.Page("views/tracker.py", title="Ticket tracker", icon="🎫"),
    st.Page("views/dashboard.py", title="Organiser dashboard", icon="📊"),
], position="top")
inject_css()
expo_header()
page.run()
expo_footer()
