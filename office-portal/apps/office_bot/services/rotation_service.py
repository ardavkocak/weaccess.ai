"""
Rotasyon servisi — ofis-gorev-takibi/src/services/rotation.service.js'in
Python/Django ORM portu. "Sira kimde?" sorusunu yanitlayan is kurallari
(tur/served takibi dahil) birebir korunmustur.
"""
from __future__ import annotations

from django.db import transaction

from ..models import DutyCycleServed, DutyHistory, RotationState
from . import employee_service
from .date_utils import today_iso


def get_state(duty_type_id):
    state, _ = RotationState.objects.get_or_create(duty_type_id=duty_type_id, defaults={"current_employee_id": None})
    return state


def set_current(duty_type_id, employee_id):
    get_state(duty_type_id)
    RotationState.objects.filter(duty_type_id=duty_type_id).update(current_employee_id=employee_id)


def find_next_active(employee_id):
    actives = employee_service.get_active()
    if not actives:
        return None
    if employee_id is None:
        return actives[0]

    index = next((i for i, e in enumerate(actives) if e.id == employee_id), None)
    if index is not None:
        return actives[(index + 1) % len(actives)]

    stale = employee_service.get_by_id(employee_id)
    if not stale:
        return actives[0]
    return next((e for e in actives if e.position > stale.position), actives[0])


def get_served_ids(duty_type_id):
    return set(DutyCycleServed.objects.filter(duty_type_id=duty_type_id).values_list("employee_id", flat=True))


def mark_served(duty_type_id, employee_id):
    DutyCycleServed.objects.get_or_create(duty_type_id=duty_type_id, employee_id=employee_id)


def clear_served(duty_type_id):
    DutyCycleServed.objects.filter(duty_type_id=duty_type_id).delete()


def unmark_served(duty_type_id, employee_id):
    if employee_id is None:
        return
    DutyCycleServed.objects.filter(duty_type_id=duty_type_id, employee_id=employee_id).delete()


def next_unserved_after(after_id, served):
    actives = employee_service.get_active()
    if not actives:
        return None

    index = next((i for i, e in enumerate(actives) if e.id == after_id), None)
    if after_id is None:
        start_index = -1
    elif index is not None:
        start_index = index
    else:
        stale = employee_service.get_by_id(after_id)
        after_pos = stale.position if stale else float("-inf")
        found = next((i for i, e in enumerate(actives) if e.position > after_pos), None)
        start_index = len(actives) - 1 if found is None else found - 1

    for step in range(1, len(actives) + 1):
        candidate = actives[(start_index + step) % len(actives)]
        if candidate.id not in served:
            return candidate
    return None


def resolve_current(duty_type_id):
    state = get_state(duty_type_id)
    actives = employee_service.get_active()

    if not actives:
        if state.current_employee_id is not None:
            set_current(duty_type_id, None)
        return None

    served = get_served_ids(duty_type_id)
    current = employee_service.get_by_id(state.current_employee_id) if state.current_employee_id else None

    if current and current.is_active == 1 and current.id not in served:
        return current

    next_employee = next_unserved_after(state.current_employee_id, served)

    if not next_employee:
        clear_served(duty_type_id)
        next_employee = find_next_active(state.current_employee_id) or actives[0]

    set_current(duty_type_id, next_employee.id if next_employee else None)
    return next_employee


def get_today_record(duty_type_id):
    return DutyHistory.objects.filter(duty_type_id=duty_type_id, duty_date=today_iso()).first()


def get_overview(duty_type_id):
    from .. import models

    duty_type = models.DutyType.objects.filter(pk=duty_type_id).first()
    current = resolve_current(duty_type_id)
    today_record = get_today_record(duty_type_id)
    is_sent_today = today_record is not None

    today = None
    today_name = None
    if is_sent_today:
        today = employee_service.get_by_id(today_record.employee_id) if today_record.employee_id else None
        today_name = today_record.employee_name

    next_employee = current
    is_stand_in = is_sent_today and today_record.consumed_turn == 0

    today_id = today_record.employee_id if is_sent_today else None
    queue = []
    for employee in employee_service.get_all():
        queue.append({
            "employee": employee,
            "is_today": today_id is not None and employee.id == today_id,
            "is_next": next_employee is not None and employee.id == next_employee.id and employee.id != today_id,
        })

    return {
        "duty_type": duty_type,
        "today": today,
        "today_name": today_name,
        "next": next_employee,
        "is_sent_today": is_sent_today,
        "is_stand_in": is_stand_in,
        "queue": queue,
    }


