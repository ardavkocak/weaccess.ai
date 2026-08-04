"""Portal uygulamasinin URL yapisi."""
from django.urls import path

from . import views

app_name = "portal"

urlpatterns = [
    path("", views.DashboardView.as_view(), name="dashboard"),
    # Genel "operasyonlar/<slug>/" placeholder rotasi: yalnizca `url_name`
    # tanimlanmamis (henuz var olmayan) moduller icin bir guvenlik agidir.
    path("operasyonlar/<slug:slug>/", views.ModulePlaceholderView.as_view(), name="module"),
]
