"""
Gunluk IK hatirlatmalarini gonderir.

Orijinal proje bunu kendi surecinde node-cron ile ('0 9 * * 1-5' — is
gunlerinde 09:00) yapiyordu. Django/WSGI'nin kendi surekli calisan bir
zamanlayicisi olmadigi icin bu komut, sunucu ortaminda OS seviyesinde bir
zamanlayicidan (cron/systemd timer) her is gunu 09:00'da cagirilmalidir:

    0 9 * * 1-5  cd /path/to/office-portal && ./venv/bin/python manage.py send_hr_reminders
"""
from datetime import date

from django.core.management.base import BaseCommand

from apps.hr.services.reminder_service import run_daily_reminders


class Command(BaseCommand):
    help = "Bugün için doğum günü / iş yıldönümü hatırlatma e-postalarını gönderir (tekrar göndermez)."

    def handle(self, *args, **options):
        if date.today().weekday() >= 5:  # Cumartesi/Pazar
            self.stdout.write("Hafta sonu — hatırlatma gönderilmedi.")
            return
        result = run_daily_reminders()
        self.stdout.write(self.style.SUCCESS(
            f"Tamamlandı: {result['birthdays']} doğum günü, {result['anniversaries']} yıldönümü hatırlatması gönderildi."
        ))
