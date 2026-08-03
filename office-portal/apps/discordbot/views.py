from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View

from . import docker_control
from .models import DiscordBotSettings


class DashboardView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Discord bot ayarları + Başlat/Durdur/Yeniden Oluştur kontrolü.

    Bu sayfa bir Discord bot token'ı ve Google servis hesabı private key'i
    içerdiği için, ve container kontrolü host'taki Docker'a erişim sağladığı
    için, yalnızca Yönetici rolündeki kullanıcılar erişebilir.
    """

    login_url = reverse_lazy("accounts:login")

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_admin_role

    def get(self, request):
        return render(request, "discordbot/dashboard.html", self._context())

    def post(self, request):
        action = request.POST.get("action")

        if action == "save":
            self._save(request)
        elif action == "start":
            try:
                docker_control.start()
                messages.success(request, "Bot başlatıldı.")
            except Exception as exc:  # noqa: BLE001
                messages.error(request, f"Bot başlatılamadı: {exc}")
        elif action == "stop":
            try:
                docker_control.stop()
                messages.success(request, "Bot durduruldu.")
            except Exception as exc:  # noqa: BLE001
                messages.error(request, f"Bot durdurulamadı: {exc}")

        return redirect("discordbot:dashboard")

    def _save(self, request):
        ayar = DiscordBotSettings.get_solo()
        # Token alani bos birakilirsa mevcut deger korunur (arayuzde maskeli
        # gosterilir, formu her acista yeniden doldurmak guvenlik acisindan
        # yanlis olurdu); degistirmek icin kullanici yenisini girmeli.
        yeni_token = (request.POST.get("discord_token") or "").strip()
        if yeni_token:
            ayar.discord_token = yeni_token
        ayar.service_account_json = (request.POST.get("service_account_json") or "").strip()
        try:
            ayar.poll_minutes = max(1, int(request.POST.get("poll_minutes") or 30))
            ayar.stale_days = max(1, int(request.POST.get("stale_days") or 7))
        except ValueError:
            messages.error(request, "Kontrol sıklığı ve eskime eşiği sayı olmalı.")
            return
        ayar.save()

        try:
            docker_control.write_env_files(ayar)
            docker_control.rebuild_and_recreate()
            messages.success(request, "Ayarlar kaydedildi; bot yeniden oluşturulup başlatıldı.")
        except Exception as exc:  # noqa: BLE001
            messages.error(
                request,
                f"Ayarlar kaydedildi ama bot yeniden oluşturulamadı: {exc}",
            )

    def _context(self):
        ayar = DiscordBotSettings.get_solo()
        status, detail = docker_control.get_status()
        return {"ayar": ayar, "status": status, "status_detail": detail}
