"""Aylik Takip URL yapisi."""
from django.urls import path

from . import views

app_name = "monthly_tracking"

urlpatterns = [
    path("", views.DashboardView.as_view(), name="dashboard"),
]
