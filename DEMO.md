# Demo run-of-show (1:50 – 3:30 in the pitch)

**Setup before going on stage**
- `scripts/start.sh` (n8n + API + app), browser full screen at 1366 px or wider, zoom 100%.
- Optional second screen: n8n at http://localhost:5678 → Executions, to show the workflow runs live.
- Ticket tracker → Reset demo, so the ticket is MNJ-1001.
- Second browser window on **Desk console** (Logistics selected), ready to switch to.
- Backup video ready in case the laptop fails.

| Time | On screen | Say |
|---|---|---|
| 0:00 | Participant app, Home | "This is the Expo 2030 Riyadh app. France's pavilion team needs one thing tonight. Today that's three desks and three forms." |
| 0:10 | Tap **Start a request** → **① Request** | "They just say it, in English or Arabic." |
| 0:20 | Desk cards turn amber; trace steps 1–3 go green | "Munjiz split it into three desks and checked 17 rules in code. It knows Logistics needs a plate, Accreditation needs IDs, Facilities needs the load. So it asks **once**." |
| 0:40 | **② Answer** → three green cards | "It booked Gate L2 and a night slot, because heavy trucks only enter after visitor hours. It also issued contractor passes and sized a 63 A outlet. The participant typed the time once and every desk got it." |
| 1:00 | **Confirm and submit** → ticket MNJ-1001 | "One ticket. All three desks were notified at the same moment." |
| 1:05 | (optional) Point at trace step 6 | "n8n has already routed each part to that desk's own system: gate booking, accreditation, utilities. Those refs came back from them." |
| 1:10 | Switch to **Desk console** → Approve on each desk | "Each desk sees only its part, already checked. A person approves. The AI prepares, humans decide." |
| 1:30 | Back to the app: ticket **Done**, trace 7/7 | "Done in under a minute. From one message." |
| 1:40 | (optional) **Rule demo** | "Ask for a truck at 3 pm while the Expo is open, and the rule stops it before any desk wastes time." |

Then go to **Organiser dashboard** for the impact section (3:30 – 4:05): the before→after cards, then the
"At Expo 2030 Riyadh scale" numbers. Say clearly that the data is simulated and that the 197 participants is the
organisers' public figure.

**If anything fails on stage:** the offline parser needs no internet. If the app itself fails, switch to the
backup video and keep talking.
