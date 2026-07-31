"""Tarih kurallari — ik-otomasyon/src/services/date.service.js'in Python portu."""
from __future__ import annotations

from datetime import date, timedelta
import calendar as _calendar


def last_friday(year: int, month: int) -> date:
    """Belirtilen ayin (1-12) son cuma gunu."""
    last_day = date(year, month, _calendar.monthrange(year, month)[1])
    days_since_friday = (last_day.weekday() - 4) % 7  # Python: Pazartesi=0 .. Cuma=4
    return last_day - timedelta(days=days_since_friday)


def move_weekend_reminder_to_friday(d: date) -> date:
    if d.weekday() == 5:  # Cumartesi
        return d - timedelta(days=1)
    if d.weekday() == 6:  # Pazar
        return d - timedelta(days=2)
    return d


def reminder_trigger_date(year: int, month: int) -> date:
    """
    Doğum günü + iş yıldönümü hatırlatmasının BİRLİKTE gönderileceği tarih:
    ayın son cumasından 2 gün önce (hafta sonuna denk gelirse cumaya çekilir).
    Bu iki hatırlatma artık TEK bir e-postada birleştiği için tetikleme
    tarihi de tektir (bkz. reminder_service.run_daily_reminders).
    """
    return move_weekend_reminder_to_friday(last_friday(year, month) - timedelta(days=2))


def next_month(year: int, month: int) -> tuple[int, int]:
    """Verilen ay/yıldan bir SONRAKİ ayı (yıl taşması dahil) döner."""
    if month == 12:
        return year + 1, 1
    return year, month + 1


def upcoming_trigger_date(today=None) -> date:
    """
    Bir SONRAKİ otomatik hatırlatmanın gönderileceği tarih (panelde
    "Sonraki Otomatik Hatırlatma" bilgisi için).

    Bu ayın tetikleme tarihi bugünden ileriyse (veya tam bugünse — o zaman
    otomasyon bugün henüz çalışmamış demektir) o tarih kullanılır; geçmişse
    bir sonraki ayın tetikleme tarihine bakılır. Böylece ay sonu/başı
    geçişlerinde de her zaman GERÇEKTEN gelecekteki (veya bugünkü) doğru
    tarih gösterilir, geçmiş bir tarih asla gösterilmez.
    """
    today = today or date.today()
    candidate = reminder_trigger_date(today.year, today.month)
    if candidate < today:
        year, month = next_month(today.year, today.month)
        candidate = reminder_trigger_date(year, month)
    return candidate
