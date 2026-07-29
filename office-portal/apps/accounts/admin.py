"""Kullanici modeli icin ozellestirilmis Django Admin yapilandirmasi."""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ("username", "email", "first_name", "last_name", "role", "is_active", "last_seen")
    list_filter = ("role", "is_active", "is_staff")
    search_fields = ("username", "email", "first_name", "last_name")
    ordering = ("username",)
    readonly_fields = ("last_login", "date_joined", "last_seen")

    fieldsets = UserAdmin.fieldsets + (
        ("Sistem Rolu", {"fields": ("role", "phone_number", "last_seen")}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Sistem Rolu", {"fields": ("role", "phone_number", "email")}),
    )
