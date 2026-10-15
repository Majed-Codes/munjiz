import html
import re
from datetime import datetime

import streamlit as st

from munjiz import config, expo
from munjiz.agent import AgentResult, desk_title, describe, locked_text, pick
from munjiz.i18n import fmt_dt
from munjiz.rules import DeskCheck, load_cross_desk, load_rules, rule_count  # noqa: F401

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Rubik:wght@500;600;700;800&family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Sans+Arabic:wght@400;500;600;700&display=swap');
/* ---- Night at the Expo: tokens -------------------------------------------------------------- */
:root {
  --bg: #06120E; --bg-2: #0A1A14; --bg-3: #10261D;
  --glass: rgba(255,255,255,0.05); --glass-2: rgba(255,255,255,0.08); --line: rgba(255,255,255,0.10); --line-2: rgba(255,255,255,0.16);
  --ink: #EEF5F1; --ink-2: #C9D8D1; --muted: #9AAFA6;
  --em: #2FBF8A; --em-2: #12805F; --em-3: #7FE0B8; --gold: #E2B04A; --gold-2: #F3D58E;
  --amber: #FFD27A; --red: #FCA5A5; --orange: #FDBA74; --sky: #8BD3F7;
  --head: Rubik, 'IBM Plex Sans Arabic', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  --body: 'IBM Plex Sans', 'IBM Plex Sans Arabic', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  --ar: 'IBM Plex Sans Arabic', 'Geeza Pro', 'Segoe UI', sans-serif;
}

/* ---- Stage: night-green base, emerald and gold glows, a faint Sadu weave at the edges ------------ */
.stApp { background-color: var(--bg) !important;
  background-image:
    radial-gradient(1100px 620px at 6% -12%, rgba(47,191,138,0.20), transparent 62%),
    radial-gradient(900px 560px at 104% -6%, rgba(226,176,74,0.13), transparent 60%),
    radial-gradient(1200px 700px at 50% 118%, rgba(18,128,95,0.20), transparent 62%),
    linear-gradient(180deg, #071711 0%, #06120E 55%, #050F0B 100%) !important;
  background-attachment: fixed !important; }
.stApp::before { content:""; position:fixed; inset:0; pointer-events:none; z-index:0; opacity:0.07;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='96' height='96' viewBox='0 0 96 96'%3E%3Cg fill='none' stroke='%23E2B04A' stroke-width='1.2'%3E%3Cpath d='M48 14 82 48 48 82 14 48Z'/%3E%3Cpath d='M48 30 66 48 48 66 30 48Z'/%3E%3C/g%3E%3Cg fill='%232FBF8A'%3E%3Cpath d='M44 48 48 44 52 48 48 52Z'/%3E%3Cpath d='M0 0h12L6 7ZM24 0h12l-6 7ZM48 0h12l-6 7ZM72 0h12l-6 7ZM12 96h12l-6-7ZM36 96h12l-6-7ZM60 96h12l-6-7ZM84 96h12l-6-7Z'/%3E%3C/g%3E%3C/svg%3E");
  background-size: 96px 96px;
  -webkit-mask-image: radial-gradient(ellipse 70% 70% at 50% 45%, transparent 40%, #000 100%);
          mask-image: radial-gradient(ellipse 70% 70% at 50% 45%, transparent 40%, #000 100%); }
[data-testid="stAppViewContainer"], [data-testid="stMain"], [data-testid="stBottomBlockContainer"] { background: transparent !important; }
[data-testid="stAppViewContainer"] { position: relative; z-index: 1; }
header[data-testid="stHeader"] { background: rgba(6,18,14,0.55) !important; backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px); border-bottom: 1px solid rgba(255,255,255,0.06); }
header[data-testid="stHeader"]:not(:has([data-testid="stTopNavLink"])) { background: transparent !important;
  backdrop-filter: none; -webkit-backdrop-filter: none; border-bottom: none; }
.stApp:has([data-testid="stTopNavLink"]) .block-container { padding-top: 4.6rem !important; }
.block-container { padding-top: 2.4rem !important; padding-bottom: 2rem !important; max-width: 1280px; }
html, body, .stApp { font-family: var(--body); }
.stApp h1, .stApp h2, .stApp h3, .stApp h4 { font-family: var(--head) !important; letter-spacing: -0.01em; color: var(--ink); }
.stApp p, .stApp li { color: var(--ink-2); }
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p { color: var(--muted) !important; }
.rtl, .rtl * { direction: rtl; text-align: right; font-family: var(--ar); }
a { color: var(--em-3); }

[data-testid="stSidebar"] { background: rgba(7,20,15,0.88) !important; border-right: 1px solid var(--line);
  backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px); }

/* Top navigation (organiser / supervisor) */
[data-testid="stTopNavLink"] { border-radius: 999px !important; padding: 4px 12px !important; }
[data-testid="stTopNavLink"] p { color: var(--ink-2) !important; font-weight: 500; }
[data-testid="stTopNavLink"]:hover { background: var(--glass-2) !important; }
[data-testid="stTopNavLink"][aria-current="page"] { background: rgba(47,191,138,0.14) !important;
  box-shadow: inset 0 0 0 1px rgba(47,191,138,0.45); }
[data-testid="stTopNavLink"][aria-current="page"] p { color: var(--ink) !important; font-weight: 600; }

/* ---- Brand bar: slim dark glass with the glowing check mark --------------------------------------- */
.brandbar { position:relative; overflow:hidden; display:flex; flex-wrap:wrap; align-items:center; justify-content:space-between;
  gap:10px 18px; color:var(--ink); padding:9px 14px 9px 10px; border-radius:18px; margin-bottom:0.7rem;
  background: linear-gradient(180deg, rgba(255,255,255,0.07), rgba(255,255,255,0.03));
  border:1px solid var(--line); backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px);
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.06); }
.brandbar::after { content:""; position:absolute; left:18px; right:18px; bottom:0; height:1px;
  background: linear-gradient(90deg, transparent, var(--em) 25%, var(--gold) 75%, transparent); opacity:0.7; }
