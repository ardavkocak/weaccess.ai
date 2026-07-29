"""IK Otomasyonu URL yapisi."""
from django.urls import path

from . import views

app_name = "hr"

urlpatterns = [
    path("", views.DashboardView.as_view(), name="dashboard"),
    path("excel-yukle/", views.UploadView.as_view(), name="upload"),
    path("ayarlar/", views.SettingsView.as_view(), name="settings"),
    path("hatirlatmalari-test-et/", views.TestReminderView.as_view(), name="test_reminders"),
]
