"""
Tarih yardimcilari — ofis-gorev-takibi/src/utils/date.js'in Python portu.

Orijinal JS kodu tum hesaplari ofis saat diliminde (Europe/Istanbul) yapar.
Python tarafinda ayni sonucu almak icin zoneinfo kullanilir.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

OFFICE_TZ = ZoneInfo("Europe/Istanbul")

_AY_ADLARI = [
    "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
    "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık",
]
_GUN_ADLARI = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]


def today_iso() -> str:
    """Ofis saat diliminde bugunun tarihi ('YYYY-MM-DD')."""
    return datetime.now(OFFICE_TZ).date().isoformat()


def now_hhmm() -> str:
    """Ofis saat diliminde su anki saat ('HH:MM')."""
    return datetime.now(OFFICE_TZ).strftime("%H:%M")


def parse_iso(value: str) -> date:
    return date.fromisoformat(value)


def add_days(iso_date: str, days: int) -> str:
    return (date.fromisoformat(iso_date) + timedelta(days=days)).isoformat()


def format_long_tr(iso_date: str) -> str:
    """'2026-07-17' -> '17 Temmuz 2026 Cuma'"""
    d = date.fromisoformat(iso_date)
    return f"{d.day} {_AY_ADLARI[d.month - 1]} {d.year} {_GUN_ADLARI[d.weekday()]}"


def format_short_tr(iso_date: str) -> str:
    """'2026-07-17' -> '17.07.2026'"""
    d = date.fromisoformat(iso_date)
    return f"{d.day:02d}.{d.month:02d}.{d.year}"


def is_today(iso_date: str) -> bool:
    return iso_date == today_iso()


def next_working_day(iso_date: str) -> str:
    """Cumartesi/Pazari atlayan bir sonraki is gunu (basit tatil desteksiz surum)."""
    current = date.fromisoformat(iso_date)
    current += timedelta(days=1)
    while current.weekday() >= 5:  # 5=Cumartesi, 6=Pazar
        current += timedelta(days=1)
    return current.isoformat()


def previous_working_day(iso_date: str) -> str:
    """Cumartesi/Pazari atlayan bir onceki is gunu (Pazartesi -> onceki Cuma)."""
    current = date.fromisoformat(iso_date)
    current -= timedelta(days=1)
    while current.weekday() >= 5:
        current -= timedelta(days=1)
    return current.isoformat()
