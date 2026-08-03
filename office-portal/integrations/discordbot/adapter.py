"""Hatırlatıcı Discord Bot (discord-bot) için entegrasyon adapteru.

Diğer adapterlerden farklı olarak bu proje Portal'in kendi sürecinde
ÇALIŞMAZ — ayrı bir Docker container'ında (discord.py) bağımsız bir süreç
olarak çalışır. "Bağlantı durumu" burada container'ın çalışıp çalışmadığıdır
(bkz. apps.discordbot.docker_control), veritabanı/API bağlantısı değil.
"""
from integrations.base import BaseIntegration, IntegrationInfo, IntegrationStatus


class DiscordBotIntegration(BaseIntegration):
    info = IntegrationInfo(
        key="discordbot",
        name="Hatırlatıcı Bot",
        source_project="discord-bot",
        tech_stack="discord.py — ayrı Docker container'ında bağımsız süreç",
        planned_mode="docker_control",
        notes=(
            "Portal'in kendi sürecinde çalışmaz; Docker socket üzerinden "
            "ayrı container'ı başlatır/durdurur/yeniden oluşturur "
            "(bkz. apps.discordbot.docker_control)."
        ),
    )

    def get_status(self) -> str:
        from apps.discordbot import docker_control

        status, _ = docker_control.get_status()
        return IntegrationStatus.CONNECTED if status == "running" else IntegrationStatus.NOT_CONNECTED

    def health_check(self):
        from apps.discordbot import docker_control

        status, detail = docker_control.get_status()
        if status == "running":
            return True, "Bot container'ı çalışıyor."
        if status == "not_found":
            return False, "Bot henüz oluşturulmadı — ayarları kaydedin."
        if status == "error":
            return False, f"Docker durumu okunamadı: {detail}"
        return False, f"Bot durduruldu (durum: {status})."
