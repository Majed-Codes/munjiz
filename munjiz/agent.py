"""One conversational turn: extract → split per desk → rule check → follow-up or summary."""
from dataclasses import dataclass
from datetime import datetime

from . import config, expo, extract_local
from .i18n import detect_lang, fmt_dt, t
from .rules import DeskCheck, check_desk, load_rules


@dataclass
class AgentResult:
    language: str
    checks: dict[str, DeskCheck]
    reply: str

    @property
    def ready(self) -> bool:
        return bool(self.checks) and all(c.ok for c in self.checks.values())


def pick(value, lang: str):
    """Rule-file values are either plain or {en, ar}."""
    return value.get(lang, value.get("en")) if isinstance(value, dict) and "en" in value else value


def extract(conversation: list[dict], pavilion: str, now: datetime, backend: str) -> dict:
    if backend == "claude":
        from . import extract_claude
        return extract_claude.extract(conversation, pavilion, now)
    return extract_local.extract([m["content"] for m in conversation if m["role"] == "user"], now)


def split(raw: dict, pavilion: str) -> dict[str, dict]:
    """One sub-request per desk. Shared facts (time, pavilion) are given once and copied to every desk."""
    subs = {desk: dict(payload) for desk, payload in raw.items() if payload is not None}
    when = (subs.get("logistics", {}).get("arrival_datetime")
            or subs.get("security", {}).get("access_datetime")
            or subs.get("facilities", {}).get("needed_from"))
    if "logistics" in subs:
        subs["logistics"].setdefault("arrival_datetime", when)
        if subs["logistics"]["arrival_datetime"]:  # some site rules depend on the Expo phase
            subs["logistics"]["phase"] = expo.phase(datetime.fromisoformat(subs["logistics"]["arrival_datetime"]))
    if "security" in subs:
        subs["security"].setdefault("access_datetime", when)
        if subs["security"].get("workers") and subs["security"].get("worker_count") is None:
            subs["security"]["worker_count"] = len(subs["security"]["workers"])
    if "facilities" in subs:
        subs["facilities"].setdefault("needed_from", when)
        subs["facilities"].setdefault("service", "power_connection")
    for payload in subs.values():
        payload["pavilion"] = pavilion
    return subs


def desk_title(desk: str, lang: str) -> str:
    rules = load_rules()[desk]
    return f"{rules['icon']} {rules['title'][lang]}"


def describe(check: DeskCheck, lang: str) -> str:
    """One-line human summary of a desk's sub-request and what the desk will assign."""
    p, a, fields = check.payload, {k: pick(v, lang) for k, v in check.assigned.items()}, load_rules()[check.desk]["fields"]
    comma = "، " if lang == "ar" else ", "
    if check.desk == "logistics":
        vehicle = fields["vehicle_type"]["values"].get(p.get("vehicle_type"), {}).get(lang, "—")
        slot = f"{a['slot_minutes']} {'دقيقة' if lang == 'ar' else 'min slot'}"
        return (f"{vehicle} · {p.get('vehicle_plate', '—')} · {p.get('cargo_description', '—')} · "
                f"{fmt_dt(p.get('arrival_datetime'), lang)} → **{a['gate']}**{comma}{a['route']} ({slot})")
    if check.desk == "security":
        people = comma.join(f"{w['full_name']} ({w['id_number']})" for w in p.get("workers", []))
        count = f"عدد العمال {p.get('worker_count', 0)}" if lang == "ar" else f"{p.get('worker_count', 0)} workers"
        return f"{count}: {people} → **{a['permit_type']}**{comma}{a['badge_pickup']}"
    if check.desk == "facilities":
        service = fields["service"]["values"][p["service"]][lang]
        kw = f"{p['power_kw']:g} {'كيلوواط' if lang == 'ar' else 'kW'}" if p.get("power_kw") is not None else "—"
        since = "من" if lang == "ar" else "from"
        return f"{service} · {kw} {since} {fmt_dt(p.get('needed_from'), lang)} → **{a['connection']}**"
    return str(p)


def compose_reply(checks: dict[str, DeskCheck], lang: str) -> str:
    if not checks:
        return t("nothing_understood", lang)

    missing = [(d, i) for d, c in checks.items() for i in c.blocking if i.kind == "missing"]
    problems = [(d, i) for d, c in checks.items() for i in c.blocking if i.kind == "rule"]
    if missing or problems:
        lines = []
        if missing:
            lines.append(t("followup_intro", lang))
            for n, (desk, issue) in enumerate(missing, 1):
                ask = issue.message[lang]
                count = checks[desk].payload.get("worker_count")
                if issue.field == "workers" and count:
                    ask += f" ({t('for_workers', lang, n=count)})"
                lines.append(f"{n}. {ask}  ·  _{load_rules()[desk]['title'][lang]}_")
        if problems:
            lines.append("" if not missing else "\n" + t("problems_intro", lang))
            lines += [f"- ⚠️ {issue.message[lang]}" for _, issue in problems]
        return "\n".join(lines).strip()

    lines = [t("summary_intro", lang), ""]
    for desk, check in checks.items():
        lines.append(f"- **{desk_title(desk, lang)}**: {describe(check, lang)}")
        lines += [f"  - ℹ️ {i.message[lang]}" for i in check.notes]
    lines += ["", t("summary_outro", lang)]
    return "\n".join(lines)


def run_turn(conversation: list[dict], pavilion: str, now: datetime | None = None,
             backend: str | None = None) -> AgentResult:
    now = now or config.now()
    last_user = next(m["content"] for m in reversed(conversation) if m["role"] == "user")
    lang = detect_lang(last_user)
    raw = extract(conversation, pavilion, now, backend or config.BACKEND)
    checks = {desk: check_desk(desk, payload, now) for desk, payload in split(raw, pavilion).items()}
    return AgentResult(language=lang, checks=checks, reply=compose_reply(checks, lang))
