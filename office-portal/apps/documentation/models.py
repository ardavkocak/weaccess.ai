from django.db import models


class SheetsSettings(models.Model):
    """Google Sheets entegrasyon ayarları — tek satırlık (singleton) tablo.

    Önceden bu değerler .env dosyasında (GOOGLE_SHEETS_URL,
    GOOGLE_SERVICE_ACCOUNT_JSON) düz metin olarak duruyordu. Artık arayüzden
    (Ayarlar ikonu) girilip veritabanında saklanır; .env hâlâ bir fallback
    olarak desteklenir (bkz. views.py _sheets_url / _servis_hesabi).
    """

    sheets_url = models.CharField(
        max_length=500, blank=True, verbose_name="Google Sheets URL'si"
    )
    service_account_json = models.TextField(
        blank=True,
        verbose_name="Servis Hesabı JSON İçeriği",
        help_text="Google Cloud Console'dan indirilen service account anahtar dosyasının tüm içeriği.",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Sheets Ayarı"
        verbose_name_plural = "Sheets Ayarları"

    def __str__(self):
        return "Google Sheets Ayarları"

    @classmethod
    def get_solo(cls) -> "SheetsSettings":
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
