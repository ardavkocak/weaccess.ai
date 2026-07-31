"""
IK Otomasyonu modelleri.

Eskiden bu uygulama Excel'den GELEN KEYFİ sütunları (HrImport.headers +
employees[].values) tek bir JSON blob'unda saklıyordu — Excel her firmada
farklı sütun adları/sırası taşıyabildiği için bu esneklik gerekliydi.

Artık kaynak PDF'e ve SABİT 4 alana (Ad Soyad, İşe Giriş Tarihi, Doğum
Tarihi, Alerji Bilgisi) geçildiği için keyfi sütun esnekliğine gerek kalmadı;
bunun yerine GERÇEK, sorgulanabilir alanlara sahip bir model kullanılır. Bu,
arama ve sıralamanın veritabanı seviyesinde (güvenilir, hızlı) yapılmasını
sağlar — JSON blob içinde Python'da sıralamaya kıyasla çok daha sağlam.

Yükleme davranışı KORUNUR: yeni bir PDF yüklendiğinde önceki tüm kayıtların
yerine yenileri yazılır (bkz. views.UploadView).
"""
from django.db import models


class HrEmployee(models.Model):
    """PDF'ten çıkarılan tek bir çalışan kaydı."""
    full_name = models.CharField(max_length=200, verbose_name="Ad Soyad")
    department = models.CharField(max_length=200, blank=True, verbose_name="Departman")
    role = models.CharField(max_length=200, blank=True, verbose_name="Rol / Unvan")
    hire_date = models.DateField(null=True, blank=True, verbose_name="İşe Giriş Tarihi")
    work_model = models.CharField(max_length=100, blank=True, verbose_name="Çalışma Modeli")
    birth_date = models.DateField(null=True, blank=True, verbose_name="Doğum Tarihi")
    blood_type = models.CharField(max_length=10, blank=True, verbose_name="Kan Grubu")
    allergy_info = models.CharField(max_length=255, blank=True, verbose_name="Alerji Bilgisi")
    import_confidence = models.PositiveSmallIntegerField(
        null=True, blank=True, verbose_name="Okuma Güven Skoru (%)"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "hr"
        ordering = ["full_name"]

    def __str__(self):
        return self.full_name


class HrSettings(models.Model):
    """Bildirim ayarları. Tek satır (singleton) tutulur."""
    # --- Mevcut e-posta/SMTP yapısı (aynen korunur) ---
    sender_email = models.CharField(max_length=255, blank=True)
    recipient_emails = models.JSONField(default=list, blank=True)
    smtp_host = models.CharField(max_length=255, blank=True)
    smtp_port = models.IntegerField(null=True, blank=True)
    smtp_user = models.CharField(max_length=255, blank=True)
    smtp_pass = models.CharField(max_length=255, blank=True)
    smtp_secure = models.BooleanField(default=False)
    mail_from = models.CharField(max_length=255, blank=True)

    # --- Yeni: bildirim açık/kapalı + hatırlatmaların gideceği tek adres ---
    notifications_enabled = models.BooleanField(default=True, verbose_name="Bildirim Açık/Kapalı")
    notification_email = models.CharField(max_length=255, blank=True, verbose_name="Bildirim Gönderilecek E-posta")

    last_reminder_sent_at = models.DateTimeField(null=True, blank=True, verbose_name="Son Bildirim Tarihi")

    class Meta:
        app_label = "hr"

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def reminder_recipients(self):
        """
        Hatırlatma e-postasının gideceği adres(ler). Yeni tekil
        `notification_email` alanı doluysa o kullanılır; boşsa eski
        `recipient_emails` listesine (geriye dönük uyum) düşülür.
        """
        if self.notification_email.strip():
            return [self.notification_email.strip()]
        return self.recipient_emails


class HrSentReminder(models.Model):
    """Bir hatirlatmanin daha once gonderilip gonderilmedigini isaretler."""
    key = models.CharField(max_length=100, unique=True)
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "hr"