def restore_turn(duty_type_id, employee_id):
    if employee_id is None:
        return
    employee = employee_service.get_by_id(employee_id)
    unmark_served(duty_type_id, employee_id)
    if not employee or employee.is_active != 1:
        return
    set_current(duty_type_id, employee_id)


@transaction.atomic
def complete_duty(duty_type_id, employee_id):
    if employee_id is None:
        return {"consumed": False, "holder": resolve_current(duty_type_id)}

    state = get_state(duty_type_id)
    was_front = state.current_employee_id == employee_id

    mark_served(duty_type_id, employee_id)

    served = get_served_ids(duty_type_id)
    active_ids = [e.id for e in employee_service.get_active()]
    all_served = len(active_ids) > 0 and all(i in served for i in active_ids)

    if all_served:
        clear_served(duty_type_id)
        next_employee = find_next_active(employee_id)
        set_current(duty_type_id, next_employee.id if next_employee else None)
        return {"consumed": True, "holder": next_employee}

    if was_front:
        next_employee = next_unserved_after(employee_id, served)
        set_current(duty_type_id, next_employee.id if next_employee else None)
        return {"consumed": True, "holder": next_employee}

    return {"consumed": True, "holder": resolve_current(duty_type_id)}


@transaction.atomic
def skip_to_next(duty_type_id):
    """
    Panelden "Sırayı Geç" — Discord'daki "Hayır" cevabının panel karşılığı.

    NOT: Orijinal JS sürümü bekleyen bir Discord onay akışını da kapatır
    (mesajdaki butonları kaldırır). Bu port o adımı YAPMAZ — Discord bot
    (ayrı süreçte, değişmeden çalışmaya devam eder) zaten kendi
    "kendini toparlama" mantığına sahiptir: biri eski/tutarsız bir butona
    basarsa hata göstermek yerine mesajı günün görevlisiyle günceller
    (bkz. ofis-gorev-takibi/README.md → "Kendini toparlar"). Bu yüzden
    burada ek bir Discord API çağrısına gerek yoktur.
    """
    actives = employee_service.get_active()
    if not actives:
        return {"ok": False, "message": "Aktif çalışan bulunmadığı için sıra geçilemiyor."}
    if len(actives) == 1:
        return {"ok": False, "message": "Sırada tek aktif çalışan var; geçilecek başka kişi yok."}

    today_record = get_today_record(duty_type_id)
    current = resolve_current(duty_type_id)

    today_holder_id = today_record.employee_id if today_record else (current.id if current else None)
    from_name = today_record.employee_name if today_record else (current.full_name if current else "—")

    if today_record and today_record.consumed_turn == 1:
        restore_turn(duty_type_id, today_record.employee_id)

    served = get_served_ids(duty_type_id)
    new_holder = next_unserved_after(today_holder_id, served) or find_next_active(today_holder_id)
    if not new_holder:
        return {"ok": False, "message": "Sıradaki aktif çalışan bulunamadı."}

    result = complete_duty(duty_type_id, new_holder.id)

    from .history_service import record as record_history

    record_history(
        duty_type_id=duty_type_id,
        employee=new_holder,
        date=today_iso(),
        source="manual",
        notified=bool(today_record and today_record.notified == 1),
        consumed_turn=result["consumed"],
    )

    return {
        "ok": True,
        "message": (
            f"Görev {from_name} kişisinden {new_holder.full_name} kişisine geçirildi. Sıra ilerledi."
            if result["consumed"]
            else f"Görev {from_name} kişisinden {new_holder.full_name} kişisine geçirildi. {from_name} sırasını kaybetmedi."
        ),
        "from": from_name,
        "to": new_holder.full_name,
    }
