"""
Etkilesimli gorev onayi servisi — dutyConfirmation.service.js'in Python portu.

Yalnizca BASLATMA/SIFIRLAMA/DURUM tarafi buradadir (Portal'in "Test
Islemleri" sayfasindan tetiklenir). Buton TIKLAMALARINI (onButton/
decideAnswer) islemek gateway baglantisi gerektirir; bu, degismeden
calismaya devam eden orijinal Node botunun isidir (bkz. discord_client.py
docstring'i). Portal yalnizca akisi baslatir/sifirlar; sonraki Evet/Hayir
tiklamalarini zaten calisan bot isler ve ayni SQLite'a yazar.
"""
from __future__ import annotations

from django.db import transaction

from ..models import DutyConfirmation, Employee
from . import discord_client, rotation_service, settings_service
from .date_utils import add_days, format_long_tr, today_iso
from .discord_client import DiscordError
from .messages import render_template


def get_flow(duty_type_id, date):
    return DutyConfirmation.objects.filter(duty_type_id=duty_type_id, duty_date=date).first()


def get_active_flow(duty_type_id):
    """Panelin ilgilendigi akis: bugunden itibaren en ileri tarihli olan."""
    return (
        DutyConfirmation.objects.filter(duty_type_id=duty_type_id, duty_date__gte=today_iso())
        .order_by("-duty_date")
        .first()
    )


def _next_working_day(from_iso=None):
    from_iso = from_iso or today_iso()
    current = from_iso
    for _ in range(14):
        current = add_days(current, 1)
        from datetime import date as _date

        if _date.fromisoformat(current).weekday() < 5:
            return current
    return add_days(from_iso, 1)


@transaction.atomic
def _ensure_flow(duty_type_id, source):
    target_date = _next_working_day()
    existing = get_flow(duty_type_id, target_date)
    if existing:
        return existing, False

    candidate = rotation_service.resolve_current(duty_type_id)
    if not candidate:
        return None, False

    flow = DutyConfirmation.objects.create(
        duty_type_id=duty_type_id, duty_date=target_date, status="pending", step=0, source=source,
        start_employee_id=candidate.id, candidate_employee_id=candidate.id, candidate_name=candidate.full_name,
    )
    return flow, True


def start_flow(duty_type_id, source="manual"):
    """Onay akisini baslatir (veya mevcut akisi tazeler). Discord'a REST ile gonderir."""
    from ..models import DutyType

    duty_type = DutyType.objects.filter(pk=duty_type_id).first()
    if not duty_type:
        return {"ok": False, "message": "Görev türü bulunamadı."}

    flow, created = _ensure_flow(duty_type_id, source)
    if not flow:
        return {"ok": False, "message": "Aktif çalışan bulunamadı. Önce en az bir çalışanı aktif yapın."}

    day_label = format_long_tr(flow.duty_date)

    if flow.status == "confirmed":
        return {"ok": True, "skipped": True, "message": f"{day_label} görevi zaten kesinleşti: {flow.confirmed_name}."}
    if flow.status == "exhausted":
        return {"ok": True, "skipped": True, "message": f"{day_label} için uygun kişi bulunamadı olarak işaretlenmiş."}

    from ..models import ScheduledMessage

    template_row = ScheduledMessage.objects.filter(kind="duty", duty_type_id=duty_type_id).order_by("sort_order").first()
    template = template_row.message_template if template_row else "📅 {gunUn} görevlisi belirleniyor.\n\n👤 {mention}\n\n{gun} ofiste misin?"

    candidate_employee = Employee.objects.filter(pk=flow.candidate_employee_id).first() or {
        "full_name": flow.candidate_name, "discord_user_id": None,
    }
    content = render_template(
        template, employee=candidate_employee, duty_type=duty_type,
        company=settings_service.get("company_name", ""), target_date=flow.duty_date,
    )

    try:
        duty_channel_id = settings_service.get_channel_id("duty")
        if not duty_channel_id:
            raise DiscordError("Görev Kanalı ID tanımlı değil. Discord Ayarları sayfasından ekleyin.")

        if not created and flow.message_id and flow.channel_id == duty_channel_id:
            discord_client.edit_channel_message(
                flow.channel_id, flow.message_id, content, discord_client.build_components(flow.id, flow.step)
            )
            return {"ok": True, "message": f"Onay mesajı güncel: {flow.candidate_name} soruluyor."}

        sent = discord_client.send_channel_message(duty_channel_id, content, flow_id=flow.id, step=flow.step)
    except DiscordError as exc:
        if created:
            flow.delete()
        return {"ok": False, "message": str(exc)}

    flow.channel_id = duty_channel_id
    flow.message_id = sent["id"]
    flow.save(update_fields=["channel_id", "message_id"])

    return {"ok": True, "message": f"{day_label} için {flow.candidate_name} soruldu."}


