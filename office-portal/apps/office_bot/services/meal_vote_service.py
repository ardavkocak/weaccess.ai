"""Yemek katilim oylari servisi (salt okunur kisim) — mealVote.service.js portu."""
from __future__ import annotations

from ..models import Employee, MealVote
from .date_utils import today_iso


def is_open(menu_date: str) -> bool:
    """
    Anket açık mı? KURAL: menünün ait olduğu günün SONUNDA otomatik kapanır —
    yani menu_date bugünden eskiyse anket kapalıdır. Gerçek oylar Discord
    butonları üzerinden Node botuna gelir; bu fonksiyon aynı kuralın Portal
    tarafındaki karşılığıdır (bkz. ofis-gorev-takibi mealVote.service.js
    isOpen), yalnızca GÖSTERİM amaçlı (açık/kapalı rozeti) kullanılır.
    """
    return menu_date >= today_iso()


def get_counts(menu_date):
    votes = MealVote.objects.filter(menu_date=menu_date)
    yes = votes.filter(choice="yes").count()
    no = votes.filter(choice="no").count()
    return {"yes": yes, "no": no, "total": yes + no}


def get_participation(menu_date):
    votes = list(MealVote.objects.filter(menu_date=menu_date).order_by("updated_at"))
    employees_by_discord_id = {
        e.discord_user_id: e for e in Employee.objects.exclude(discord_user_id__isnull=True).exclude(discord_user_id="")
    }

    def to_entry(vote):
        employee = employees_by_discord_id.get(vote.discord_user_id)
        return {
            "employee_id": employee.id if employee else None,
            "name": employee.full_name if employee else (vote.discord_user_name or vote.discord_user_id),
            "discord_user_id": vote.discord_user_id,
            "is_external": employee is None,
            "updated_at": vote.updated_at,
        }

    yes = [to_entry(v) for v in votes if v.choice == "yes"]
    no = [to_entry(v) for v in votes if v.choice == "no"]

    voted_ids = {v.discord_user_id for v in votes}
    pending = []
    for employee in Employee.objects.filter(is_active=1).order_by("position"):
        if not employee.discord_user_id or employee.discord_user_id not in voted_ids:
            pending.append({
                "employee_id": employee.id,
                "name": employee.full_name,
                "discord_user_id": employee.discord_user_id,
                "has_no_discord_id": not employee.discord_user_id,
            })

    return {
        "yes": yes, "no": no, "pending": pending,
        "counts": {
            "yes": len(yes), "no": len(no), "pending": len(pending),
            "responded": len(yes) + len(no),
            "total": len(pending) + len(yes) + len(no),
        },
    }
