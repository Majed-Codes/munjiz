# Demo run-of-show (1:50 – 3:30 in the pitch)

**Setup before going on stage**
- `scripts/start.sh` (n8n + API + app), browser full screen at 1366 px or wider, zoom 100%.
- **Window 1 · Participant:** sign in → **Demo accounts (prototype)** → **France** (or type the pavilion code
  `FRA-2030`; the account id in the link is `p-france`, the code is never in the URL).
- **Window 2 · Expo Admin:** sign in → **Accreditation** (desk staff, PIN `2030`). Keep a third tab signed in as
  **Logistics** and one as **Facilities**, or sign in as **Supervisor** and use the desk switcher.
- Organiser tab (sign in → **Organiser**) → Ticket tracker → Reset demo, so no old tickets show. Ticket numbers
  keep counting after a reset (they are never reused), so the demo ticket is the next number, e.g. MNJ-1004.
- After a server restart everyone signs in again unless `MUNJIZ_API_TOKEN` is set in `.env`.
- Optional: n8n at http://localhost:5678 → Executions, to show the workflow runs live.
- Backup video ready in case the laptop fails.

| Time | On screen | Say |
|---|---|---|
| 0:00 | Window 1, Participant app | "Two sides, one ticket. This is the participant side: France's pavilion team in the Expo 2030 Riyadh app. Today one request means three desks and three forms." |
| 0:10 | **① Request** | "They just say it, in English or Arabic." |
| 0:20 | Cards turn amber; trace steps 1–4 | "Munjiz split it into three desks, checked 17 desk rules and 4 clash checks in code, and asks **once** for the plate, the IDs and the kW." |
| 0:35 | **② Answer** → three green cards → **Confirm** | "Gate L2 and a night slot, contractor passes, a 63 A outlet. One ticket, three desks notified at once." |
| 0:50 | Window 2, Accreditation desk console | "This is the Expo Admin side. The desk sees only its part, already checked against its rules and the other desks' parts." |
| 1:00 | **Send back to the participant** → "John Smith's ID could not be verified" → **Request a change**; approve Logistics and Facilities | "A person decides. Here one passport needs fixing." |
| 1:10 | Window 1: Munjiz says which part came back; ticket **Partially approved** | "The other parts stay approved. Munjiz asks for that part only." |
| 1:15 | **Fix: new passport** → **Send the fix** | "Only the security part (SEC-…) goes back, as version 2, on the same ticket." |
| 1:25 | Window 2: v2 → **Approve**; Window 1: **Done** | "One request, one ticket, done, even with a correction." |
| 1:35 | **↺ New request** → **🔀 Clash demo** | "Every desk says yes on its own, but the truck may only come at night and the utility crews stop at 23:00. Munjiz catches the clash before any desk wastes time, and suggests the fix." Tap **Apply the suggested fix**, then **Confirm & send to 3 desks**. Leave this second ticket pending: the SLA step uses it. |

Then (3:30 – 4:05):
- **SLA:** sign in as **Supervisor** → SLA & escalations → open **Presenter control · SLA demo** at the bottom →
  **⏩ +300 min** (it ages every part still waiting, i.e. the clash ticket's three parts). Within 3 seconds the
  Logistics and Facilities parts appear under **Escalated to you** (their target is 120 min, escalation 240) and the
  Security part under **Reminder sent to the desk** (240 / 480). "Each desk has a response target. Late parts get
  a reminder, then reach the supervisor, who can reassign or decide." Optionally **👤 Reassign** one part.
  (Nothing to show here if no ticket is waiting: the step needs the pending clash ticket from 1:35.)
- **Organiser dashboard**: the before→after cards, SLA breaches by desk, clashes caught, then the "At Expo 2030
  Riyadh scale" numbers. Say clearly that the data is simulated and that 197 participants is the organisers' public figure.
- (optional) **Desk rules**: "Organisers change a rule here, with no code, and every change is logged."

**Starting over in the participant window:** **↺ New request** (or the phone's Home → New request) always starts
a fresh request, even while another ticket waits for a fix. To go back to a ticket a desk sent back, use
**↪ Continue fixing MNJ-…** under the demo scripts, or the phone's Requests tab → the ticket → **Fix this request**.
Right after sign-in Munjiz reopens a ticket that waits for a fix once, by itself.

**If anything fails on stage:** the offline parser needs no internet. If the app itself fails, switch to the
backup video and keep talking.
