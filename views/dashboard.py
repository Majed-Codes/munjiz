import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from munjiz import expo, simulate, tickets
from munjiz.agent import desk_title
from munjiz.config import DESKS
from munjiz.db import connect
from views.common import ago, kpi_cards, page_header

# Categorical slots from the validated reference palette; "before" is a recessive neutral.
DESK_COLOR = {"logistics": "#2a78d6", "security": "#eb6834", "facilities": "#1baf7a"}
BEFORE, AFTER = "#a3a29c", "#0B6B4F"
DESK_NAME = {d: desk_title(d, "en").split(" ", 1)[1] for d in DESKS}


def style(fig: go.Figure, height=320) -> go.Figure:
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=36, b=10), bargap=0.35, bargroupgap=0.08,
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, title=None),
                      font=dict(family="Source Sans Pro, sans-serif", size=13), plot_bgcolor="rgba(0,0,0,0)",
                      paper_bgcolor="rgba(0,0,0,0)", hoverlabel=dict(font_size=13))
    fig.update_xaxes(gridcolor="rgba(128,128,128,0.15)", zeroline=False, automargin=True, title_standoff=8,
                     title_font_size=12)
    fig.update_yaxes(gridcolor="rgba(0,0,0,0)", automargin=True, ticksuffix="  ")
    fig.update_traces(marker_line_width=0)
    return fig


@st.cache_data(ttl=5)
def load():
    with connect() as conn:
        req = pd.read_sql("SELECT * FROM hist_requests", conn)
        steps = pd.read_sql("SELECT * FROM hist_steps", conn)
    return req, steps


page_header("Organiser dashboard", "Where participant requests wait, and what one ticket changes",
            "Expo 2030 Riyadh participant services across Logistics & Site Access, Accreditation & Security and "
            "Facilities & Utilities.")
req, steps = load()
if req.empty:
    simulate.generate()
    load.clear()
    req, steps = load()

st.markdown(f'<div class="sim-banner"><b>Simulated data.</b> {len(req)} synthetic participant requests, each run '
            'through a model of today\'s process and of Munjiz. The assumptions are listed at the bottom; '
            'replace them with real figures from the organisers.</div>', unsafe_allow_html=True)
st.write("")

# Headline numbers: stat tiles, not charts.
L, M = req.legacy_hours.mean(), req.munjiz_hours.mean()
LP, MP = req.legacy_participant_minutes.mean(), req.munjiz_participant_minutes.mean()
LF, MF = req.legacy_first_time.mean(), req.munjiz_first_time.mean()
kpi_cards([
    {"label": "Time to complete a request", "value": f"{M:.1f} h", "was": f"{L:.1f} h", "change": f"{M / L - 1:.0%}"},
    {"label": "Participant effort", "value": f"{MP:.0f} min", "was": f"{LP:.0f} min", "change": f"{MP / LP - 1:.0%}"},
    {"label": "Complete first time", "value": f"{MF:.0%}", "was": f"{LF:.0%}", "change": f"+{(MF - LF) * 100:.0f} pts"},
    {"label": "Forms per request", "value": "1", "was": f"{req.legacy_forms.mean():.1f}",
     "change": f"{1 / req.legacy_forms.mean() - 1:.0%}"},
])

st.subheader("At Expo 2030 Riyadh scale")
s1, s2, s3 = st.columns(3)
participants = s1.number_input("Participating countries", 50, 250, expo.FACTS["expected_participating_countries"],
                               help="Organisers expect 197 participating countries (Swiss Federal Council notice, Apr 2026).")
per_month = s2.number_input("Cross-desk requests per participant per month", 1, 100, 10,
                            help="Assumption. Ask mentors for a real figure.")
months = s3.number_input("Months of build-up and operations", 1, 36, 18,
                         help="Assumption: about 12 months of pavilion build-up plus the 6 months the Expo is open.")
total = participants * per_month * months
reworks = steps.groupby("process").reworked.sum() / len(req)
kpi_cards([
    {"label": "Requests in one window", "value": f"{total:,.0f}", "plain": True},
    {"label": "Participant hours saved", "value": f"{total * (LP - MP) / 60:,.0f}"},
    {"label": "Request-days of waiting removed", "value": f"{total * (L - M) / 24:,.0f}"},
    {"label": "Bounced forms avoided", "value": f"{total * (reworks['legacy'] - reworks['munjiz']):,.0f}"},
])
st.caption("Projection = the simulated per-request savings above × requests at Expo scale. Only the participant "
           "count is a public figure; everything else is an assumption to replace with organiser data.")

