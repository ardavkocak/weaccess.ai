"""IK Otomasyonu view'lari — Portal'in kendi native sayfalari (iframe yok)."""
from __future__ import annotations

from django.contrib import messages
from django.shortcuts import redirect, render
from django.views import View

from apps.inventory.mixins import AdminRequiredMixin

from .models import HrImport, HrSettings
from .services import reminder_service
from .services.excel_service import read_employees


class DashboardView(AdminRequiredMixin, View):
    def get(self, request):
        dataset = HrImport.objects.first()
        return render(request, "hr/dashboard.html", {
            "headers": dataset.headers if dataset else [],
            "employees": dataset.employees if dataset else [],
            "settings": HrSettings.load(),
        })


class UploadView(AdminRequiredMixin, View):
    def post(self, request):
        uploaded = request.FILES.get("excel")
        if not uploaded:
            messages.error(request, "Dosya seçilmedi. Lütfen .xlsx veya .csv dosyasını seçip yeniden deneyin.")
            return redirect("hr:dashboard")

        try:
            data = read_employees(uploaded)
        except ValueError as exc:
            messages.error(request, str(exc))
            return redirect("hr:dashboard")

        HrImport.objects.all().delete()
        HrImport.objects.create(headers=data["headers"], employees=data["employees"])

        message = f"{len(data['employees'])} çalışan yüklendi."
        if data["missing"]:
            messages.warning(request, f"Excel başlıklarında eksik alanlar: {', '.join(data['missing'])}. Bu alanlar boş kaydedildi.")
        messages.success(request, message)
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
        settings.save()

        messages.success(
            request,
            f"Ayarlar kaydedildi. Gönderen: {settings.sender_email or '-'}, "
            f"Alıcılar: {', '.join(settings.recipient_emails) or '-'}",
        )
        return redirect("hr:dashboard")


class TestReminderView(AdminRequiredMixin, View):
    def post(self, request):
        try:
            result = reminder_service.run_test_reminders()
            messages.success(
                request,
                f"Test başarılı: İK adresine 2 test e-postası gönderildi "
                f"({result['birthdays']} doğum günü, {result['anniversaries']} plaket kaydı).",
            )
        except ValueError as exc:
            messages.error(request, str(exc))
        return redirect("hr:dashboard")
