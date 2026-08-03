"""Discord Bot (Hatırlatıcı) URL yapısı."""
from django.urls import path

from . import views

app_name = "discordbot"

urlpatterns = [
    path("", views.DashboardView.as_view(), name="dashboard"),
]
