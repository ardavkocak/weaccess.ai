"""
Gunluk IK hatirlatmalarini gonderir.

NOT: Bu artik ZORUNLU degildir — apps.hr.scheduler, web sureci icinde
calisan bir arka plan thread'i ile ayni kontrolu her gun saat 10:00
civarinda OTOMATIK yapar (bkz. apps/hr/apps.py -> HrConfig.ready()).

Bu komut, isteğe bagli olarak elle tetiklemek veya OS seviyesinde ayrica
bir cron/systemd timer kurmak isteyenler icin korunmustur; asil "bugun mu
gonderilecek" kontrolu reminder_service.run_daily_reminders() icinde
yapilir (ayin son cumasindan 2 gun once, tek seferlik).
"""
from datetime import date

from django.core.management.base import BaseCommand

from apps.hr.services.reminder_service import run_daily_reminders


class Command(BaseCommand):
    help = "Ayın son Cuma gününden 2 gün önce, bu ayın doğum günü/iş yıldönümü bildirimini TEK e-postada gönderir."

    def handle(self, *args, **options):
        result = run_daily_reminders()
        if result.get("skipped"):
            self.stdout.write(f"Atlandı: {result['reason']}")
            return
        self.stdout.write(self.style.SUCCESS(
            f"Tamamlandı: {result['birthdays']} doğum günü, {result['anniversaries']} iş yıldönümü TEK e-postada gönderildi."
        ))
