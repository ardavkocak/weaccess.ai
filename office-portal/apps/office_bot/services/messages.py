"""Discord mesaj sablonlarinin islenmesi — discord/messages.js'in Python portu."""
from __future__ import annotations

from datetime import date

from .date_utils import add_days, format_long_tr, today_iso

WEEKDAY_LABELS = [
    {"plain": "Pazartesi", "genitive": "Pazartesinin"},
    {"plain": "Salı", "genitive": "Salının"},
    {"plain": "Çarşamba", "genitive": "Çarşambanın"},
    {"plain": "Perşembe", "genitive": "Perşembenin"},
    {"plain": "Cuma", "genitive": "Cumanın"},
    {"plain": "Cumartesi", "genitive": "Cumartesinin"},
    {"plain": "Pazar", "genitive": "Pazarın"},
]


def day_label(target_iso: str, today: str | None = None):
    today = today or today_iso()
    if target_iso and target_iso == add_days(today, 1):
        return {"plain": "Yarın", "genitive": "Yarının"}
    weekday = date.fromisoformat(target_iso).weekday()  # Pazartesi=0
    return WEEKDAY_LABELS[weekday]


def build_mention(employee) -> str:
    discord_id = getattr(employee, "discord_user_id", None) or (employee.get("discord_user_id") if isinstance(employee, dict) else None)
    full_name = getattr(employee, "full_name", None) or (employee.get("full_name") if isinstance(employee, dict) else "")
    return f"<@{discord_id}>" if discord_id else full_name


def first_name(full_name: str) -> str:
    parts = str(full_name or "").strip().split()
    return parts[0] if parts else str(full_name or "")


def render_template(template: str, *, employee, duty_type, company: str = "", target_date: str | None = None) -> str:
    target_date = target_date or today_iso()
    day = day_label(target_date)
    full_name = getattr(employee, "full_name", None) or (employee.get("full_name") if isinstance(employee, dict) else "")
    emoji = getattr(duty_type, "emoji", None) or (duty_type.get("emoji") if isinstance(duty_type, dict) else "")
    duty_name = getattr(duty_type, "name", None) or (duty_type.get("name") if isinstance(duty_type, dict) else "")

    values = {
        "name": full_name,
        "first": first_name(full_name),
        "mention": build_mention(employee),
        "emoji": emoji or "",
        "duty": duty_name,
        "company": company,
        "date": format_long_tr(target_date),
        "gun": day["plain"],
        "gunUn": day["genitive"],
    }

    import re

    return re.sub(r"\{(\w+)\}", lambda m: str(values.get(m.group(1), m.group(0))), template)
