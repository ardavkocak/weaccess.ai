"""
Hatirlatma is mantigi — ik-otomasyon/src/services/reminder.service.js'in
Python portu. Dogum gunu (ayin son cumasi -2 gun) ve is yildonumu (3 yilin
katlari, -2 gun) kurallari birebir korunmustur.
"""
from __future__ import annotations

from datetime import date

from . import mail_service
from .date_service import anniversary_date, anniversary_reminder_date, birthday_reminder_date
from ..models import HrImport, HrSentReminder


def _list_html(items):
    return "<ul>" + "".join(f"<li>{item}</li>" for item in items) + "</ul>"


def _load_employees():
    dataset = HrImport.objects.first()
    return dataset.employees if dataset else []


def _hydrate(employee):
    birth = date.fromisoformat(employee["birth_date"]) if employee.get("birth_date") else None
    hire = date.fromisoformat(employee["hire_date"]) if employee.get("hire_date") else None
    return {**employee, "birth_date_obj": birth, "hire_date_obj": hire}


def run_test_reminders(today=None):
    today = today or date.today()
    people = [_hydrate(e) for e in _load_employees()]

    birthday_people = [p for p in people if p["birth_date_obj"] and p["birth_date_obj"].month == today.month]
    anniversary_people = []
    for p in people:
        if not p["hire_date_obj"]:
            continue
        years = today.year - p["hire_date_obj"].year
        if years >= 3 and years % 3 == 0:
            anniversary_people.append((p, years))

    mail_service.send_reminder(
        "[TEST] Doğum günü kutlama hazırlığı",
        f"<p>Bu bir test e-postasıdır. Bu ay doğan çalışanlar:</p>"
        + _list_html([p["full_name"] for p in birthday_people] or ["Bu ay doğum günü kaydı bulunamadı."]),
    )
    mail_service.send_reminder(
        "[TEST] Plaket hazırlık hatırlatması",
        f"<p>Bu bir test e-postasıdır. 3 yıl ve katlarına ulaşan çalışanlar:</p>"
        + _list_html([f"{p['full_name']} — {y}. yıl" for p, y in anniversary_people] or ["Bu yıl için plaket kaydı bulunamadı."]),
    )

    return {"birthdays": len(birthday_people), "anniversaries": len(anniversary_people), "emails_sent": 2}


def run_daily_reminders(today=None):
    today = today or date.today()
    employees = _load_employees()
    output = {"birthdays": 0, "anniversaries": 0}

    if birthday_reminder_date(today.year, today.month) == today:
        people = [_hydrate(e) for e in employees]
        people = [p for p in people if p["birth_date_obj"] and p["birth_date_obj"].month == today.month]
        key = f"birthday:{today.year}-{today.month}"
        if people and not HrSentReminder.objects.filter(key=key).exists():
            mail_service.send_reminder(
                "Doğum günü kutlama hazırlığı",
                "<p>Bu ay doğan çalışanlar:</p>" + _list_html([p["full_name"] for p in people]),
            )
            HrSentReminder.objects.create(key=key)
            output["birthdays"] = len(people)

    for raw in employees:
        person = _hydrate(raw)
        if not person["hire_date_obj"]:
            continue
        years = today.year - person["hire_date_obj"].year
        if years < 3 or years % 3 != 0:
            continue
        milestone = anniversary_date(person["hire_date_obj"], today.year)
        if anniversary_reminder_date(milestone) != today:
            continue
        key = f"anniversary:{person['row_number']}:{today.year}"
        if HrSentReminder.objects.filter(key=key).exists():
            continue
        mail_service.send_reminder(
            "Plaket hazırlık hatırlatması",
            "<p>Plaket hazırlanacak çalışan:</p>" + _list_html([f"{person['full_name']} — {years}. yıl"]),
        )
        HrSentReminder.objects.create(key=key)
        output["anniversaries"] += 1

    return output
