"""
Hatırlatma iş mantığı — doğum günü ve iş yıldönümü kontrolleri TEK bir
birleşik e-postada gönderilir (bkz. modül talebi: "Doğum günleri ve iş
yıldönümleri ayrı ayrı mail olarak gitmesin").

ZAMANLAMA
---------
Otomasyon her ayın son Cuma gününden 2 gün önce çalışır (bkz.
date_service.reminder_trigger_date — hafta sonuna denk gelirse Cuma'ya
çekilir). Hem doğum günleri hem iş yıldönümleri, bildirimin gönderildiği
GÜNÜN AYI için kontrol edilir — bir SONRAKİ ay DEĞİL (örn. 29 Temmuz 2026'da
gönderilen bildirim Temmuz 2026 çalışanlarını listeler, Ağustos'u değil).
Ay hesaplaması `today.month`/`today.year` üzerinden doğrudan yapılır; ay
ilerletme (next_month, +1, relativedelta vb.) KULLANILMAZ.

KURAL: 3'ÜN KATI YIL
---------------------
İş yıldönümü yalnızca tam 3, 6, 9, 12... yılını dolduran çalışanlar için
hatırlatılır (`years >= 3 and years % 3 == 0`), hedef ayın YILI baz alınarak
hesaplanır (Aralık→Ocak geçişinde yıl da doğru ilerler).

KURAL: UZAKTAN ÇALIŞANLAR
--------------------------
Çalışma Modeli "UZAKTAN" olan çalışanlar YALNIZCA doğum günü listesinden
çıkarılır (bkz. `_find_birthdays`). İş yıldönümü listesi bu filtreden
ETKİLENMEZ — ofis/hibrit/uzaktan farkı olmadan tüm çalışma modelleri iş
yıldönümü listesine dahildir (bkz. `_find_anniversaries`).

YANLIŞ KİŞİYE BİLDİRİM GİTMEMESİ
--------------------------------
Doğum günü kontrolü yalnızca `birth_date.month` hedef aya eşit olan
çalışanları seçer; iş yıldönümü kontrolü hem `hire_date.month` hedef aya eşit
HEM DE o yıl gerçekten 3'ün katı bir yıl dönümü olan çalışanları seçer —
ikisi de tarih nesneleri üzerinden karşılaştırıldığı için (string değil)
yıl/ay/gün karışıklığı riski yoktur.
"""
from __future__ import annotations

from datetime import date

from django.db import IntegrityError
from django.utils import timezone

from . import mail_service
from .date_service import reminder_trigger_date
from ..models import HrEmployee, HrSentReminder, HrSettings

REMINDER_SUBJECT = "Doğum Günü ve İş Yıldönümü Bildirimi"


def _month_name_tr(month: int) -> str:
    return [
        "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
        "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık",
    ][month - 1]


def _find_birthdays(target_month: int):
    """Doğum günü listesi — UZAKTAN çalışanlar bu listeden hariç tutulur (yalnızca burada)."""
    employees = HrEmployee.objects.filter(birth_date__month=target_month).order_by("birth_date__day")
    return [e for e in employees if (e.work_model or "").strip().upper() != "UZAKTAN"]


def _find_anniversaries(target_year: int, target_month: int):
    """(employee, kaçıncı_yıl) çiftleri — yalnızca 3'ün katı yıl dönümleri."""
    result = []
    for employee in HrEmployee.objects.filter(hire_date__month=target_month):
        years = target_year - employee.hire_date.year
        if years >= 3 and years % 3 == 0:
            result.append((employee, years))
    result.sort(key=lambda pair: pair[0].hire_date.day)
    return result


def _gather_reminder_data(today: date):
    """
    Verilen `today` tarihinin KENDİ AYINI hedef alarak (bir sonraki ay DEĞİL)
    doğum günü ve iş yıldönümü listelerini toplar. Hem `run_daily_reminders`
    hem de manuel test butonu (`run_manual_test_reminder`) BU fonksiyonu
    çağırır — böylece iki yol arasında algoritma farkı olamaz.
    """
    target_year, target_month = today.year, today.month
    birthdays = _find_birthdays(target_month)
    anniversaries = _find_anniversaries(target_year, target_month)
    return target_year, target_month, birthdays, anniversaries


