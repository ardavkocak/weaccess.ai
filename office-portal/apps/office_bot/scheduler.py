"""
Yemek sonuçlarını yetkili kişiye DM olarak gönderen arka plan zamanlayıcı.

Desen apps.hr.scheduler ve ofis-gorev-takibi'ndeki mealScheduler.js ile
birebir aynıdır: uygulama süreci içinde çalışan, her dakika kontrol eden
sürekli bir daemon thread — ayrı bir OS cron/systemd timer GEREKMEZ.

Saat SABİT DEĞİLDİR: her tetiklemede `settings` tablosundaki
meal_result_notify_time/meal_result_enabled/meal_result_discord_user_id
doğrudan okunur (bkz. services/meal_vote_service.py MEAL_RESULT_* anahtarları),
böylece Ayarlar sayfasından yapılan bir değişiklik sunucu yeniden
başlatılmadan bir sonraki dakika kontrolünde devreye girer.

Birden fazla gunicorn worker'ı bu döngüyü bağımsız çalıştırabilir; bu
ZARARSIZDIR çünkü gönderim, settings_service.claim_once_per_day() ile
atomik olarak "bugünü" ele geçiren TEK worker'a kilitlenir — diğerleri
False görüp hiçbir şey yapmaz (apps.hr.scheduler'daki unique-constraint'li
HrSentReminder yaklaşımının key/value tablosu karşılığı).

Hedef saat TAM dakikada eşleşmeyi beklemez (`>=` kullanılır): thread'in
`time.sleep` sapmasıyla dakikayı kaçırma riski, claim_once_per_day'in günde
tek gönderimi zaten garanti etmesi sayesinde zararsızdır — dakika kaçsa
bile bir sonraki tetiklemede gönderim yine de (o gün için tek sefer) olur.
"""
from __future__ import annotations

import logging
import threading
import time

logger = logging.getLogger("office_bot.meal_result_scheduler")

CHECK_INTERVAL_SECONDS = 60

_started = False
_lock = threading.Lock()


def _tick():
    from .services import discord_client, meal_vote_service, settings_service
    from .services.date_utils import now_hhmm, today_iso

    if settings_service.get(meal_vote_service.MEAL_RESULT_ENABLED_KEY, "0") != "1":
        return

    target_time = settings_service.get(
        meal_vote_service.MEAL_RESULT_TIME_KEY, meal_vote_service.MEAL_RESULT_DEFAULT_TIME
    )
    if now_hhmm() < target_time:
        return

    today = today_iso()
    if not settings_service.claim_once_per_day(meal_vote_service.MEAL_RESULT_LAST_SENT_KEY, today):
        return  # Bugün için zaten gönderildi (bu worker ya da başka biri tarafından).

    user_id = settings_service.get(meal_vote_service.MEAL_RESULT_USER_ID_KEY)
    if not user_id:
        logger.warning("Yemek sonuç bildirimi açık ama Discord Kullanıcı ID'si tanımlı değil.")
        return

    embed = meal_vote_service.build_result_embed(today)
    ok, detail = discord_client.send_direct_message(user_id, embeds=[embed])
    if ok:
        logger.info("Yemek sonuç bildirimi gönderildi (%s).", today)
    else:
        logger.error("Yemek sonuç bildirimi gönderilemedi: %s", detail)


def _loop():
    logger.info("Yemek sonuç bildirimi zamanlayıcısı başlatıldı (her dakika kontrol).")
    while True:
        try:
            _tick()
        except Exception:  # noqa: BLE001 — zamanlayıcı hiçbir şekilde çökmemeli
            logger.exception("Yemek sonuç bildirimi zamanlayıcısında beklenmeyen hata.")
        time.sleep(CHECK_INTERVAL_SECONDS)


def start():
    """Yalnızca bir kez, arka planda (daemon thread) döngüyü başlatır."""
    global _started
    with _lock:
        if _started:
            return
        _started = True
    threading.Thread(target=_loop, name="meal-result-dm-scheduler", daemon=True).start()
