"""
Calisan servisi — ofis-gorev-takibi/src/services/employee.service.js'in
Python/Django ORM portu. Is kurallari (sira/position mantigi) birebir
korunmustur; yalnizca dil ve ORM API'si degismistir.
"""
from __future__ import annotations

import re

from django.db import transaction
from django.db.models import F

from ..models import Employee

DISCORD_ID_PATTERN = re.compile(r"^\d{17,20}$")


def get_all():
    return list(Employee.objects.order_by("position"))


def get_active():
    return list(Employee.objects.filter(is_active=1).order_by("position"))


def get_by_id(employee_id):
    return Employee.objects.filter(pk=employee_id).first()


def get_counts():
    total = Employee.objects.count()
    active = Employee.objects.filter(is_active=1).count()
    return {"total": total, "active": active, "passive": total - active}


def get_total():
    return Employee.objects.count()


def validate(data, exclude_id=None):
    errors = []
    full_name = str(data.get("full_name") or "").strip()
    if not full_name:
        errors.append("Ad soyad boş bırakılamaz.")
    elif len(full_name) < 2:
        errors.append("Ad soyad en az 2 karakter olmalıdır.")
    elif len(full_name) > 100:
        errors.append("Ad soyad en fazla 100 karakter olabilir.")

    discord_user_id = str(data.get("discord_user_id") or "").strip()
    if discord_user_id and not DISCORD_ID_PATTERN.match(discord_user_id):
        errors.append("Discord kullanıcı ID yalnızca rakamlardan oluşmalı ve 17-20 haneli olmalıdır.")

    if discord_user_id:
        clash = Employee.objects.filter(discord_user_id=discord_user_id)
        if exclude_id:
            clash = clash.exclude(pk=exclude_id)
        if clash.exists():
            errors.append("Bu Discord kullanıcı ID başka bir çalışana tanımlı.")

    if errors:
        return errors, None

    is_active_raw = data.get("is_active")
    is_active = 1 if is_active_raw in ("on", True, "1", 1) else 0
    company = str(data.get("company") or "").strip()
    return [], {
        "full_name": full_name,
        "discord_user_id": discord_user_id or None,
        "is_active": is_active,
        "company": company or None,
    }


def normalize_positions():
    rows = list(Employee.objects.order_by("position", "id"))
    for index, row in enumerate(rows):
        Employee.objects.filter(pk=row.pk).update(position=index + 1)


def _clamp_position(value, maximum, fallback=None):
    if value is None or str(value).strip() == "":
        return fallback
    try:
        parsed = int(str(value))
    except ValueError:
        return fallback
    return min(max(parsed, 1), maximum)


@transaction.atomic
def create(data, position=None):
    normalize_positions()
    total = get_total()
    target = _clamp_position(position, total + 1, total + 1)

    Employee.objects.filter(position__gte=target).update(position=F("position") + 1)

    employee = Employee.objects.create(
        full_name=data["full_name"],
        discord_user_id=data["discord_user_id"],
        is_active=data["is_active"],
        position=target,
        company=data["company"],
    )
    return employee


def update(employee_id, data):
    Employee.objects.filter(pk=employee_id).update(
        full_name=data["full_name"],
        discord_user_id=data["discord_user_id"],
        is_active=data["is_active"],
        company=data["company"],
    )
    return get_by_id(employee_id)


def toggle_active(employee_id):
    employee = get_by_id(employee_id)
    if not employee:
        return None
    next_state = 0 if employee.is_active == 1 else 1
    Employee.objects.filter(pk=employee_id).update(is_active=next_state)
    return get_by_id(employee_id)


@transaction.atomic
def remove(employee_id):
    employee = get_by_id(employee_id)
    if not employee:
        return False
    employee.delete()
    Employee.objects.filter(position__gt=employee.position).update(position=F("position") - 1)
    return True


@transaction.atomic
def move(employee_id, direction):
    employee = get_by_id(employee_id)
    if not employee:
        return False

    if direction == "up":
        neighbour = Employee.objects.filter(position__lt=employee.position).order_by("-position").first()
    else:
        neighbour = Employee.objects.filter(position__gt=employee.position).order_by("position").first()

    if not neighbour:
        return False

    Employee.objects.filter(pk=employee.pk).update(position=neighbour.position)
    Employee.objects.filter(pk=neighbour.pk).update(position=employee.position)
    return True


@transaction.atomic
def move_to_position(employee_id, position):
    normalize_positions()
    employee = get_by_id(employee_id)
    if not employee:
        return {"ok": False, "message": "Çalışan bulunamadı."}

    target = _clamp_position(position, get_total(), None)
    if target is None:
        return {"ok": False, "message": "Geçerli bir sıra numarası girin."}
    if target == employee.position:
        return {"ok": True, "employee": employee, "from": employee.position, "to": target}

    if target < employee.position:
        Employee.objects.filter(position__gte=target, position__lt=employee.position).update(
            position=F("position") + 1
        )
    else:
        Employee.objects.filter(position__gt=employee.position, position__lte=target).update(
            position=F("position") - 1
        )

    Employee.objects.filter(pk=employee_id).update(position=target)
    return {"ok": True, "employee": get_by_id(employee_id), "from": employee.position, "to": target}


@transaction.atomic
def reorder(ids):
    current = get_all()
    known_ids = {e.id for e in current}

    if not isinstance(ids, list) or len(ids) != len(current):
        return {"ok": False, "message": "Sıralama listesi güncel değil. Sayfayı yenileyip tekrar deneyin."}

    seen = set()
    for employee_id in ids:
        if employee_id not in known_ids or employee_id in seen:
            return {"ok": False, "message": "Sıralama listesi geçersiz. Sayfayı yenileyip tekrar deneyin."}
        seen.add(employee_id)

    for index, employee_id in enumerate(ids):
        Employee.objects.filter(pk=employee_id).update(position=index + 1)
    return {"ok": True}
