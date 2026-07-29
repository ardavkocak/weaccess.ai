"""Dokumantasyon Otomasyonu URL yapisi."""
from django.urls import path

from . import views

app_name = "documentation"

urlpatterns = [
    path("", views.DashboardView.as_view(), name="dashboard"),
    path("ayarlar/", views.SettingsView.as_view(), name="settings"),
]
