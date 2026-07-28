"""Kullanici (giris yapan hesap) modeli."""
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Sistemdeki giris yapan hesaplari temsil eder.

    Employee modeli calisanin ozluk bilgilerini tutarken, User modeli
    yalnizca kimlik dogrulama ve rol bilgisini tasir. Bir Employee kaydi
    isterse bir User hesabina baglanabilir (apps.inventory.Employee.user).
    """

    class Role(models.TextChoices):
        ADMIN = "admin", "Yonetici"
        STAFF = "staff", "Personel"

    role = models.CharField(
        max_length=10, choices=Role.choices, default=Role.STAFF, verbose_name="Rol"
    )
    phone_number = models.CharField(max_length=20, blank=True, verbose_name="Telefon")
    last_seen = models.DateTimeField(null=True, blank=True, verbose_name="Son Gorulme")
    must_change_password = models.BooleanField(
        default=False,
        verbose_name="Sifre Degistirmeli",
        help_text=(
            "Calisan eklenirken uretilen otomatik sifre (ad + 123) tahmin edilebilir "
            "oldugundan, hesap sahibi kendi sifresini belirleyene kadar bu bayrak acik "
            "kalir ve diger sayfalara erisim engellenir."
        ),
    )

    class Meta:
        verbose_name = "Kullanici"
        verbose_name_plural = "Kullanicilar"
        ordering = ["username"]

    def __str__(self):
        return self.get_full_name() or self.username

    @property
    def is_admin_role(self):
        return self.role == self.Role.ADMIN

    @property
    def is_staff_role(self):
        return self.role == self.Role.STAFF
