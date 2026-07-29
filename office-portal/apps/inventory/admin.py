"""Envanter uygulamasi icin ozellestirilmis Django Admin yapilandirmasi."""
from django.contrib import admin

from .models import ActivityLog, Assignment, Company, Device, Employee, Notification


class AssignmentInline(admin.TabularInline):
    model = Assignment
    fk_name = "device"
    extra = 0
    fields = ("employee", "assigned_date", "expected_return_date", "returned", "returned_date")
    readonly_fields = ("employee", "assigned_date")
    can_delete = False
    show_change_link = True
    verbose_name = "Zimmet Gecmisi"
    verbose_name_plural = "Zimmet Gecmisi"


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("name", "employee_count", "created_at")
    search_fields = ("name",)
    ordering = ("name",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ("full_name", "email", "tc_kimlik_no", "company", "hire_date", "is_active")
    list_filter = ("company", "is_active", "hire_date")
    search_fields = ("first_name", "last_name", "email", "tc_kimlik_no")
    ordering = ("first_name", "last_name")
    autocomplete_fields = ("company", "user")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (None, {"fields": ("user", "first_name", "last_name", "email", "tc_kimlik_no")}),
        ("Is Bilgileri", {"fields": ("company", "hire_date", "is_active")}),
        ("Profil", {"fields": ("profile_photo",)}),
        ("Tarih Bilgileri", {"fields": ("created_at", "updated_at")}),
    )
    search_help_text = "Ad, soyad, e-posta veya TC kimlik no ile arayin."


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ("name", "total_quantity", "assigned_count", "available_count", "created_at")
    search_fields = ("name",)
    ordering = ("name",)
    readonly_fields = ("created_at", "updated_at")
    inlines = [AssignmentInline]
    fields = ("name", "total_quantity", "created_at", "updated_at")

    def get_queryset(self, request):
        # Listedeki stok sayaclari icin N+1 sorguyu onler.
        return super().get_queryset(request).with_stock_counts()

    @admin.display(description="Zimmette", ordering="assigned_quantity")
    def assigned_count(self, obj):
        return obj.assigned_count

    @admin.display(description="Bosta")
    def available_count(self, obj):
        return obj.available_count


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = (
        "device",
        "employee",
        "assigned_date",
        "expected_return_date",
        "returned",
        "returned_date",
        "return_condition",
    )
    list_filter = ("returned", "return_condition", "assigned_date")
    search_fields = ("device__name", "employee__first_name", "employee__last_name")
    ordering = ("-assigned_date",)
    autocomplete_fields = ("device", "employee", "assigned_by", "returned_by")
    readonly_fields = ("created_at", "updated_at")
    date_hierarchy = "assigned_date"


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "user", "action_type", "description", "ip_address")
    list_filter = ("action_type", "created_at")
    search_fields = ("description", "user__username", "ip_address")
    ordering = ("-created_at",)
    readonly_fields = ("user", "action_type", "description", "ip_address", "created_at")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "is_read", "created_at")
    list_filter = ("is_read", "created_at")
    search_fields = ("title", "message", "user__username")
    ordering = ("-created_at",)
