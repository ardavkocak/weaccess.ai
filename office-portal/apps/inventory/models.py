"""Stok ve Zimmet Yonetim Sistemi veritabani modelleri.

Sistem cihazlari tek tek (envanter/seri no ile) degil, stok mantigiyla takip
eder: ayni urun tek bir Device satiridir ve yalnizca toplam adedi tutulur.
Kac adedin zimmette oldugu, o cihaza ait aktif Assignment kayitlarindan
hesaplanir; boylece stok sayaci ile zimmet kayitlari arasinda tutarsizlik
olusamaz.

Bu dosya sirketleri, calisanlari, cihaz stoklarini, zimmet/iade islemlerini ve
sistem uzerinde yapilan islemlerin gunlugunu (ActivityLog) tanimlar.
"""
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, RegexValidator
from django.db.models import Count, Q
from django.db import models
from django.urls import reverse
from django.utils import timezone

tc_kimlik_no_validator = RegexValidator(
    regex=r"^\d{11}$",
    message="TC Kimlik No 11 haneli olmali ve yalnizca rakam icermelidir.",
)


class TimeStampedModel(models.Model):
    """Olusturulma ve guncellenme tarihlerini otomatik tutan soyut temel model."""

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Olusturulma Tarihi")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Guncellenme Tarihi")

    class Meta:
        abstract = True


class Company(TimeStampedModel):
    """Calisanlarin bagli oldugu sirketleri temsil eder."""

    name = models.CharField(max_length=100, unique=True, verbose_name="Sirket Adi")

    class Meta:
        verbose_name = "Sirket"
        verbose_name_plural = "Sirketler"
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def employee_count(self):
        return self.employees.filter(is_active=True).count()


class Employee(TimeStampedModel):
    """Sirket calisanlarini temsil eder. Isterse bir kullanici (User) hesabina baglidir."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="employee_profile",
        verbose_name="Kullanici Hesabi",
    )
    first_name = models.CharField(max_length=50, verbose_name="Ad")
    last_name = models.CharField(max_length=50, verbose_name="Soyad")
    email = models.EmailField(unique=True, verbose_name="E-posta")
    tc_kimlik_no = models.CharField(
        max_length=11,
        unique=True,
        validators=[tc_kimlik_no_validator],
        help_text="11 haneli TC Kimlik Numarasi.",
        verbose_name="TC Kimlik No",
    )
    hire_date = models.DateField(verbose_name="Ise Giris Tarihi")
    company = models.ForeignKey(
        Company, on_delete=models.PROTECT, related_name="employees", verbose_name="Sirket"
    )
    profile_photo = models.ImageField(
        upload_to="employees/%Y/%m/", blank=True, null=True, verbose_name="Profil Fotografi"
    )
    is_active = models.BooleanField(default=True, verbose_name="Aktif Calisan")

    class Meta:
        verbose_name = "Calisan"
        verbose_name_plural = "Calisanlar"
        ordering = ["first_name", "last_name"]

    def __str__(self):
        return self.full_name

    def get_absolute_url(self):
        return reverse("inventory:employee-detail", kwargs={"pk": self.pk})

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def active_assignment_count(self):
        return self.assignments.filter(returned=False).count()


class DeviceQuerySet(models.QuerySet):
    """Device sorgularina stok sayaclarini ekleyen yardimci QuerySet."""

    def with_stock_counts(self):
        """Zimmetteki adedi tek sorguda hesaplar (N+1 sorgu olusmaz).

        Sablonlarda ve listelerde `assigned_count` / `available_count`
        ozelliklerinin ek sorgu acmadan calismasini saglar.
        """
        return self.annotate(
            assigned_quantity=Count("assignments", filter=Q(assignments__returned=False))
        )

    def with_available_stock(self):
        """Yalnizca zimmetlenebilecek (bosta adedi olan) cihazlari dondurur."""
        return self.with_stock_counts().filter(total_quantity__gt=models.F("assigned_quantity"))


class Device(TimeStampedModel):
    """Bir cihaz urununun stok kaydi.

    Sistem tek tek fiziksel birimleri degil, urun bazinda stogu takip eder:
    ornegin "Apple MacBook Air M4" tek bir satirdir ve toplam adedi tutar.
    Zimmetteki adet, aktif Assignment kayitlarindan hesaplandigi icin ayrica
    saklanmaz.
    """

    name = models.CharField(max_length=150, unique=True, verbose_name="Cihaz Adi")
    total_quantity = models.PositiveIntegerField(
        default=1, validators=[MinValueValidator(0)], verbose_name="Toplam Adet"
    )

    objects = DeviceQuerySet.as_manager()

    class Meta:
        verbose_name = "Cihaz"
        verbose_name_plural = "Cihazlar"
        ordering = ["name"]
        indexes = [models.Index(fields=["name"])]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("inventory:device-detail", kwargs={"pk": self.pk})

    @property
    def assigned_count(self):
        """Zimmette olan adet. with_stock_counts() ile gelen deger varsa onu kullanir."""
        annotated = getattr(self, "assigned_quantity", None)
        if annotated is not None:
            return annotated
        return self.assignments.filter(returned=False).count()

    @property
    def available_count(self):
        """Bostaki adet. Negatif olmamasi icin alt sinir 0'dir."""
        return max(self.total_quantity - self.assigned_count, 0)

    @property
    def stock_badges(self):
        """Durum sutununda gosterilecek otomatik rozetler.

        Durum kullanici tarafindan girilmez; toplam adet ile zimmetteki adetten
        turetilir.
        """
        total, assigned, available = self.total_quantity, self.assigned_count, self.available_count
        if total == 0:
            return [("Stok Yok", "muted")]
        if available == 0:
            return [("Tamami Zimmette", "warning")]
        if assigned == 0:
            return [(f"Bosta ({available})", "success")]
        return [(f"Bosta ({available})", "success"), (f"Zimmette ({assigned})", "info")]

    def clean(self):
        """Toplam adet, zimmetteki adedin altina dusurulemez."""
        if self.pk and self.total_quantity is not None:
            assigned = self.assignments.filter(returned=False).count()
            if self.total_quantity < assigned:
                raise ValidationError(
                    {
                        "total_quantity": (
                            f"Bu cihazdan {assigned} adet zimmette oldugu icin toplam adet "
                            f"{assigned} degerinin altina dusurulemez."
                        )
                    }
                )


