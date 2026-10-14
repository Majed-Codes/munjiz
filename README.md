# Munjiz · منجز

**One request. One ticket. Done.** A prototype for **Expo 2030 Riyadh**, challenge 5.5.

Expo 2030 Riyadh runs 1 Oct 2030 – 31 Mar 2031 on a ~6 km² site north of Riyadh, and organisers expect
197 participating countries ([BIE](https://www.bie-paris.org/site/en/2030-riyadh),
[Swiss Federal Council](https://www.admin.ch/en/newnsb/U5jT34vgqmGSHnWNihoPw)). Each participant's pavilion team
and its contractors deal with several service desks for everyday requests. Munjiz is their single window.

A participant describes a request once, in English or Arabic. Munjiz splits it into one sub-request per desk
(Logistics & Site Access, Accreditation & Security, Facilities & Utilities), checks each desk's rules in code, asks once for anything
missing, shows a summary to confirm, and submits everything under one ticket. Desk staff approve with one click.
Organisers see the impact on a dashboard.

## Run

```bash
pip install -r requirements.txt
scripts/n8n_setup.sh             # first time only: .env + token, start n8n in Docker, import and activate workflows
scripts/start.sh                 # n8n + Munjiz API (:8000) + app (:8501)
```

Without Docker, `streamlit run app.py` alone still runs the whole demo; the n8n integration simply stays off
(leave `N8N_WEBHOOK_URL` empty in `.env`).

Open the **Participant app (Munjiz)** page in one window and **Desk staff console** in another; approvals show up live.

Terminal version of Scenario A:

```bash
python cli.py --demo       # English
python cli.py --demo-ar    # Arabic
python cli.py              # type your own
```

Tests: `python -m pytest -q` (17 tests, including the n8n event and API contract)

## How it works

| Step | Where |
|---|---|
| Extract the request into structured fields | `munjiz/extract_local.py` (offline, default) or `munjiz/extract_claude.py` (one tool per desk) |
| Split into desk sub-requests; shared facts (time, pavilion) said once and copied to every desk | `munjiz/agent.py` → `split()` |
| Check each desk's rules: required fields, notice period, time windows, limits, ID formats | `rules/*.yaml` + `munjiz/rules.py` |
| Ask once for what's missing, or show the summary | `munjiz/agent.py` → `compose_reply()` |
| One ticket, sub-requests, approvals, event log | `munjiz/tickets.py`, `munjiz/db.py` (SQLite) |
| Simulated before/after data | `munjiz/simulate.py` (assumptions at the top) |
| UI: participant chat, staff console, tracker, dashboard | `app.py`, `views/` |

The LLM only extracts. Rules, follow-up questions and summaries are produced by code, so a bad model
output can't skip a rule, and the human approval step is always there.

## n8n integration

n8n is the integration layer between Munjiz and each desk's own systems. Munjiz never calls desk systems
directly: it sends one event per change, and n8n routes it. Swapping a mock desk for a real system is an n8n
change, not a Munjiz change.

```
Participant app ──► Munjiz (agent + rules + one ticket) ──event──► n8n ──► Logistics system  (gate booking)
                         ▲                                           ├──► Accreditation system
                         │                                           ├──► Utilities work orders
                         └──── decisions ◄── n8n desk-decision ◄─────┴──► desk alerts · participant updates
```

| Workflow (in `n8n/workflows/`) | Trigger | What it does |
|---|---|---|
| Munjiz · Route ticket to desks | webhook `munjiz-events` | `ticket_submitted`: one item per desk part → each desk's system (returns its ref, e.g. GATE-1001) → desk alert. `sub_decided` / `ticket_completed`: participant update in their language |
| Munjiz · SLA watchdog | every 5 min | asks Munjiz for parts waiting > 30 min and escalates them to the desk supervisor |
| Munjiz · Desk decision intake | webhook `desk-decision` | a desk approves or rejects from its own tools (Slack button, email link, its system) → Munjiz decision API |

- Events: `ticket_submitted`, `sub_decided`, `ticket_completed` (`munjiz/events.py`). Delivery is logged on the
  ticket (`n8n_sent` / `n8n_failed`); if n8n is down the app carries on.
- API for n8n (`munjiz/api.py`, port 8000): `GET /health`, `GET /api/tickets/{id}`,
  `GET /api/subrequests/pending?older_than_minutes=30`, `POST /api/subrequests/{id}/decision`,
  `POST /mock/desks/{desk}/inbox`. Write calls need `X-Munjiz-Token` (generated into `.env`).
- Notification steps are No-op placeholders labelled "Connect Slack, Teams or email here" / "Connect Expo
  app push or WhatsApp here": add credentials in n8n to make them real.
- Edit the workflows in `n8n/make_workflows.py` and re-run `scripts/n8n_setup.sh`, or edit them in the n8n
  editor at http://localhost:5678 (create the owner account on first visit).

Try a desk approving through n8n:

```bash
curl -X POST localhost:5678/webhook/desk-decision -H 'Content-Type: application/json' -d '{"sub_id":"LOG-1001","approve":true,"staff":"logistics.officer"}'
```

## Expo 2030 Riyadh context

- `munjiz/expo.py`: event dates, phases (build-up, open to visitors, dismantling), participants and sources.
- **Participants:** official participants (countries, international organisations) and non-official participants
  (companies). The countries in the sign-in list have publicly confirmed or signed participation; the others are
  placeholders.
- **Desks:** Logistics & Site Access, Accreditation & Security, Facilities & Utilities. Their rules, gates and
  plots are **simulated**, modelled on how World Expos usually run participant services. Replace them with
  Expo 2030 Riyadh's Special Regulations and site plan when available.
- **Phase-aware rules:** while the Expo is open to visitors, heavy trucks enter only 22:00–06:00; during build-up
  they can come at any time.
- **Expo clock:** the demo moves today's real time of day to Expo day 48 (Sun 17 Nov 2030), so "tomorrow" is a
  day of the Expo. `MUNJIZ_CLOCK=real` uses today's date; `MUNJIZ_EXPO_DATE=2030-06-01` puts the demo in build-up.
- **In-app feature:** the participant page shows Munjiz inside a phone mock-up of the Expo 2030 Riyadh app
  (Home → Munjiz → My requests), next to other app features it doesn't build. Presenter controls sit beside
  the phone. The staff console and dashboard are back-office web screens. The phone is a concept mock-up, not
  the official app, and uses no official logo.
- **Dashboard:** an "At Expo 2030 Riyadh scale" section projects the savings to 197 participants. Only the
  participant count is a public figure; the other inputs are assumptions you can change on screen.

The app says on every page that it is a hackathon prototype and not an official Expo service.

## Agent backends

- **Offline parser** (default, `MUNJIZ_BACKEND=local`): free and deterministic. It covers the demo
  scenarios, not every way of phrasing a request.
- **Claude** (`MUNJIZ_BACKEND=claude`, or pick it in the sidebar): needs `ANTHROPIC_API_KEY`. Uses
  `claude-opus-5-5` with server-side refusal fallback enabled. Each response is cached in `data/llm_cache/`
  by transcript, so a rehearsed demo replays with no API call. If the call fails on stage, the app falls back
  to the offline parser.

## Demo scripts

In **Presenter controls → Demo scripts** next to the phone:

1. Scenario A (English or Arabic) → follow-up question for plate, workers' IDs and kW
2. Follow-up answer → summary with gate, route, permit and power connection → Confirm
3. Rule demo: a heavy truck at 3 pm is blocked (while the Expo is open, heavy vehicles only 22:00–06:00)

Reset demo tickets from **Ticket tracker → Reset demo** (the simulated history stays).

## Simulated data

The dashboard data is synthetic and labelled as such. Every number comes from `ASSUMPTIONS` in
`munjiz/simulate.py`. Replace them with figures from the organisers or mentors.
