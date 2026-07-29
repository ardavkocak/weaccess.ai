"""
Dokumantasyon Otomasyonu — Portal'in kendi native sayfasi.

`scraper.py` ve `sheets_export.py`, orijinal projeden HICBIR SATIR
DEGISTIRILMEDEN kopyalanmistir (bkz. ayni klasor) — asil is mantigi
(tarama, kategorilendirme, Google Sheets'e yazma) aynen yeniden kullanilir.
Bu dosya yalnizca Flask form akisini Django view'ina cevirir.
"""
from __future__ import annotations

import os

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View

from . import scraper
from .models import SheetsSettings
from .sheets_export import sheets_e_yaz


def _servis_hesabi():
    """Veritabanındaki ayar önceliklidir; boşsa .env'e (eski davranış) düşer."""
    kayitli = SheetsSettings.get_solo().service_account_json.strip()
    if kayitli:
        return kayitli
    return os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "service_account.json")


def _sheets_url():
    kayitli = SheetsSettings.get_solo().sheets_url.strip()
    if kayitli:
        return kayitli
    return os.environ.get("GOOGLE_SHEETS_URL", "")


def _servis_hesabi_tanimli_mi():
    servis_hesabi = _servis_hesabi()
    if servis_hesabi.strip().startswith("{"):
        return True
    return os.path.exists(servis_hesabi)


class DashboardView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, "documentation/dashboard.html", {"sonuc": None, "hata": None})

    def post(self, request):
        banka_adi = (request.POST.get("banka_adi") or "").strip()
        sayfa_url = (request.POST.get("sayfa_url") or "").strip()
        zorla_tarayici = request.POST.get("zorla_tarayici") == "on"

        sonuc = None
        hata = None

        if not banka_adi or not sayfa_url:
            hata = "Banka adı ve sayfa URL'si zorunludur."
        elif not _sheets_url():
            hata = "GOOGLE_SHEETS_URL tanımlı değil. Lütfen .env dosyasını yapılandırın."
        elif not _servis_hesabi_tanimli_mi():
            hata = f"Servis hesabı bilgisi bulunamadı: {_servis_hesabi()}."
        else:
            try:
                belgeler = scraper.kaz(sayfa_url, zorla_tarayici=zorla_tarayici)
                if not belgeler:
                    hata = "Sayfada hiç doküman (PDF/DOC/XLS) bağlantısı bulunamadı. 'Tarayıcı ile aç (JS)' seçeneğini işaretleyip tekrar deneyin."
                else:
                    sekme_url = sheets_e_yaz(
                        belgeler=belgeler,
                        spreadsheet_url_veya_id=_sheets_url(),
                        banka_adi=banka_adi,
                        servis_hesabi=_servis_hesabi(),
                    )
                    sozlesme = sum(1 for b in belgeler if b.kategori == "Sözleşme")
                    form = sum(1 for b in belgeler if b.kategori == "Form")
                    diger = len(belgeler) - sozlesme - form
                    sonuc = {
                        "banka_adi": banka_adi,
                        "toplam": len(belgeler),
                        "sozlesme": sozlesme,
                        "form": form,
                        "diger": diger,
                        "sekme_url": sekme_url,
                        "belgeler": belgeler,
                    }
            except Exception as exc:  # noqa: BLE001 — orijinal Flask app.py ile ayni genis yakalama
                hata = f"İşlem sırasında hata oluştu: {exc}"

        return render(request, "documentation/dashboard.html", {"sonuc": sonuc, "hata": hata})


class SettingsView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Google Sheets baglanti ayarlari (URL + servis hesabi JSON).

    Bu bilgiler bir Google service account private key'i icerdigi icin
    yalnizca Yonetici rolundeki kullanicilar erisebilir.
    """

    login_url = reverse_lazy("accounts:login")

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_admin_role

    def get(self, request):
        ayar = SheetsSettings.get_solo()
        return render(request, "documentation/settings.html", {"ayar": ayar})

    def post(self, request):
        ayar = SheetsSettings.get_solo()
        ayar.sheets_url = (request.POST.get("sheets_url") or "").strip()
        ayar.service_account_json = (request.POST.get("service_account_json") or "").strip()
        ayar.save()
        messages.success(request, "Google Sheets ayarları güncellendi.")
        return redirect("documentation:settings")
