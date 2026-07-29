"""Ofis Portali ana URL yapilandirmasi."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    # --- Zimmet Sistemi entegrasyonu (Faz 2) ---
    # Kimlik dogrulama artik apps.accounts'un kendi view'lari uzerinden
    # yapilir (e-posta ile giris, "beni hatirla", sifre sifirlama, zorunlu
    # sifre degistirme). Portal'in kendi basit login/logout URL'leri kaldirildi.
    path("accounts/", include("apps.accounts.urls", namespace="accounts")),
    path("envanter/", include("apps.inventory.urls", namespace="inventory")),
    path("operasyonlar/zimmet/", include("apps.dashboard.urls", namespace="dashboard")),
    # --- Faz 3: Ofis Gorev Takibi + Yemek Sistemi (Portal'in kendi sayfalari) ---
    path("operasyonlar/", include("apps.office_bot.urls", namespace="office_bot")),
    path("operasyonlar/ik-otomasyon/", include("apps.hr.urls", namespace="hr")),
    path("operasyonlar/dokumantasyon/", include("apps.documentation.urls", namespace="documentation")),
    path("operasyonlar/aylik-takip/", include("apps.monthly_tracking.urls", namespace="monthly_tracking")),
    path("", include("portal.urls")),
]

handler403 = "apps.inventory.views.error_403_view"
handler404 = "apps.inventory.views.error_404_view"
handler500 = "apps.inventory.views.error_500_view"

if settings.DEBUG:
    # Calisan profil fotograflari (Employee.profile_photo) gelistirme
    # ortaminda Django'nun kendisi tarafindan sunulur.
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
