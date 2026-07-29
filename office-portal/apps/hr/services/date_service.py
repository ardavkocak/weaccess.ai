"""Tarih kurallari — ik-otomasyon/src/services/date.service.js'in Python portu."""
from __future__ import annotations

from datetime import date, timedelta
import calendar as _calendar


def last_friday(year: int, month: int) -> date:
    """Belirtilen ayin (1-12) son cuma gunu."""
    last_day = date(year, month, _calendar.monthrange(year, month)[1])
    days_since_friday = (last_day.weekday() - 4) % 7  # Python: Pazartesi=0 .. Cuma=4
    return last_day - timedelta(days=days_since_friday)


def move_weekend_reminder_to_friday(d: date) -> date:
    if d.weekday() == 5:  # Cumartesi
        return d - timedelta(days=1)
    if d.weekday() == 6:  # Pazar
        return d - timedelta(days=2)
    return d


def birthday_reminder_date(year: int, month: int) -> date:
    return move_weekend_reminder_to_friday(last_friday(year, month) - timedelta(days=2))


def anniversary_date(hire_date: date, year: int) -> date:
    if hire_date.month == 2 and hire_date.day == 29:
        try:
            return date(year, 2, 29)
        except ValueError:
            return date(year, 2, 28)
    return date(year, hire_date.month, hire_date.day)


def anniversary_reminder_date(anniversary: date) -> date:
    return move_weekend_reminder_to_friday(anniversary - timedelta(days=2))
