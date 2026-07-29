"""Yemek menusu servisi — mealMenu.service.js'in Python portu."""
from __future__ import annotations

import json

from ..models import MealMenu
from .date_utils import format_long_tr, format_short_tr, next_working_day, today_iso

DAY_NAMES = ["Pazar", "Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi"]


def _normalize_item(item):
    if isinstance(item, str):
        name = item.strip()
        return {"name": name, "kcal": None} if name else None
    if isinstance(item, dict) and str(item.get("name") or "").strip():
        kcal = item.get("kcal")
        kcal = kcal if isinstance(kcal, (int, float)) and kcal > 0 else None
        return {"name": item["name"].strip(), "kcal": kcal}
    return None


def _day_name_of(iso_date):
    from datetime import date

    d = date.fromisoformat(iso_date)
    # Python Monday=0..Sunday=6; DAY_NAMES JS getUTCDay() Sunday=0 tabanlidir.
    return DAY_NAMES[(d.weekday() + 1) % 7]


def _hydrate(row):
    if not row:
        return None
    try:
        parsed = json.loads(row.items)
        items = [i for i in (_normalize_item(x) for x in parsed) if i] if isinstance(parsed, list) else []
    except (json.JSONDecodeError, TypeError):
        items = []

    return {
        "row": row,
        "items": items,
        "day_name": row.day_name or _day_name_of(row.menu_date),
        "date_long": format_long_tr(row.menu_date),
        "date_short": format_short_tr(row.menu_date),
        "is_announced": bool(row.announced_at),
    }


def get_by_date(menu_date):
    return _hydrate(MealMenu.objects.filter(menu_date=menu_date).first())


def next_menu_date_iso():
    return next_working_day(today_iso())


def get_next_menu():
    return get_by_date(next_menu_date_iso())


def list_menus(upcoming_only=False, limit=None):
    qs = MealMenu.objects.all()
    if upcoming_only:
        qs = qs.filter(menu_date__gte=today_iso())
    qs = qs.order_by("menu_date")
    if limit:
        qs = qs[:limit]
    return [_hydrate(row) for row in qs]


def save_rows(rows, source_file=None, replace_all=False):
    removed = 0
    if replace_all:
        removed = MealMenu.objects.all().delete()[0]

    inserted = updated = 0
    for row in rows:
        existed = not replace_all and MealMenu.objects.filter(menu_date=row["menu_date"]).exists()
        MealMenu.objects.update_or_create(
            menu_date=row["menu_date"],
            defaults={
                "day_name": row.get("day_name") or "",
                "items": json.dumps(row.get("items") or [], ensure_ascii=False),
                "source_file": source_file,
                "announced_at": None,
            },
        )
        if existed:
            updated += 1
        else:
            inserted += 1

    return {"inserted": inserted, "updated": updated, "removed": removed}


def remove_by_date(menu_date):
    return MealMenu.objects.filter(menu_date=menu_date).delete()[0] > 0


def remove_all():
    return MealMenu.objects.all().delete()[0]


def get_last_announced_date():
    """En son GERÇEKTEN duyurulan menünün tarihi (mealMenu.service.js'in Node portu)."""
    row = (
        MealMenu.objects.exclude(announced_at__isnull=True)
        .exclude(announced_at="")
        .order_by("-announced_at")
        .first()
    )
    return row.menu_date if row else None