@transaction.atomic
def reset_today(duty_type_id):
    from . import history_service

    flow = get_active_flow(duty_type_id)
    if not flow:
        return {"ok": False, "message": 'Sıfırlanacak bir onay akışı yok. Önce "Görev Onayını Başlat" deyin.'}
    if flow.status == "pending" and flow.step == 0:
        return {"ok": False, "message": "Onay akışı zaten en baştan bekliyor; sıfırlanacak bir cevap yok."}

    from ..models import DutyHistory

    record = DutyHistory.objects.filter(duty_type_id=duty_type_id, duty_date=flow.duty_date).first()
    if record:
        if record.consumed_turn == 1:
            rotation_service.restore_turn(duty_type_id, record.employee_id)
        record.delete()

    candidate = rotation_service.resolve_current(duty_type_id)
    if not candidate:
        return {"ok": False, "message": "Aktif çalışan bulunamadı. Önce en az bir çalışanı aktif yapın."}

    previous_name = flow.confirmed_name
    flow.status = "pending"
    flow.step = 0
    flow.start_employee_id = candidate.id
    flow.candidate_employee_id = candidate.id
    flow.candidate_name = candidate.full_name
    flow.previous_name = None
    flow.confirmed_employee_id = None
    flow.confirmed_name = None
    flow.reset_count = (flow.reset_count or 0) + 1
    flow.save()

    return {
        "ok": True, "message": f"Onay sıfırlandı. Yeniden {candidate.full_name} soruluyor.",
        "flow": flow, "previous_name": previous_name,
    }


def reset_and_ask_again(duty_type_id):
    reset = reset_today(duty_type_id)
    if not reset["ok"]:
        return reset

    sent = start_flow(duty_type_id, source="manual")
    if not sent["ok"]:
        return {"ok": False, "message": f"Onay sıfırlandı ancak Discord mesajı güncellenemedi: {sent['message']}"}

    suffix = f" Önceki sonuç ({reset['previous_name']}) iptal edildi." if reset.get("previous_name") else ""
    return {"ok": True, "message": f"{sent['message']}{suffix}"}


def get_today_status(duty_type_id):
    flow = get_active_flow(duty_type_id)
    if not flow:
        return None

    is_today = flow.duty_date == today_iso()
    day_word = "Bugünkü" if is_today else "Yarınki"
    day_label_text = "bugün" if is_today else format_long_tr(flow.duty_date)

    labels = {
        "pending": {"state": "pending", "label": "Onay bekleniyor", "detail": f"{day_label_text} görevi için {flow.candidate_name} soruluyor."},
        "confirmed": {"state": "confirmed", "label": "Kesinleşti", "detail": f"{day_word} görevli: {flow.confirmed_name}."},
        "exhausted": {"state": "exhausted", "label": "Kimse bulunamadı", "detail": f"{day_label_text} için uygun kişi bulunamadı."},
    }
    status = dict(labels.get(flow.status, labels["pending"]))
    status["flow"] = flow
    if flow.reset_count:
        status["detail"] += f" ({flow.reset_count} kez sıfırlandı.)"
    return status
