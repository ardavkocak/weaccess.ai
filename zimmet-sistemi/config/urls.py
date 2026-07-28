"""Zimmet Sistemi ana URL yapilandirmasi."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("apps.accounts.urls", namespace="accounts")),
    path("envanter/", include("apps.inventory.urls", namespace="inventory")),
    path("", include("apps.dashboard.urls", namespace="dashboard")),
]

handler403 = "apps.inventory.views.error_403_view"
handler404 = "apps.inventory.views.error_404_view"
handler500 = "apps.inventory.views.error_500_view"

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
