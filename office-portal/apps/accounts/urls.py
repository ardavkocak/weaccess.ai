"""Hesap yonetimi URL yapilandirmasi."""
from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.CustomLoginView.as_view(), name="login"),
    path("logout/", views.CustomLogoutView.as_view(), name="logout"),
    path("profile/", views.profile_view, name="profile"),
    path("password-change/", views.password_change_view, name="password_change"),
    path("password-reset/", views.StyledPasswordResetView.as_view(), name="password_reset"),
    path("password-reset/done/", views.StyledPasswordResetDoneView.as_view(), name="password_reset_done"),
    path(
        "password-reset/confirm/<uidb64>/<token>/",
        views.StyledPasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path("password-reset/complete/", views.StyledPasswordResetCompleteView.as_view(), name="password_reset_complete"),
]