class Assignment(TimeStampedModel):
    """Bir cihazin bir calisana zimmetlenmesi (teslim/iade) surecini temsil eder."""

    class ReturnCondition(models.TextChoices):
        UNDAMAGED = "undamaged", "Hasarsiz Teslim Edildi"
        DAMAGED = "damaged", "Hasarli Teslim Edildi"
        MISSING = "missing", "Eksik Teslim Edildi"

    employee = models.ForeignKey(
        Employee, on_delete=models.PROTECT, related_name="assignments", verbose_name="Calisan"
    )
    device = models.ForeignKey(
        Device, on_delete=models.PROTECT, related_name="assignments", verbose_name="Cihaz"
    )
    assigned_date = models.DateField(default=timezone.localdate, verbose_name="Teslim Tarihi")
    expected_return_date = models.DateField(null=True, blank=True, verbose_name="Beklenen Iade Tarihi")
    returned_date = models.DateField(null=True, blank=True, verbose_name="Gercek Iade Tarihi")
    notes = models.TextField(blank=True, verbose_name="Teslim Notu")
    return_notes = models.TextField(blank=True, verbose_name="Iade Notu")
    return_condition = models.CharField(
        max_length=20,
        choices=ReturnCondition.choices,
        blank=True,
        verbose_name="Iade Durumu",
    )
    damage_description = models.TextField(blank=True, verbose_name="Hasar / Eksik Aciklamasi")
    returned = models.BooleanField(default=False, verbose_name="Iade Edildi mi")
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assignments_created",
        verbose_name="Teslim Eden",
    )
    returned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assignments_returned",
        verbose_name="Iadeyi Alan",
    )

    class Meta:
        verbose_name = "Zimmet"
        verbose_name_plural = "Zimmetler"
        ordering = ["-assigned_date", "-created_at"]

    def __str__(self):
        return f"{self.device} -> {self.employee}"

    def get_absolute_url(self):
        return reverse("inventory:assignment-detail", kwargs={"pk": self.pk})

    def clean(self):
        """Stokta bosta adet kalmamissa yeni zimmet olusturulmasini engeller.

        Stok mantiginda ayni cihazdan birden fazla kisiye zimmet verilebilir;
        sinir, cihazin toplam adedidir. Cihaz henuz secilmemisse kontrol
        atlanir; zorunlu alan hatasini alan dogrulamasi zaten uretir.
        """
        if self.returned or not self.device_id:
            return
        active_count = (
            Assignment.objects.filter(device_id=self.device_id, returned=False).exclude(pk=self.pk).count()
        )
        if active_count >= self.device.total_quantity:
            raise ValidationError(
                {"device": "Bu cihazin tum adedi zimmette. Once bir iade alinmalidir."}
            )

    @property
    def is_overdue(self):
        if self.returned or not self.expected_return_date:
            return False
        return timezone.localdate() > self.expected_return_date


class ActivityLog(models.Model):
    """Sistemde gerceklestirilen tum onemli islemlerin denetim kaydini tutar."""

    class ActionType(models.TextChoices):
        CREATE = "create", "Olusturma"
        UPDATE = "update", "Guncelleme"
        DELETE = "delete", "Silme"
        LOGIN = "login", "Giris"
        LOGOUT = "logout", "Cikis"
        ASSIGN = "assign", "Zimmetleme"
        RETURN = "return", "Iade"
        OTHER = "other", "Diger"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="activity_logs",
        verbose_name="Kullanici",
    )
    action_type = models.CharField(max_length=20, choices=ActionType.choices, verbose_name="Islem Tipi")
    description = models.CharField(max_length=255, verbose_name="Aciklama")
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP Adresi")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Tarih")

    class Meta:
        verbose_name = "Sistem Hareketi"
        verbose_name_plural = "Sistem Hareketleri"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["-created_at"])]

    def __str__(self):
        return f"[{self.get_action_type_display()}] {self.description}"


class Notification(models.Model):
    """Kullanicilara gosterilecek sistem bildirimleri (garanti bitimi, gecikmis iade vb.)."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications", verbose_name="Kullanici"
    )
    title = models.CharField(max_length=150, verbose_name="Baslik")
    message = models.CharField(max_length=255, verbose_name="Mesaj")
    link = models.CharField(max_length=255, blank=True, verbose_name="Baglanti")
    is_read = models.BooleanField(default=False, verbose_name="Okundu mu")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Olusturulma Tarihi")

    class Meta:
        verbose_name = "Bildirim"
        verbose_name_plural = "Bildirimler"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
