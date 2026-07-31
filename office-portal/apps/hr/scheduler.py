"""
Uygulama süreci içinde çalışan basit bir arka plan zamanlayıcı.

OS seviyesinde ayrı bir cron/systemd timer kurulumu GEREKTİRMEDEN, ayın son
Cuma gününden 2 gün önce saat 10:00 civarında otomatik hatırlatma e-postasını
gönderir (bkz. `services.reminder_service.run_daily_reminders`). Deseni,
ofis-gorev-takibi'ndeki `mealScheduler.js` ile aynıdır: her dakika kontrol
eden sürekli bir arka plan döngüsü.

Birden fazla gunicorn worker'ı bu döngüyü bağımsız olarak çalıştırabilir;
bu ZARARSIZDIR çünkü `run_daily_reminders` içindeki `HrSentReminder.objects
.create()` atomik ve `key` alanı unique olduğu için e-posta yalnızca BİR
KEZ gönderilir (bkz. reminder_service.py).

Saat 10:00 tam dakikasını kaçırma riskine (thread zamanlama sapması) karşı,
10:00-10:04 arasındaki her dakika kontrol edilir; idempotency garantisi
sayesinde bu pencere içinde birden çok kontrol olsa da e-posta tekrar
gönderilmez.
"""
from __future__ import annotations

import logging
import threading
import time
from datetime import datetime

logger = logging.getLogger("hr.scheduler")

CHECK_INTERVAL_SECONDS = 60
TARGET_HOUR = 10
TARGET_MINUTE_WINDOW = range(0, 5)  # 10:00 - 10:04 arası (dakika sapmasına karşı tolerans)

_started = False
_lock = threading.Lock()


def _tick():
    from .services.reminder_service import run_daily_reminders

    now = datetime.now()
    if now.hour != TARGET_HOUR or now.minute not in TARGET_MINUTE_WINDOW:
        return
    result = run_daily_reminders(today=now.date())
    if result.get("skipped"):
        logger.info("İK hatırlatma zamanlayıcısı: atlandı (%s).", result.get("reason"))
    else:
        logger.info(
            "İK hatırlatma zamanlayıcısı: e-posta gönderildi (%d doğum günü, %d iş yıldönümü).",
            result["birthdays"], result["anniversaries"],
        )


def _loop():
    logger.info(
        "İK hatırlatma zamanlayıcısı başlatıldı (her dakika kontrol, hedef saat %02d:00-%02d:04).",
        TARGET_HOUR, TARGET_HOUR,
    )
    while True:
        try:
            _tick()
        except Exception:  # noqa: BLE001 — zamanlayıcı hiçbir şekilde çökmemeli
            logger.exception("İK hatırlatma zamanlayıcısında beklenmeyen hata.")
        time.sleep(CHECK_INTERVAL_SECONDS)


def start():
    """Yalnızca bir kez, arka planda (daemon thread) döngüyü başlatır."""
    global _started
    with _lock:
        if _started:
            return
        _started = True
    threading.Thread(target=_loop, name="hr-reminder-scheduler", daemon=True).start()
