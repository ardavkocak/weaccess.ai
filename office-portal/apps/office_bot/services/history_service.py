"""Gorev gecmisi servisi — history.service.js'in Python portu."""
from __future__ import annotations

from django.db.models import Count, Max

from ..models import DutyHistory
from .date_utils import format_long_tr, format_short_tr, is_today, today_iso


def record(*, duty_type_id, employee, date=None, source="cron", notified=False, consumed_turn=False):
    date = date or today_iso()
    DutyHistory.objects.update_or_create(
        duty_type_id=duty_type_id,
        duty_date=date,
        defaults={
            "employee_id": employee.id,
            "employee_name": employee.full_name,
            "source": source,
            "notified": 1 if notified else 0,
            "consumed_turn": 1 if consumed_turn else 0,
        },
    )


def list_history(duty_type_id=None, date_from=None, date_to=None, page=1, page_size=20):
    qs = DutyHistory.objects.select_related("duty_type")
    if duty_type_id:
        qs = qs.filter(duty_type_id=duty_type_id)
    if date_from:
        qs = qs.filter(duty_date__gte=date_from)
    if date_to:
        qs = qs.filter(duty_date__lte=date_to)

    total = qs.count()
    total_pages = max(1, -(-total // page_size))
    safe_page = min(max(1, page), total_pages)

    rows = list(qs.order_by("-duty_date", "-id")[(safe_page - 1) * page_size: safe_page * page_size])
    enriched = [{
        "row": row,
        "date_long": format_long_tr(row.duty_date),
        "date_short": format_short_tr(row.duty_date),
        "is_today": is_today(row.duty_date),
        "is_stand_in": row.consumed_turn == 0,
    } for row in rows]

    return {"rows": enriched, "total": total, "page": safe_page, "page_size": page_size, "total_pages": total_pages}


def get_recent(limit=5):
    return list_history(page=1, page_size=limit)["rows"]


def get_stats_by_employee(duty_type_id=None):
    qs = DutyHistory.objects.all()
    if duty_type_id:
        qs = qs.filter(duty_type_id=duty_type_id)
    return list(
        qs.values("employee_name")
        .annotate(duty_count=Count("id"), last_duty=Max("duty_date"))
        .order_by("-duty_count", "employee_name")
    )


def get_total_count():
    return DutyHistory.objects.count()