left, right = st.columns(2)
with left:
    st.subheader("Completion time, before vs after")
    by_type = req.groupby("request_type")[["legacy_hours", "munjiz_hours"]].mean().sort_values("legacy_hours")
    fig = go.Figure([
        go.Bar(y=by_type.index, x=by_type.legacy_hours, name="Today (3 desks, one by one)", orientation="h",
               marker_color=BEFORE, hovertemplate="%{y}<br>Today: %{x:.1f} h<extra></extra>"),
        go.Bar(y=by_type.index, x=by_type.munjiz_hours, name="Munjiz (one ticket, in parallel)", orientation="h",
               marker_color=AFTER, text=[f"{v:.1f} h" for v in by_type.munjiz_hours], textposition="outside",
               hovertemplate="%{y}<br>Munjiz: %{x:.1f} h<extra></extra>"),
    ])
    fig.update_xaxes(title="Average hours from request to all approvals")
    st.plotly_chart(style(fig), width="stretch", theme=None)

with right:
    st.subheader("Requests by type and desk")
    exploded = req.assign(desk=req.desks.str.split(",")).explode("desk")
    counts = exploded.groupby(["request_type", "desk"]).size().unstack(fill_value=0)
    counts = counts.loc[counts.sum(axis=1).sort_values().index]
    fig = go.Figure([go.Bar(y=counts.index, x=counts[d], name=DESK_NAME[d], orientation="h",
                            marker_color=DESK_COLOR[d],
                            hovertemplate="%{y}<br>" + DESK_NAME[d] + ": %{x} sub-requests<extra></extra>")
                     for d in DESKS if d in counts])
    fig.update_layout(barmode="stack")
    fig.update_traces(marker_line_color="white")  # 2px gap between stacked segments
    fig.update_xaxes(title="Desk sub-requests")
    st.plotly_chart(style(fig).update_traces(marker_line_width=2), width="stretch", theme=None)

left, right = st.columns(2)
with left:
    st.subheader("Bottlenecks: average wait per desk")
    wait = steps.groupby(["desk", "process"]).wait_hours.mean().unstack().sort_values("legacy")
    names = [DESK_NAME[d] for d in wait.index]
    fig = go.Figure([
        go.Bar(y=names, x=wait.legacy, name="Today", orientation="h", marker_color=BEFORE,
               hovertemplate="%{y}<br>Today: %{x:.1f} h<extra></extra>"),
        go.Bar(y=names, x=wait.munjiz, name="Munjiz", orientation="h", marker_color=AFTER,
               text=[f"{v:.1f} h" for v in wait.munjiz], textposition="outside",
               hovertemplate="%{y}<br>Munjiz: %{x:.1f} h<extra></extra>"),
    ])
    fig.update_xaxes(title="Average hours at the desk")
    st.plotly_chart(style(fig, 260), width="stretch", theme=None)
    rework = steps[steps.process == "legacy"].reworked.mean()
    st.caption(f"{names[-1]} is the slowest desk today ({wait.legacy.iloc[-1]:.1f} h on average), and {rework:.0%} "
               "of desk forms bounce back for missing information. Munjiz checks each desk's rules before "
               "anything is sent, and the desks work in parallel.")

with right:
    st.subheader("Live: waiting longest")

    @st.fragment(run_every="5s")
    def live():
        rows = [dict(sub, waiting=ago(sub["created_at"])) for d in DESKS for sub in tickets.desk_queue(d)]
        live_tickets = tickets.list_tickets()
        c = st.columns(3)
        c[0].metric("Demo tickets", len(live_tickets))
        c[1].metric("Completed", sum(t["status"] == "completed" for t in live_tickets))
        c[2].metric("Sub-requests pending", len(rows))
        if rows:
            rows.sort(key=lambda r: r["created_at"])
            st.dataframe(pd.DataFrame([{"Sub-request": r["id"], "Desk": DESK_NAME[r["desk"]],
                                        "Pavilion": r["pavilion"], "Waiting": r["waiting"]} for r in rows[:8]]),
                         hide_index=True, width="stretch")
        else:
            st.caption("No live sub-requests waiting.")

    live()

with st.expander("Simulation assumptions (replace with organiser figures)"):
    st.dataframe(pd.DataFrame(simulate.ASSUMPTIONS.items(), columns=["Assumption", "Value"]), hide_index=True)
    st.caption("Generated by munjiz/simulate.py with a fixed seed, so the numbers are reproducible.")

with st.expander("Data table"):
    st.dataframe(req, hide_index=True, width="stretch")