.brandbar .mark { width:40px; height:40px; border-radius:12px; display:grid; place-items:center; font-weight:800; font-size:1.3rem;
  color:#04130D; background: linear-gradient(140deg, #7FE0B8 0%, var(--em) 45%, var(--em-2) 100%);
  box-shadow: 0 0 0 1px rgba(127,224,184,0.55), 0 0 18px rgba(47,191,138,0.55), 0 0 42px rgba(47,191,138,0.25); }
.brandbar .left { display:flex; align-items:center; gap:12px; }
.brandbar .name { font-family:var(--head); font-size:1.3rem; font-weight:700; line-height:1.1; letter-spacing:-0.01em; }
.brandbar .name .ar { font-family:var(--ar); font-weight:700; color:var(--gold-2); }
.brandbar .sub { font-size:0.78rem; color:var(--muted); letter-spacing:0.02em; margin-top:1px; }
.brandbar .right { display:flex; flex-wrap:wrap; gap:8px; align-items:center; font-size:0.78rem; }
.brandbar .chip { background:var(--glass); border:1px solid var(--line); color:var(--ink-2); padding:5px 11px;
  border-radius:999px; white-space:nowrap; display:inline-flex; align-items:center; gap:7px; }
.brandbar .chip.clock { color:var(--ink); border-color: rgba(47,191,138,0.35); background: rgba(47,191,138,0.10); }
.live-dot { display:inline-block; width:7px; height:7px; border-radius:50%; background:var(--em); box-shadow:0 0 0 0 rgba(47,191,138,0.6);
  animation: livepulse 2.2s ease-out infinite; flex:0 0 7px; }
@keyframes livepulse { 0% { box-shadow:0 0 0 0 rgba(47,191,138,0.6); } 70% { box-shadow:0 0 0 7px rgba(47,191,138,0); }
  100% { box-shadow:0 0 0 0 rgba(47,191,138,0); } }

