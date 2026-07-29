"""Zamanlanmis mesaj servisi — scheduledMessage.service.js'in Python portu."""
from __future__ import annotations

import re

from ..models import ScheduledMessage

TIME_PATTERN = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")
MAX_TEMPLATE_LENGTH = 1900


def get_all():
    return list(ScheduledMessage.objects.select_related("duty_type").order_by("sort_order", "send_time"))


def is_valid_time(value):
    return bool(TIME_PATTERN.match(str(value or "").strip()))


def _validate_template(template, message):
    errors = []
    text = str(template or "").strip()
    if not text:
        errors.append(f'"{message.name}" için mesaj metni boş bırakılamaz.')
        return errors
    if len(text) > MAX_TEMPLATE_LENGTH:
        errors.append(f'"{message.name}" mesajı çok uzun ({len(text)} karakter). En fazla {MAX_TEMPLATE_LENGTH} olabilir.')
    if message.kind == "duty" and not re.search(r"\{(name|first|mention)\}", text):
        errors.append(f'"{message.name}" bir onay sorusudur; {{name}}, {{first}} veya {{mention}} içermelidir.')
    return errors


def validate_schedule(data):
    errors = []
    updates = []

    for message in get_all():
        raw_time = data.get(f"time_{message.id}")
        if raw_time is None:
            continue

        time = str(raw_time).strip()
        if not is_valid_time(time):
            errors.append(f'"{message.name}" için geçersiz saat: {time or "(boş)"}. SS:DD biçiminde olmalı.')
            continue

        raw_template = data.get(f"template_{message.id}")
        template = message.message_template
        if raw_template is not None:
            template = str(raw_template).replace("\r\n", "\n").strip()
            template_errors = _validate_template(template, message)
            if template_errors:
                errors.extend(template_errors)
                continue

        enabled = 1 if data.get(f"enabled_{message.id}") else 0
        timing_changed = time != message.send_time or enabled != message.is_enabled
        template_changed = template != message.message_template

        if timing_changed or template_changed:
            updates.append({
                "id": message.id, "time": time, "enabled": enabled,
                "template": template, "timing_changed": timing_changed,
            })

    if errors:
        return errors, None
    return [], updates


def save_schedule(updates):
    if not updates:
        return {"saved": False, "timing_changed": False}

    for row in updates:
        ScheduledMessage.objects.filter(pk=row["id"]).update(
            send_time=row["time"], is_enabled=row["enabled"], message_template=row["template"],
        )
    return {"saved": True, "timing_changed": any(row["timing_changed"] for row in updates)}
