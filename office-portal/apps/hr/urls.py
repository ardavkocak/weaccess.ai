"""IK Otomasyonu URL yapisi."""
from django.urls import path

from . import views

app_name = "hr"

urlpatterns = [
    path("", views.DashboardView.as_view(), name="dashboard"),
    path("pdf-yukle/", views.UploadView.as_view(), name="upload"),
    path("ayarlar/", views.SettingsView.as_view(), name="settings"),
    path("bu-ayin-hatirlatmasini-gonder/", views.SendThisMonthReminderView.as_view(), name="send_this_month_reminder"),
]