/* ---- Status pills, readable on dark --------------------------------------------------------------- */
.pill { display:inline-block; padding:2px 10px; border-radius:999px; font-size:0.74rem; font-weight:700; white-space:nowrap;
  border:1px solid transparent; line-height:1.5; }
.pill.pending { background:rgba(245,180,60,0.14); color:var(--amber); border-color:rgba(245,180,60,0.38); }
.pill.approved, .pill.completed { background:rgba(47,191,138,0.15); color:var(--em-3); border-color:rgba(47,191,138,0.42); }
.pill.rejected, .pill.action_needed { background:rgba(248,113,113,0.14); color:var(--red); border-color:rgba(248,113,113,0.40); }
.pill.changes_requested, .pill.partially_approved { background:rgba(251,146,60,0.14); color:var(--orange); border-color:rgba(251,146,60,0.40); }
.pill.in_review { background:rgba(56,189,248,0.13); color:var(--sky); border-color:rgba(56,189,248,0.38); }
.pill.sla-on_time { background:var(--glass-2); color:var(--ink-2); border-color:var(--line); }
.pill.sla-overdue { background:rgba(245,180,60,0.14); color:var(--amber); border-color:rgba(245,180,60,0.38); }
.pill.sla-escalate { background:rgba(248,113,113,0.14); color:var(--red); border-color:rgba(248,113,113,0.40); }

/* ---- Signed-in bar --------------------------------------------------------------------------------- */
.userbar { display:flex; align-items:center; gap:8px; font-size:0.86rem; color:var(--ink-2); justify-content:flex-end; padding-top:4px; }
.userbar b { color:var(--ink); }
.userbar .side { font-size:0.68rem; font-weight:800; letter-spacing:0.1em; text-transform:uppercase; padding:3px 10px; border-radius:999px; }
.userbar .side.participant { background:rgba(56,189,248,0.13); color:var(--sky); border:1px solid rgba(56,189,248,0.38); }
.userbar .side.admin { background:rgba(226,176,74,0.14); color:var(--gold-2); border:1px solid rgba(226,176,74,0.42); }
.conflict-box { border:1px solid rgba(251,146,60,0.40); background:rgba(251,146,60,0.10); color:var(--ink); border-radius:12px;
  padding:8px 12px; margin:6px 0; font-size:0.9rem; }

/* ---- Streamlit widgets on the dark stage ----------------------------------------------------------- */
[class*="st-key-glass"], [class*="st-key-door_"] { background: var(--glass) !important; border:1px solid var(--line) !important;
  border-radius:20px !important; backdrop-filter: blur(14px); -webkit-backdrop-filter: blur(14px);
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.05); }
.stButton button, [data-testid="stPopover"] button, [data-testid="stFormSubmitButton"] button {
  border-radius:12px !important; font-weight:600 !important; transition: all 0.15s ease; }
[data-testid="stBaseButton-secondary"], [data-testid="stPopoverButton"] { background: var(--glass) !important;
  border:1px solid var(--line-2) !important; color: var(--ink) !important; }
[data-testid="stBaseButton-secondary"]:hover:not(:disabled), [data-testid="stPopoverButton"]:hover {
  border-color: rgba(47,191,138,0.65) !important; background: rgba(47,191,138,0.10) !important;
  box-shadow: 0 0 0 1px rgba(47,191,138,0.25), 0 0 18px rgba(47,191,138,0.18); }
