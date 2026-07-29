"""Yonetim paneli (dashboard) view'i.

Admin rolundeki kullanicilar icin ozet istatistik kartlarini ve son zimmet
kayitlarini gosterir. Personel rolundeki kullanicilar kendi zimmet ekranlarina
yonlendirilir.
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from django.shortcuts import redirect
from django.utils import timezone
from django.views.generic import TemplateView

from apps.inventory.models import Assignment, Company, Device, Employee


class DashboardView(LoginRequiredMixin, TemplateView):
    # Office Portal'ın kendi Dashboard'u "dashboard/dashboard.html" adını
    # zaten kullandığı için bu şablon "zimmet/" altına taşındı (bkz.
    # office-portal/templates/zimmet/dashboard.html). Orijinal zimmet-sistemi
    # projesindeki dosya adı/yolu değişmedi, yalnızca bu kopyada değişti.
    template_name = "zimmet/dashboard.html"

    def get(self, request, *args, **kwargs):
        if not request.user.is_admin_role:
            return redirect("inventory:my-assignments")
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Stok mantigi: toplam adet Device'tan, zimmetteki adet aktif
        # Assignment kayitlarindan gelir; bosta adet ikisinin farkidir.
        total_quantity = Device.objects.aggregate(total=Sum("total_quantity"))["total"] or 0
        assigned_quantity = Assignment.objects.filter(returned=False).count()

        context.update(
            {
                "total_device_types": Device.objects.count(),
                "total_quantity": total_quantity,
                "assigned_quantity": assigned_quantity,
                "available_quantity": max(total_quantity - assigned_quantity, 0),
                "total_employees": Employee.objects.filter(is_active=True).count(),
                "total_companies": Company.objects.count(),
                "overdue_assignment_count": Assignment.objects.filter(
                    returned=False, expected_return_date__lt=timezone.localdate()
                ).count(),
                "recent_assignments": Assignment.objects.select_related("employee", "device").order_by(
                    "-created_at"
                )[:5],
            }
        )
        return context
