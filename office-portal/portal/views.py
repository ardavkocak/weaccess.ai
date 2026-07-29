"""
Portal kabuk uygulamasinin view'lari.

Faz 3 (v1.1) tamamlandi: Zimmet, Gorev Takibi, Yemek Sistemi, IK Otomasyonu,
Aylik Takip ve Dokumantasyon Otomasyonu artik hepsi kendi native Django
uygulamalarina (apps.*) sahip. Bu dosyada iframe veya harici port
yonlendirmesi yapan HICBIR view kalmadi; yalnizca Dashboard ve genel
placeholder/guvenlik agi kaldi.
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.shortcuts import render
from django.views import View

from .modules import MODULES, get_module, get_module_status, get_module_url


class DashboardView(LoginRequiredMixin, View):
    """Portal acildiginda gorunen tek sayfa: modul kartlarinin oldugu ana panel."""

    def get(self, request):
        modules_with_status = []
        for module in MODULES:
            entry = dict(module)
            entry["link_url"] = get_module_url(module)
            entry["status_ok"], entry["status_message"] = get_module_status(module)
            modules_with_status.append(entry)
        return render(request, "dashboard/dashboard.html", {"modules": modules_with_status})


class ModulePlaceholderView(LoginRequiredMixin, View):
    """
    Operasyonlar altindaki her modul icin ortak bos sayfa.

    Yalnizca `url_name` TANIMLANMAMIS moduller (henuz entegre edilmemis,
    ileride eklenecek moduller) buraya duser. Mevcut 6 modulun hepsi artik
    kendi native view'ina sahip oldugu icin bu view pratikte calismaz; ama
    Portal'in "tanimadigi" bir modul eklendiginde hata VERMEDEN calismaya
    devam etmesini saglayan guvenlik agidir (bkz. modules.py docstring'i).
    """

    def get(self, request, slug):
        module = get_module(slug)
        if module is None:
            raise Http404("Modül bulunamadı.")

        integration_ok, integration_message = get_module_status(module)
        return render(
            request,
            "modules/placeholder.html",
            {
                "module": module,
                "integration_ok": integration_ok,
                "integration_message": integration_message,
            },
        )


class StaticPlaceholderView(LoginRequiredMixin, View):
    """Raporlar/Ayarlar gibi tekil (modul listesinde olmayan) bos sayfalar icin."""

    name = ""
    icon = ""
    description = ""

    def get(self, request):
        module = {"name": self.name, "icon": self.icon, "description": self.description}
        return render(request, "modules/placeholder.html", {"module": module})


ReportsView = StaticPlaceholderView.as_view(
    name="Raporlar",
    icon="bi-bar-chart",
    description="Modüller entegre edildikçe burada ortak raporlama panosu oluşacak.",
)

SettingsView = StaticPlaceholderView.as_view(
    name="Ayarlar",
    icon="bi-gear",
    description="Portal geneli ayarlar (tema, bildirim, entegrasyon) burada yönetilecek.",
)

# Not: Portal'in kendi placeholder "Profil" sayfasi kaldirildi. Zimmet
# entegrasyonuyla birlikte gercek profil sayfasi artik apps.accounts
# uzerinden geliyor (bkz. config/urls.py -> "accounts:profile").