[data-testid="stBaseButton-secondary"]:disabled { opacity:0.45; }
[data-testid^="stBaseButton-primary"] { background: linear-gradient(135deg, #5AD7A6 0%, var(--em) 45%, #1FA373 100%) !important;
  border:1px solid rgba(127,224,184,0.6) !important; color:#03140D !important;
  box-shadow: 0 6px 22px rgba(47,191,138,0.28), inset 0 1px 0 rgba(255,255,255,0.35); }
[data-testid^="stBaseButton-primary"] p { color:#03140D !important; font-weight:700 !important; }
[data-testid^="stBaseButton-primary"]:hover { filter: brightness(1.07); box-shadow: 0 8px 28px rgba(47,191,138,0.42), inset 0 1px 0 rgba(255,255,255,0.35); }
[data-testid="stMetric"] { background: var(--glass); border:1px solid var(--line); border-radius:16px; padding:12px 16px;
  backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); }
[data-testid="stMetricLabel"] p { color: var(--muted) !important; font-weight:500; }
[data-testid="stMetricValue"] { font-family: var(--head); font-weight:700; color: var(--ink); }
[data-testid="stExpander"] details { background: rgba(255,255,255,0.035); border:1px solid var(--line) !important; border-radius:14px !important; }
[data-testid="stExpander"] summary { background: transparent !important; }
[data-testid="stExpander"] summary:hover { color: var(--em-3); }
[data-testid="stExpander"] summary p { color: var(--ink-2); font-weight:500; }
[data-testid="stDataFrame"] { border-radius:12px; overflow:hidden; }
[data-baseweb="tab-list"] { gap: 4px; }
[data-baseweb="tab"] p { font-weight:600; }
[data-testid="stAlert"] { border-radius:14px; }
code { border-radius:6px; }

/* ---- Hero (participant + sign-in) ------------------------------------------------------------------ */
.eyebrow-x { display:inline-flex; align-items:center; gap:8px; font-size:0.74rem; letter-spacing:0.16em; color:var(--gold-2);
  font-weight:700; text-transform:uppercase; }
.eyebrow-x::before { content:""; width:9px; height:9px; transform:rotate(45deg); border:1.5px solid var(--gold);
  box-shadow: 0 0 10px rgba(226,176,74,0.5); }
.hero-line { font-family:var(--head); font-size:3rem; font-weight:700; line-height:1.02; color:var(--ink); margin:0.35rem 0 0.4rem;
  letter-spacing:-0.025em; }
.hero-line .g, .grad { background: linear-gradient(95deg, #7FE0B8 0%, var(--em) 35%, var(--gold) 100%);
  -webkit-background-clip:text; background-clip:text; color:transparent; -webkit-text-fill-color: transparent;
  filter: drop-shadow(0 0 22px rgba(47,191,138,0.30)); }
.hero-ar { font-family:var(--ar); font-size:1.15rem; color:var(--gold-2); font-weight:600; direction:rtl; text-align:left; }
.hero-sub { color:var(--ink-2); font-size:0.98rem; line-height:1.55; margin:0.5rem 0 1rem; max-width:62ch; }
.hero-sub b { color: var(--ink); }

/* ---- Agent trace: a glowing vertical timeline ------------------------------------------------------ */
.trace { position:relative; border:1px solid var(--line); border-radius:22px; padding:16px 18px 6px;
  background: linear-gradient(180deg, rgba(255,255,255,0.06), rgba(255,255,255,0.025));
  backdrop-filter: blur(14px); -webkit-backdrop-filter: blur(14px); box-shadow: inset 0 1px 0 rgba(255,255,255,0.05); }
.trace h4 { display:flex; align-items:center; gap:8px; margin:0 0 14px !important; padding:0 !important; font-family:var(--body) !important;
  font-size:0.74rem !important; letter-spacing:0.16em; color:var(--em-3) !important; text-transform:uppercase; font-weight:700 !important; }
.trace h4 .live-dot { margin-right:9px; vertical-align:middle; position:relative; top:-1px; }
.step { display:flex; gap:14px; padding:0 0 14px; position:relative; }
.step .dot { flex:0 0 26px; height:26px; border-radius:50%; display:grid; place-items:center; font-size:0.8rem; font-weight:800;
  background:#0C1E17; color:#6F857C; border:1.5px solid rgba(255,255,255,0.16); z-index:1; }
.step:not(:last-child)::before { content:""; position:absolute; left:12px; top:26px; bottom:0; width:2px; background:rgba(255,255,255,0.09); }
.step.done .dot { background: linear-gradient(140deg, #7FE0B8, var(--em) 55%, var(--em-2)); color:#03140D; border-color:rgba(127,224,184,0.8);
  box-shadow: 0 0 12px rgba(47,191,138,0.65), 0 0 28px rgba(47,191,138,0.25); }
.step.done:not(:last-child)::before { background: linear-gradient(180deg, var(--em), rgba(47,191,138,0.55));
  box-shadow: 0 0 8px rgba(47,191,138,0.5); }
.step.active .dot { background:#0C1E17; color:var(--gold-2); border-color:var(--gold); animation: steppulse 1.8s ease-out infinite; }
@keyframes steppulse { 0% { box-shadow: 0 0 0 0 rgba(226,176,74,0.55); } 70% { box-shadow: 0 0 0 10px rgba(226,176,74,0); }
  100% { box-shadow: 0 0 0 0 rgba(226,176,74,0); } }
.step .t { font-weight:600; color:var(--ink); font-size:0.97rem; line-height:1.35; }
.step.active .t { color:var(--gold-2); }
.step.pending .t { color:#7F958B; font-weight:500; }
.step .d { font-size:0.83rem; color:var(--muted); margin-top:1px; }
.step .chips { margin-top:6px; display:flex; flex-wrap:wrap; gap:5px; }
.step .chips span { font-size:0.72rem; background:rgba(47,191,138,0.12); color:var(--em-3); border:1px solid rgba(47,191,138,0.32);
  border-radius:999px; padding:2px 9px; }
@media (prefers-reduced-motion: reduce) { .step.active .dot, .live-dot { animation:none !important; } }

/* Phone column: a soft emerald halo behind the device */
[data-testid="stColumn"]:has(iframe[title*="phone"]) { position:relative; }
[data-testid="stColumn"]:has(iframe[title*="phone"])::before { content:""; position:absolute; left:50%; top:46%; width:560px; height:760px;
  transform:translate(-50%,-50%); pointer-events:none; z-index:0;
  background: radial-gradient(closest-side, rgba(47,191,138,0.42), rgba(47,191,138,0.13) 55%, transparent 100%); filter: blur(10px); }
[data-testid="stColumn"]:has(iframe[title*="phone"]) > * { position:relative; z-index:1; }
iframe[title*="phone"] { background: transparent !important; color-scheme: light; }

/* Demo-script buttons as glass pills */
.demo-label { font-size:0.78rem; letter-spacing:0.14em; text-transform:uppercase; color:var(--muted); font-weight:700; margin:1.1rem 0 0.2rem; }
.demo-label b { color: var(--gold-2); }
.st-key-demo { gap:8px !important; }
.st-key-demo button { border-radius:999px !important; padding:4px 16px !important; min-height:38px !important;
  background: rgba(255,255,255,0.05) !important; border:1px solid rgba(255,255,255,0.16) !important; }
.st-key-demo button p { font-weight:600 !important; }

/* ---- Desk cards and the small ticket (legacy renderers) -------------------------------------------- */
.desk { border:1px solid var(--line); border-radius:12px; padding:8px 10px; margin:6px 0; background:var(--glass); }
.desk .hd { display:flex; align-items:center; gap:6px; font-weight:700; font-size:0.82rem; color:var(--ink); }
.desk .hd .st { margin-left:auto; font-size:0.68rem; font-weight:800; padding:2px 8px; border-radius:999px; }
.rtl .desk .hd .st { margin-left:0; margin-right:auto; }
.desk.ok { border-color:rgba(47,191,138,0.4); } .desk.ok .st { background:rgba(47,191,138,0.15); color:var(--em-3); }
.desk.missing { border-color:rgba(245,180,60,0.4); } .desk.missing .st { background:rgba(245,180,60,0.14); color:var(--amber); }
.desk.blocked { border-color:rgba(248,113,113,0.4); } .desk.blocked .st { background:rgba(248,113,113,0.14); color:var(--red); }
.desk.conflict { border-color:rgba(251,146,60,0.4); } .desk.conflict .st { background:rgba(251,146,60,0.14); color:var(--orange); }
.desk .bd { font-size:0.8rem; color:var(--ink-2); margin-top:4px; line-height:1.35; }
.desk .note { font-size:0.74rem; color:var(--sky); margin-top:3px; }
.intro { font-size:0.88rem; color:var(--ink); }
.tk { background:var(--glass); border:1px solid var(--line); border-radius:16px; padding:12px; margin-top:6px; }
.tk .top { display:flex; align-items:center; justify-content:space-between; }
.tk .id { font-family:var(--head); font-weight:700; font-size:1rem; color:var(--ink); }
.tk .lbl { font-size:0.66rem; letter-spacing:0.12em; color:var(--muted); font-weight:700; }
.tk .bar { display:flex; gap:4px; margin:10px 0 8px; }
.tk .bar span { flex:1; height:6px; border-radius:999px; background:rgba(255,255,255,0.12); transition: background 0.4s; }
.tk .bar span.approved { background:var(--em); box-shadow:0 0 8px rgba(47,191,138,0.6); } .tk .bar span.rejected { background:#F87171; }
.tk .bar span.changes_requested { background:#FB923C; }
.tk .row { display:flex; align-items:center; gap:8px; padding:5px 0; border-top:1px solid var(--line); font-size:0.8rem; color:var(--ink-2); }
.tk .row .who { font-size:0.68rem; color:var(--muted); }
.tk .row .pill { margin-left:auto; }
.rtl .tk .row .pill { margin-left:0; margin-right:auto; }
.tk .foot { font-size:0.74rem; color:var(--muted); margin-top:6px; }
.tk .done { margin-top:8px; background:linear-gradient(135deg, var(--em), var(--em-2)); color:#03140D; border-radius:10px; padding:8px 10px;
  font-weight:700; font-size:0.82rem; animation: pop 0.5s ease-out; }
@keyframes pop { from { transform: scale(0.96); opacity: 0; } to { transform: scale(1); opacity: 1; } }

/* ---- Page header + KPI cards ----------------------------------------------------------------------- */
.ph { margin: 0.4rem 0 0.4rem; }
.ph .eyebrow { display:inline-flex; align-items:center; gap:8px; font-size:0.74rem; letter-spacing:0.16em; color:var(--gold-2);
  font-weight:700; text-transform:uppercase; }
.ph .eyebrow::before { content:""; width:8px; height:8px; transform:rotate(45deg); border:1.5px solid var(--gold);
  box-shadow: 0 0 10px rgba(226,176,74,0.5); }
.ph h1 { font-family:var(--head) !important; font-size:2.5rem !important; font-weight:700 !important; margin:0.2rem 0 0 !important;
  padding:0 !important; color:var(--ink) !important; letter-spacing:-0.025em !important; line-height:1.08 !important; }
.ph p { color:var(--ink-2); margin:0.45rem 0 1rem; max-width:80ch; line-height:1.55; }
.kpis { display:grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap:14px; margin:0.6rem 0 1.1rem; }
.kpi { position:relative; overflow:hidden; background: linear-gradient(180deg, rgba(255,255,255,0.065), rgba(255,255,255,0.025));
  border:1px solid var(--line); border-radius:20px; padding:16px 18px 15px; backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); }
.kpi::before { content:""; position:absolute; left:0; right:0; top:0; height:2px;
  background: linear-gradient(90deg, var(--em), var(--gold)); opacity:0.8; }
.kpi::after { content:""; position:absolute; right:-40px; top:-60px; width:150px; height:150px; border-radius:50%;
  background: radial-gradient(closest-side, rgba(47,191,138,0.18), transparent); pointer-events:none; }
.kpi .l { font-size:0.82rem; color:var(--muted); font-weight:500; line-height:1.3; }
.kpi .v { font-family:var(--head); font-size:2.6rem; font-weight:700; line-height:1.05; margin-top:6px; letter-spacing:-0.02em;
  background: linear-gradient(95deg, #8FE6C2 0%, var(--em) 40%, var(--gold) 100%); -webkit-background-clip:text; background-clip:text;
  color:transparent; -webkit-text-fill-color:transparent; }
.kpi .w { font-size:0.82rem; color:var(--muted); margin-top:3px; }
.kpi .w s { color:#C2CFC9; text-decoration-color: rgba(248,113,113,0.8); text-decoration-thickness: 2px; }
.kpi .c { display:inline-block; margin-top:8px; font-size:0.74rem; font-weight:700; color:var(--em-3); background:rgba(47,191,138,0.13);
  border:1px solid rgba(47,191,138,0.35); padding:2px 9px; border-radius:999px; }
.kpi.plain .v { background:none; color:var(--ink); -webkit-text-fill-color: var(--ink); }
.expo-footer { color:var(--muted); font-size:0.74rem; border-top:1px solid var(--line); margin-top:2.2rem; padding-top:0.7rem; line-height:1.6; }
.expo-footer a { color:var(--ink-2); }
.sim-banner { background:rgba(226,176,74,0.09); border:1px solid rgba(226,176,74,0.35); color:var(--gold-2); padding:9px 14px;
  border-radius:14px; font-size:0.9rem; }
.sim-banner b { color:#FBE3A6; }

/* ---- Sign-in: two doors ---------------------------------------------------------------------------- */
.signin-hero { margin: 0.6rem 0 1.4rem; }
.signin-hero .hero-line { font-size:3.4rem; }
[class*="st-key-door_"] { padding: 22px 24px 18px !important; position:relative; overflow:hidden; }
[class*="st-key-door_"]::before { content:""; position:absolute; inset:0 0 auto 0; height:3px; }
.st-key-door_participant::before { background: linear-gradient(90deg, var(--em), #7FE0B8); }
.st-key-door_admin::before { background: linear-gradient(90deg, var(--gold), #F3D58E); }
.st-key-door_participant { box-shadow: 0 0 0 1px rgba(47,191,138,0.18), 0 20px 60px -20px rgba(47,191,138,0.35) !important; }
.st-key-door_admin { box-shadow: 0 0 0 1px rgba(226,176,74,0.16), 0 20px 60px -20px rgba(226,176,74,0.30) !important; }
.door-hd { display:flex; align-items:center; gap:14px; }
.door-ic { width:52px; height:52px; border-radius:16px; display:grid; place-items:center; flex:0 0 52px; }
.door-ic.p { background: linear-gradient(140deg, rgba(127,224,184,0.25), rgba(18,128,95,0.25)); border:1px solid rgba(47,191,138,0.5);
  color:#8FE6C2; box-shadow: 0 0 22px rgba(47,191,138,0.35); }
.door-ic.a { background: linear-gradient(140deg, rgba(243,213,142,0.22), rgba(226,176,74,0.12)); border:1px solid rgba(226,176,74,0.5);
  color:var(--gold-2); box-shadow: 0 0 22px rgba(226,176,74,0.28); }
.door-eye { font-size:0.7rem; letter-spacing:0.16em; text-transform:uppercase; font-weight:700; color:var(--muted); }
.door-t { font-family:var(--head); font-size:1.75rem; font-weight:700; color:var(--ink); line-height:1.1; }
.door-p { color:var(--ink-2); font-size:0.95rem; margin:0.7rem 0 0.4rem; }
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
        f'<span class="chip clock"><span class="live-dot"></span>{day} · {now:%a %d %b, %H:%M}{sim}</span></div></div>', unsafe_allow_html=True)


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
    with st.container(border=True, key=f"glass_tk_{ticket['id']}"):
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
