"""IK Otomasyonu view'lari — Portal'in kendi native sayfalari (iframe yok)."""
from __future__ import annotations

from datetime import date

from django.contrib import messages
from django.shortcuts import redirect, render
from django.views import View

from apps.inventory.mixins import AdminRequiredMixin

from .models import HrEmployee, HrSettings
from .services import reminder_service
from .services.date_service import upcoming_trigger_date
from .services.pdf_service import read_employees_from_pdf

SORT_FIELDS = {
    "full_name": "full_name",
    "department": "department",
    "role": "role",
    "hire_date": "hire_date",
    "birth_date": "birth_date",
    "blood_type": "blood_type",
}


class DashboardView(AdminRequiredMixin, View):
    def get(self, request):
        query = request.GET.get("q", "").strip()
        sort = request.GET.get("sort", "full_name")
        direction = request.GET.get("dir", "asc")

        employees = HrEmployee.objects.all()
        if query:
            employees = employees.filter(full_name__icontains=query)

        order_field = SORT_FIELDS.get(sort, "full_name")
        if direction == "desc":
            order_field = f"-{order_field}"
        employees = employees.order_by(order_field)

        today = date.today()
        settings = HrSettings.load()

        return render(request, "hr/dashboard.html", {
            "employees": employees,
            "settings": settings,
            "query": query,
            "sort": sort,
            "dir": direction,
            "sort_columns": [
                ("full_name", "Ad Soyad"),
                ("department", "Departman"),
                ("role", "Rol/Unvan"),
                ("hire_date", "İşe Giriş Tarihi"),
                ("birth_date", "Doğum Tarihi"),
                ("blood_type", "Kan Grubu"),
            ],
            "summary": {
                "total": HrEmployee.objects.count(),
                "birthdays_this_month": HrEmployee.objects.filter(birth_date__month=today.month).count(),
                "anniversaries_this_month": sum(
                    1 for e in HrEmployee.objects.filter(hire_date__month=today.month)
                    if (today.year - e.hire_date.year) >= 3 and (today.year - e.hire_date.year) % 3 == 0
                ),
                "last_reminder_sent_at": settings.last_reminder_sent_at,
            },
            "next_trigger_date": upcoming_trigger_date(today),
        })


class UploadView(AdminRequiredMixin, View):
    def post(self, request):
        uploaded = request.FILES.get("pdf")
        if not uploaded:
            messages.error(request, "PDF dosyası seçilmedi. Lütfen bir dosya seçip yeniden deneyin.")
            return redirect("hr:dashboard")

        if not (uploaded.name or "").lower().endswith(".pdf"):
            messages.error(request, "Yalnızca PDF dosyaları kabul edilir.")
            return redirect("hr:dashboard")

        try:
            data = read_employees_from_pdf(uploaded)
        except ImportError:
            messages.error(request, "Sunucuda PDF okuma bileşenlerinden biri kurulu değil. Sistem yöneticisine bildirin.")
            return redirect("hr:dashboard")
        except ValueError as exc:
            messages.error(request, str(exc))
            return redirect("hr:dashboard")
        except Exception as exc:  # noqa: BLE001 — PDF kütüphaneleri çok çeşitli hata sınıfı fırlatabilir
            messages.error(request, f"PDF okunamadı; dosya bozuk olabilir. (Ayrıntı: {exc})")
            return redirect("hr:dashboard")

        HrEmployee.objects.all().delete()
        HrEmployee.objects.bulk_create([
            HrEmployee(
                full_name=e["full_name"],
                department=e["department"],
                role=e["role"],
                hire_date=e["hire_date"],
                work_model=e["work_model"],
                birth_date=e["birth_date"],
                blood_type=e["blood_type"],
                allergy_info=e["allergy_info"],
                import_confidence=e["confidence"],
            )
            for e in data["employees"]
        ])

        messages.success(
            request,
            f"{len(data['employees'])} çalışan PDF'ten okunup kaydedildi "
            f"(kullanılan motor: {data['engine_used']}).",
        )
        if data["missing_columns"]:
            messages.warning(
                request,
                f"PDF'te bulunamayan sütunlar: {', '.join(data['missing_columns'])}. Bu alanlar boş kaydedildi.",
            )
        if data["low_confidence"]:
            names = ", ".join(f"{name} (%{score})" for name, score in data["low_confidence"])
            messages.warning(request, f"Güven skoru %80'in altında olan çalışanlar: {names}")
        if data["warnings"]:
            messages.warning(
                request,
                f"{len(data['warnings'])} alan eksik/belirsiz okundu — ayrıntılar sunucu loglarında "
                "(logger: hr.pdf_parser).",
            )
        return redirect("hr:dashboard")


class SettingsView(AdminRequiredMixin, View):
    def post(self, request):
        settings = HrSettings.load()
        settings.sender_email = request.POST.get("senderEmail", "").strip()
        settings.recipient_emails = [
            e.strip() for e in request.POST.get("recipientEmails", "").replace(",", "\n").split("\n") if e.strip()
        ]
        settings.smtp_host = request.POST.get("smtpHost", "").strip()
        settings.smtp_port = int(request.POST.get("smtpPort") or 0) or None
        settings.smtp_user = request.POST.get("smtpUser", "").strip()
        new_pass = request.POST.get("smtpPass", "").strip()
        if new_pass:
            settings.smtp_pass = new_pass
        settings.smtp_secure = request.POST.get("smtpSecure") == "true"
        settings.mail_from = request.POST.get("mailFrom", "").strip()

        settings.notifications_enabled = request.POST.get("notificationsEnabled") == "on"
        settings.notification_email = request.POST.get("notificationEmail", "").strip()

        settings.save()

        messages.success(
            request,
            f"Ayarlar kaydedildi. Bildirimler: {'Açık' if settings.notifications_enabled else 'Kapalı'}, "
            f"Bildirim e-postası: {settings.notification_email or '-'}",
        )
        return redirect("hr:dashboard")


class SendThisMonthReminderView(AdminRequiredMixin, View):
    def post(self, request):
        try:
            result = reminder_service.run_manual_test_reminder()
            simulated = result["simulated_today"].strftime("%d.%m.%Y")
            messages.success(
                request,
                f"Bu ayın hatırlatması gönderildi (simüle edilen tetikleme tarihi: {simulated} — "
                f"{result['birthdays']} doğum günü, {result['anniversaries']} iş yıldönümü kaydı). "
                "Çalışan kayıtları, bildirim geçmişi ve zamanlayıcı etkilenmedi.",
            )
        except ValueError as exc:
            messages.error(request, str(exc))
        except Exception as exc:  # noqa: BLE001 — son güvenlik ağı: hiçbir hata Django hata sayfasına düşmesin
            messages.error(request, f"Hatırlatma gönderilemedi: {exc}")
        return redirect("hr:dashboard")
