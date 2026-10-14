"""Expo 2030 Riyadh context: public facts (with sources), phases, participants.

Facts are public figures checked on 2026-10-13. Desk rules, gates and plots in this prototype are SIMULATED,
modelled on how World Expos usually run participant services; swap in Expo 2030 Riyadh's Special
Regulations and site plan when the organisers share them.
"""
from datetime import date, datetime

NAME = {"en": "Expo 2030 Riyadh", "ar": "إكسبو 2030 الرياض"}
THEME = "The Era of Change: Together for a Foresighted Tomorrow"  # English only; no official Arabic wording checked
OPENS = date(2030, 10, 1)
CLOSES = date(2031, 3, 31)
DAYS = (CLOSES - OPENS).days + 1  # 182

FACTS = {
    "expected_participating_countries": 197,  # organisers' expectation (Swiss Federal Council notice, Apr 2026)
    "expected_visits_millions": 42,           # BIE estimate
    "site_km2": 6,                            # ~6 km² site north of Riyadh, near King Khalid International Airport
}
SOURCES = [
    ("BIE: Expo 2030 Riyadh", "https://www.bie-paris.org/site/en/2030-riyadh"),
    ("Swiss Federal Council: participation decision", "https://www.admin.ch/en/newnsb/U5jT34vgqmGSHnWNihoPw"),
    ("Expo 2030 Riyadh news hub", "https://www.expo2030riyadh.sa/news-hub/commissioner-general-expo-2030-riyadh-heads-saudi-delegation-bie-paris"),
]

# Who files requests. Countries listed have publicly confirmed or signed participation (2026);
# the organisation and corporate entries are placeholders.
PARTICIPANTS = {
    "France Pavilion": "Official participant · Country",
    "Bahrain Pavilion": "Official participant · Country",
    "Oman Pavilion": "Official participant · Country",
    "Switzerland Pavilion": "Official participant · Country",
    "International Organisation Pavilion (example)": "Official participant · International organisation",
    "Corporate Pavilion (example)": "Non-official participant · Company",
}
ROLES = ["Pavilion director", "Commissioner General's office", "Pavilion operations lead",
         "Contractor for the pavilion"]


def phase(when: datetime | date) -> str:
    d = when.date() if isinstance(when, datetime) else when
    if d < OPENS:
        return "build_up"
    return "operations" if d <= CLOSES else "dismantling"


PHASE_LABEL = {
    "build_up": {"en": "Build-up", "ar": "مرحلة التجهيز"},
    "operations": {"en": "Open to visitors", "ar": "مفتوح للزوار"},
    "dismantling": {"en": "Dismantling", "ar": "مرحلة التفكيك"},
}


def expo_day(when: datetime) -> int | None:
    return (when.date() - OPENS).days + 1 if phase(when) == "operations" else None
