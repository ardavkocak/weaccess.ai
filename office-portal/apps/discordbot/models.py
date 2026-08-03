import json

from django.db import models


class DiscordBotSettings(models.Model):
    """Hatırlatıcı Discord Bot ayarları — tek satırlık (singleton) tablo.

    Bot, Portal'in kendi sürecinde DEĞİL, ayrı bir Docker container'ında
    (discord.py) çalışır. Bu form kaydedildiğinde değerler discord-bot/.env
    ve credentials.json dosyalarına yazılır, ardından container docker
    socket üzerinden yeniden oluşturulup başlatılır (bkz. docker_control.py).

    Google Sheets bağlantısı burada TUTULMAZ: hangi sheet'in izleneceğini her
    kullanıcı kendisi, Discord üzerinden `/sheet-ekle` komutuyla belirler (bkz.
    discord-bot/cogs/settings.py, discord-bot/storage.py). Burada sadece botun
    tamamı için ortak olan token, servis hesabı kimliği ve varsayılan
    kontrol/eskime süreleri tutulur.
    """

    discord_token = models.CharField(
        max_length=200, blank=True, verbose_name="Discord Bot Token"
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
        return "Hatırlatıcı Discord Bot Ayarları"

    @classmethod
    def get_solo(cls) -> "DiscordBotSettings":
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    @property
    def service_account_email(self) -> str:
        """JSON içindeki client_email — kullanıcıların sheet'lerini paylaşacağı adres."""
        if not self.service_account_json:
            return ""
        try:
            return json.loads(self.service_account_json).get("client_email", "")
        except (ValueError, AttributeError):
            return ""