def _build_email_html(target_year, target_month, birthdays, anniversaries):
    month_label = f"{_month_name_tr(target_month)} {target_year}"

    def _fmt_birthday(e):
        return f"{e.full_name} - {e.birth_date.day} {_month_name_tr(e.birth_date.month)}"

    def _fmt_anniversary(pair):
        employee, years = pair
        return f"{employee.full_name} - {years}. yıl"

    birthday_html = (
        "<ul>" + "".join(f"<li>{_fmt_birthday(e)}</li>" for e in birthdays) + "</ul>"
        if birthdays else "<p>Bu ay doğum günü olan çalışan bulunmuyor.</p>"
    )
    anniversary_html = (
        "<ul>" + "".join(f"<li>{_fmt_anniversary(p)}</li>" for p in anniversaries) + "</ul>"
        if anniversaries else "<p>Bu ay iş yıldönümü olan çalışan bulunmuyor.</p>"
    )

    return (
        f"<h3>Bu ay doğum günü olan çalışanlar ({month_label})</h3>"
        f"{birthday_html}"
        f"<h3>Bu ay iş yıl dönümü olan çalışanlar ({month_label})</h3>"
        f"{anniversary_html}"
    )


def run_daily_reminders(today=None):
    """
    Uygulama içi zamanlayıcı (bkz. `apps.hr.scheduler`) tarafından her gün
    saat 10:00 civarında çağrılır. Yalnızca bugün gerçekten
    `reminder_trigger_date` ise VE bildirimler açıksa gerçek e-posta
    gönderir; aksi halde hiçbir şey yapmaz.

    `HrSentReminder` kaydı e-posta göndermeden ÖNCE, atomik `create()` ile
    oluşturulur (unique `key` kısıtlaması sayesinde). Bu, birden fazla
    gunicorn worker'ının zamanlayıcıyı aynı anda çalıştırdığı durumda bile
    e-postanın YALNIZCA BİR KEZ gönderilmesini garanti eder — ikinci
    worker `IntegrityError` alıp sessizce atlar.
    """
    today = today or date.today()
    settings = HrSettings.load()

    if not settings.notifications_enabled:
        return {"skipped": True, "reason": "Bildirimler kapalı.", "birthdays": 0, "anniversaries": 0}

    if reminder_trigger_date(today.year, today.month) != today:
        return {"skipped": True, "reason": "Bugün tetikleme günü değil.", "birthdays": 0, "anniversaries": 0}

    target_year, target_month, birthdays, anniversaries = _gather_reminder_data(today)
    key = f"hr-reminder:{target_year}-{target_month:02d}"

    try:
        HrSentReminder.objects.create(key=key)
    except IntegrityError:
        return {"skipped": True, "reason": "Bu ay için hatırlatma zaten gönderilmiş.", "birthdays": 0, "anniversaries": 0}

    if not birthdays and not anniversaries:
        return {"skipped": True, "reason": "Bu ay için doğum günü/yıldönümü yok.", "birthdays": 0, "anniversaries": 0}

    mail_service.send_reminder(
        REMINDER_SUBJECT,
        _build_email_html(target_year, target_month, birthdays, anniversaries),
    )
    settings.last_reminder_sent_at = timezone.now()
    settings.save(update_fields=["last_reminder_sent_at"])

    return {"skipped": False, "birthdays": len(birthdays), "anniversaries": len(anniversaries)}


def run_manual_test_reminder(today=None):
    """
    "🧪 Bu Ayın Hatırlatmasını Şimdi Gönder" butonu.

    Gerçek tetikleme gününü (ayın son Cuma'sından 2 gün önce) beklemeden,
    bugünü SANKİ o tetikleme günüymüş gibi simüle eder ve `run_daily_reminders`
    ile TAMAMEN AYNI `_gather_reminder_data` fonksiyonunu, AYNI konu satırını
    ve AYNI e-posta gövde şablonunu kullanarak gönderir — böylece üretilen
    e-posta, gerçek otomatik e-postanın birebir aynısıdır.

    Çalışan kayıtlarına, `HrSentReminder` geçmişine veya
    `HrSettings.last_reminder_sent_at` alanına DOKUNMAZ — yalnızca test
    e-postası gönderir, zamanlayıcının veya gerçek gönderim tarihinin
    hiçbir şekilde etkilenmemesi gerekir.
    """
    real_today = today or date.today()
    simulated_today = reminder_trigger_date(real_today.year, real_today.month)

    target_year, target_month, birthdays, anniversaries = _gather_reminder_data(simulated_today)

    mail_service.send_reminder(
        REMINDER_SUBJECT,
        _build_email_html(target_year, target_month, birthdays, anniversaries),
    )

    return {
        "birthdays": len(birthdays),
        "anniversaries": len(anniversaries),
        "simulated_today": simulated_today,
    }
