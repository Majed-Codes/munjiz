"""Desk rule engine. Each desk's rules live in rules/<desk>.yaml and are checked here, in code."""
import re
from dataclasses import dataclass, field
from datetime import datetime, time
from functools import cache

import yaml

from .config import DESKS, RULES_DIR


@dataclass
class Issue:
    desk: str
    field: str
    kind: str  # "missing" | "rule"
    severity: str  # "block" | "note"
    message: dict  # {"en": ..., "ar": ...}
    check_id: str = ""


@dataclass
class DeskCheck:
    desk: str
    payload: dict
    assigned: dict = field(default_factory=dict)
    issues: list[Issue] = field(default_factory=list)

    @property
    def blocking(self) -> list[Issue]:
        return [i for i in self.issues if i.severity == "block"]

    @property
    def notes(self) -> list[Issue]:
        return [i for i in self.issues if i.severity == "note"]

    @property
    def ok(self) -> bool:
        return not self.blocking


@cache
def load_rules() -> dict[str, dict]:
    return {d: yaml.safe_load((RULES_DIR / f"{d}.yaml").read_text(encoding="utf-8")) for d in DESKS}


def _empty(v) -> bool:
    return v is None or v == "" or v == []


def _matches(cond: dict | None, payload: dict) -> bool:
    for key, expected in (cond or {}).items():
        actual = payload.get(key)
        if isinstance(expected, dict):
            if actual is None:
                return False
            ops = {"lte": actual <= expected.get("lte", actual), "gte": actual >= expected.get("gte", actual),
                   "lt": "lt" not in expected or actual < expected["lt"],
                   "gt": "gt" not in expected or actual > expected["gt"]}
            if not all(ops.values()):
                return False
        elif actual != expected:
            return False
    return True


def _in_window(dt: datetime, start: str, end: str) -> bool:
    s, e, t = time.fromisoformat(start), time.fromisoformat(end), dt.time()
    return s <= t <= e if s <= e else (t >= s or t <= e)


def _violates(check: dict, payload: dict, now: datetime) -> bool:
    value = payload.get(check["field"])
    if _empty(value) or not _matches(check.get("when"), payload):
        return False
    kind = check["type"]
    if kind == "min_notice_hours":
        return (datetime.fromisoformat(value) - now).total_seconds() < check["hours"] * 3600
    if kind == "time_window":
        return not _in_window(datetime.fromisoformat(value), check["start"], check["end"])
    if kind == "max_value":
        return float(value) > check["value"]
    if kind == "count_match":
        expected = payload.get(check["count_field"])
        return expected is not None and len(value) != expected
    if kind == "item_pattern":
        pat = re.compile(check["pattern"])
        return any(not pat.match(str(item.get(check["item_field"], "")).upper().replace(" ", "")) for item in value)
    raise ValueError(f"unknown check type {kind}")


def check_desk(desk: str, payload: dict, now: datetime) -> DeskCheck:
    rules = load_rules()[desk]
    result = DeskCheck(desk=desk, payload=payload)

    for name in rules["required"]:
        spec = rules["fields"][name]
        value = payload.get(name)
        incomplete = spec.get("type") == "list" and not _empty(value) and any(
            any(_empty(item.get(f)) for f in spec["item_fields"]) for item in value)
        if _empty(value) or incomplete:
            result.issues.append(Issue(desk, name, "missing", "block", spec["ask"]))

    for check in rules.get("checks", []):
        if _violates(check, payload, now):
            result.issues.append(Issue(desk, check["field"], "rule", check["severity"], check["message"], check["id"]))

    for rule in rules.get("assign", []):
        if _matches(rule.get("when"), payload):
            result.assigned = dict(rule["set"])
            break
    return result
