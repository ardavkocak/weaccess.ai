"""
IK Otomasyonu modelleri.

Orijinal proje (ik-otomasyon) veriyi duz JSON dosyalarinda tutuyordu
(data/employees.json, data/settings.json, data/sent-reminders.json). Bu
Django portu ayni veri seklini (esnek/dinamik sutunlu Excel verisi + ayarlar
+ gonderilen hatirlatma kayitlari) KORUR ama Portal'in kendi PostgreSQL
veritabaninda, gercek tablolarda saklar.
"""
from django.db import models


class HrImport(models.Model):
    """
    Son yuklenen Excel verisi. Tek satir tutulur (yeni yukleme oncekini
    degistirir) — orijinal projenin "dosya her yuklendiginde ustune yazar"
    davranisiyla birebir ayni.
    """
    headers = models.JSONField(default=list, blank=True)
    employees = models.JSONField(default=list, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "hr"


class HrSettings(models.Model):
    """E-posta bildirim ayarlari. Tek satir (singleton) tutulur."""
    sender_email = models.CharField(max_length=255, blank=True)
    recipient_emails = models.JSONField(default=list, blank=True)
    smtp_host = models.CharField(max_length=255, blank=True)
    smtp_port = models.IntegerField(null=True, blank=True)
    smtp_user = models.CharField(max_length=255, blank=True)
    smtp_pass = models.CharField(max_length=255, blank=True)
    smtp_secure = models.BooleanField(default=False)
    mail_from = models.CharField(max_length=255, blank=True)

    class Meta:
        app_label = "hr"

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class HrSentReminder(models.Model):
    """Bir hatirlatmanin daha once gonderilip gonderilmedigini isaretler."""
    key = models.CharField(max_length=100, unique=True)
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "hr"
