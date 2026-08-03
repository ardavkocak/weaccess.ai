from django.db import models


class DiscordBotSettings(models.Model):
    """Satış Pipeline Discord Bot ayarları — tek satırlık (singleton) tablo.

    Bot, Portal'in kendi sürecinde DEĞİL, ayrı bir Docker container'ında
    (discord.py) çalışır. Bu form kaydedildiğinde değerler discord-bot/.env
    ve credentials.json dosyalarına yazılır, ardından container docker
    socket üzerinden yeniden oluşturulup başlatılır (bkz. docker_control.py).
    """

    discord_token = models.CharField(
        max_length=200, blank=True, verbose_name="Discord Bot Token"
    )
    spreadsheet_id = models.CharField(
        max_length=200, blank=True, verbose_name="Google Sheets Belge ID'si"
    )
    worksheet_name = models.CharField(
        max_length=200, blank=True, default="Sales Pipeline", verbose_name="Sekme Adı"
    )
    service_account_json = models.TextField(
        blank=True,
        verbose_name="Servis Hesabı JSON İçeriği (credentials.json)",
        help_text="Google Cloud Console'dan indirilen service account anahtar dosyasının tüm içeriği.",
    )
    poll_minutes = models.PositiveIntegerField(
        default=30, verbose_name="Kontrol Sıklığı (dakika)"
    )
    stale_days = models.PositiveIntegerField(
        default=7, verbose_name="Eskime Eşiği (gün)"
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Discord Bot Ayarı"
        verbose_name_plural = "Discord Bot Ayarları"

    def __str__(self):
        return "Satış Pipeline Discord Bot Ayarları"

    @classmethod
    def get_solo(cls) -> "DiscordBotSettings":
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
