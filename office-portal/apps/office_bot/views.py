"""
office_bot view'lari — Ofis Gorev Takibi + Yemek Sistemi'nin Portal icindeki
NATIF sayfalari. Hicbir view iframe veya harici port yonlendirmesi yapmaz;
tum CRUD islemleri burada, Django ORM uzerinden ayni SQLite dosyasina
(bkz. router.py) dogrudan yapilir.

Yetkilendirme: Zimmet'in AdminRequiredMixin'i (apps.inventory.mixins) aynen
yeniden kullanilir — Portal genelinde "yonetim ekranlari yalnizca admin
rolune acik" kurali tek yerden gelir, tekrar yazilmaz.
"""
from __future__ import annotations

import logging
import re

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from apps.inventory.mixins import AdminRequiredMixin

from . import models
from .forms import EmployeeForm, MealUploadForm

log = logging.getLogger("office_bot.views")
from .services import (
    discord_client,
    duty_confirmation_service,
    employee_service,
    history_service,
    meal_import,
    meal_messages,
    meal_service,
    meal_vote_service,
    rotation_service,
    schedule_service,
    settings_service,
)
from .services.date_utils import add_days, now_hhmm, previous_working_day, today_iso

# Yemek Sistemi yönetim ekranı: Portal'dan gönderilen anketin hangi (GERÇEK)
# menü gününe ait olduğunu ve Discord'daki mesajının nerede durduğunu hatırlamak
# için kullanılan Settings anahtarları. Yeni bir tabloya gerek yok — mevcut
# anahtar/değer `settings` tablosu (bkz. settings_service) yeterli.
MEAL_TRACKED_DATE_KEY = "meal_admin_message_date"
MEAL_TRACKED_CHANNEL_KEY = "meal_admin_message_channel_id"
MEAL_TRACKED_MESSAGE_KEY = "meal_admin_message_id"
MEAL_TRACKED_CLOSED_KEY = "meal_admin_message_closed"

# Yemek bildirim zamanlaması: AYNI anahtarlar Node botunun mealScheduler.js'i
# tarafından da okunur (bkz. ofis-gorev-takibi/src/cron/mealScheduler.js).
# Anahtar adları BİREBİR aynı olmalı — iki taraf da aynı `settings` tablosunu
# paylaşıyor; Node her dakika bu değerleri yeniden okuyarak zamanlamayı
# uygular, bu yüzden Portal'dan kaydetmek sunucunun yeniden başlatılmasını
# gerektirmez (bkz. mealScheduler.js dosya başlığındaki mimari not).
MEAL_SCHEDULE_TIME_KEY = "meal_notify_time"
MEAL_SCHEDULE_ENABLED_KEY = "meal_notify_enabled"
MEAL_SCHEDULE_DEFAULT_TIME = "10:00"
_TIME_PATTERN = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")


def _decorate_menu(menu):
    """Bir menu dict'ine (meal_service._hydrate çıktısı) gösterim alanları ekler."""
    if not menu:
        return None
    items = [
        {**item, "icon": meal_messages.icon_for(item["name"])}
        for item in menu["items"]
    ]
    return {
        **menu,
        "items": items,
        "total_kcal": meal_messages.total_kcal(menu["items"]),
        "is_open": meal_vote_service.is_open(menu["row"].menu_date),
    }


def _default_duty_type():
    return models.DutyType.objects.filter(key="tea").first() or models.DutyType.objects.first()


class DutyDashboardView(AdminRequiredMixin, View):
    """'Görev Takibi' ana sayfası — bugünkü görevli, sıra, hızlı erişim."""

    def get(self, request):
        duty_type = _default_duty_type()
        if not duty_type:
            return render(request, "office_bot/duty_dashboard.html", {"duty_type": None})

        overview = rotation_service.get_overview(duty_type.id)
        return render(request, "office_bot/duty_dashboard.html", {
            "duty_type": duty_type,
            "overview": overview,
            "counts": employee_service.get_counts(),
            "recent_history": history_service.get_recent(5),
            "confirmation_status": duty_confirmation_service.get_today_status(duty_type.id),
        })

    def post(self, request):
        """'Sırayı Geç' butonu."""
        duty_type = _default_duty_type()
        if duty_type:
            result = rotation_service.skip_to_next(duty_type.id)
            if result["ok"]:
                messages.success(request, result["message"])
            else:
                messages.error(request, result["message"])
        return redirect("office_bot:duty_dashboard")


class QueueView(AdminRequiredMixin, View):
    """'Görev Sırası' sayfası — tam sıra listesi + yukarı/aşağı taşıma."""

    def get(self, request):
        duty_type = _default_duty_type()
        if not duty_type:
            return render(request, "office_bot/queue.html", {"duty_type": None})
        return render(request, "office_bot/queue.html", {
            "duty_type": duty_type,
            "overview": rotation_service.get_overview(duty_type.id),
        })


class EmployeeListView(AdminRequiredMixin, View):
    """Personel listesi + ekleme formu (tek sayfa, orijinal panelle aynı düzen)."""

    def get(self, request):
        return render(request, "office_bot/employees.html", {
            "employees": employee_service.get_all(),
            "counts": employee_service.get_counts(),
            "form": EmployeeForm(),
            "editing": None,
        })

    def post(self, request):
        form = EmployeeForm(request.POST)
        errors, data = employee_service.validate(request.POST)

        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, "office_bot/employees.html", {
                "employees": employee_service.get_all(),
                "counts": employee_service.get_counts(),
                "form": form,
                "editing": None,
            }, status=400)

        position = str(request.POST.get("position") or "").strip()
        employee = employee_service.create(data, position or None)

        duty_type = _default_duty_type()
        if duty_type:
            rotation_service.resolve_current(duty_type.id)

        is_last = employee.position == employee_service.get_total()
        messages.success(
            request,
            f"{employee.full_name} sıranın sonuna eklendi." if is_last
            else f"{employee.full_name} {employee.position}. sıraya eklendi. Sonraki personeller bir basamak kaydırıldı.",
        )
        return redirect("office_bot:employee_list")


class EmployeeEditView(AdminRequiredMixin, View):
    def get(self, request, pk):
        employee = get_object_or_404(models.Employee, pk=pk)
        form = EmployeeForm(initial={
            "full_name": employee.full_name,
            "discord_user_id": employee.discord_user_id or "",
            "is_active": employee.is_active == 1,
            "company": employee.company or "",
        })
        return render(request, "office_bot/employees.html", {
            "employees": employee_service.get_all(),
            "counts": employee_service.get_counts(),
            "form": form,
            "editing": employee,
        })

    def post(self, request, pk):
        employee = get_object_or_404(models.Employee, pk=pk)
        errors, data = employee_service.validate(request.POST, exclude_id=pk)

        if errors:
            for error in errors:
                messages.error(request, error)
            form = EmployeeForm(request.POST)
            return render(request, "office_bot/employees.html", {
                "employees": employee_service.get_all(),
                "counts": employee_service.get_counts(),
                "form": form,
                "editing": employee,
            }, status=400)

        updated = employee_service.update(pk, data)
        duty_type = _default_duty_type()
        if duty_type:
            rotation_service.resolve_current(duty_type.id)

        messages.success(request, f"{updated.full_name} güncellendi.")
        return redirect("office_bot:employee_list")


class EmployeeToggleView(AdminRequiredMixin, View):
    def post(self, request, pk):
        employee = employee_service.toggle_active(pk)
        if not employee:
            messages.error(request, "Çalışan bulunamadı.")
            return redirect("office_bot:employee_list")

        duty_type = _default_duty_type()
        if duty_type:
            rotation_service.resolve_current(duty_type.id)

        state = "aktif" if employee.is_active == 1 else "pasif"
        suffix = " Görev sırasından çıkarıldı." if employee.is_active == 0 else ""
        messages.success(request, f"{employee.full_name} {state} yapıldı.{suffix}")
        return redirect("office_bot:employee_list")


class EmployeeDeleteView(AdminRequiredMixin, View):
    def post(self, request, pk):
        employee = employee_service.get_by_id(pk)
        if not employee:
            messages.error(request, "Çalışan bulunamadı.")
            return redirect("office_bot:employee_list")

        name = employee.full_name
        employee_service.remove(pk)

        duty_type = _default_duty_type()
        if duty_type:
            rotation_service.resolve_current(duty_type.id)

        messages.success(request, f"{name} silindi. Görev geçmişindeki kayıtları korundu.")
        return redirect("office_bot:employee_list")


class EmployeeMoveView(AdminRequiredMixin, View):
    def post(self, request, pk):
        direction = "up" if request.POST.get("direction") == "up" else "down"
        moved = employee_service.move(pk, direction)
        if not moved:
            messages.error(request, "Çalışan zaten sıranın başında." if direction == "up" else "Çalışan zaten sıranın sonunda.")
        redirect_to = request.POST.get("redirect_to") or "office_bot:employee_list"
        return redirect(redirect_to)


class HistoryView(AdminRequiredMixin, View):
    def get(self, request):
        duty_type = _default_duty_type()
        page = int(request.GET.get("page", 1) or 1)
        result = history_service.list_history(
            duty_type_id=duty_type.id if duty_type else None, page=page, page_size=20,
        )
        return render(request, "office_bot/history.html", {
            "result": result,
            "stats": history_service.get_stats_by_employee(duty_type.id if duty_type else None),
        })


class DiscordSettingsView(AdminRequiredMixin, View):
    """Discord Ayarları: sunucu/kanal ID'leri + bot token."""

    def get(self, request):
        return render(request, "office_bot/settings_discord.html", self._context())

    def post(self, request):
        errors, data = settings_service.validate_discord_settings(request.POST)
        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, "office_bot/settings_discord.html", self._context(), status=400)

        settings_service.save_settings(data)
        messages.success(request, "Discord ayarları kaydedildi.")
        return redirect("office_bot:settings_discord")

    @staticmethod
    def _context():
        return {
            "settings": settings_service.get_masked_settings(),
            "token_is_set": settings_service.is_set("discord_bot_token"),
        }


class ScheduleSettingsView(AdminRequiredMixin, View):
    """Bildirim Saatleri: zamanlanmış mesajların saati/metni/etkinliği."""

    def get(self, request):
        return render(request, "office_bot/settings_schedule.html", {"scheduled_messages": schedule_service.get_all()})

    def post(self, request):
        errors, updates = schedule_service.validate_schedule(request.POST)
        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, "office_bot/settings_schedule.html", {"scheduled_messages": schedule_service.get_all()}, status=400)

        result = schedule_service.save_schedule(updates)
        note = "Mesaj takvimi güncellendi." if result["timing_changed"] else ("Mesaj metinleri güncellendi." if result["saved"] else "Değişiklik yok.")
        messages.success(request, note)
        return redirect("office_bot:settings_schedule")


class GeneralSettingsView(AdminRequiredMixin, View):
    """Günlük Ayarlar: şirket adı ve çalışma günü kuralı (bilgilendirme)."""

    def get(self, request):
        return render(request, "office_bot/settings_general.html", {"settings": settings_service.get_masked_settings()})

    def post(self, request):
        errors, data = settings_service.validate_general_settings(request.POST)
        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, "office_bot/settings_general.html", {"settings": settings_service.get_masked_settings()}, status=400)

        settings_service.save_settings(data)
        messages.success(request, "Ayarlar kaydedildi.")
        return redirect("office_bot:settings_general")


class TestActionsView(AdminRequiredMixin, View):
    """Test İşlemleri: Discord bağlantı testi, onay akışını başlat/sıfırla, mesajı şimdi gönder."""

    def get(self, request):
        return render(request, "office_bot/test_actions.html", self._context())

    def post(self, request):
        action = request.POST.get("action")
        duty_type = _default_duty_type()

        if action == "test_connection":
            result = discord_client.test_connection()
        elif action == "start_flow" and duty_type:
            result = duty_confirmation_service.start_flow(duty_type.id, source="manual")
        elif action == "reset_flow" and duty_type:
            result = duty_confirmation_service.reset_and_ask_again(duty_type.id)
        elif action == "send_message":
            result = self._send_message_now(request.POST.get("message_id"), duty_type)
        else:
            result = {"ok": False, "message": "Geçersiz işlem."}

        if result["ok"]:
            messages.success(request, result["message"])
        else:
            messages.error(request, result["message"])
        return redirect("office_bot:test_actions")

    @staticmethod
    def _send_message_now(message_id, duty_type):
        message = models.ScheduledMessage.objects.filter(pk=message_id).first()
        if not message:
            return {"ok": False, "message": "Mesaj bulunamadı."}

        if message.kind == "duty":
            return duty_confirmation_service.start_flow(message.duty_type_id, source="manual")

        # Hatırlatma: bugünün görevlisine DM.
        from .services.messages import render_template

        target_duty_type = models.DutyType.objects.filter(pk=message.duty_type_id).first() if message.duty_type_id else duty_type
        if not target_duty_type:
            return {"ok": False, "message": "Tanımlı görev türü yok; hatırlatma gönderilmedi."}

        today_record = models.DutyHistory.objects.filter(duty_type_id=target_duty_type.id, duty_date=today_iso()).first()
        if not today_record:
            return {"ok": False, "message": "Bugünkü görevli henüz kesinleşmedi; hatırlatma gönderilmedi."}

        employee = models.Employee.objects.filter(pk=today_record.employee_id).first() or {
            "full_name": today_record.employee_name, "discord_user_id": None,
        }
        discord_id = getattr(employee, "discord_user_id", None) or (employee.get("discord_user_id") if isinstance(employee, dict) else None)
        if not discord_id:
            return {"ok": False, "message": f"{today_record.employee_name} için Discord ID tanımlı değil."}

        content = render_template(
            message.message_template, employee=employee, duty_type=target_duty_type,
            company=settings_service.get("company_name", ""), target_date=today_iso(),
        )
        ok, detail = discord_client.send_direct_message(discord_id, content)
        return {"ok": ok, "message": detail if not ok else f'"{message.name}" gönderildi.'}

    @staticmethod
    def _context():
        duty_type = _default_duty_type()
        return {
            "bot_configured": discord_client.is_configured(),
            "confirmation_status": duty_confirmation_service.get_today_status(duty_type.id) if duty_type else None,
            "scheduled_messages": schedule_service.get_all(),
        }


class MealDashboardView(AdminRequiredMixin, View):
    """
    'Yemek Sistemi' sayfası.

    Kullanıcı kuralı: sistem her zaman yalnızca EN SON TAMAMLANAN iş gününün
    anket sonucunu gösterir (Salı → Pazartesi, Pazartesi → önceki Cuma).
    Bugünün/yarının menüsü ayrıca bilgi amaçlı gösterilir (yükleme akışı
    için gereklidir) ama "sonuçlar" bölümü yalnızca tamamlanan güne aittir.
    """

    def get(self, request):
        completed_date = previous_working_day(today_iso())
        completed_menu = meal_service.get_by_date(completed_date)
        participation = meal_vote_service.get_participation(completed_date) if completed_menu else None

        participation_rate = 0
        if participation and participation["counts"]["total"]:
            participation_rate = round(participation["counts"]["responded"] / participation["counts"]["total"] * 100)

        return render(request, "office_bot/meal.html", {
            "completed_date": completed_date,
            "completed_menu": _decorate_menu(completed_menu),
            "participation": participation,
            "participation_rate": participation_rate,
            "today_menu": _decorate_menu(meal_service.get_by_date(today_iso())),
            "next_menu": _decorate_menu(meal_service.get_next_menu()),
            "summary": {"total": len(meal_service.list_menus())},
            "upload_form": MealUploadForm(),
        })


class MealUploadView(AdminRequiredMixin, View):
    def post(self, request):
        form = MealUploadForm(request.POST, request.FILES)
        if not form.is_valid():
            messages.error(request, "Dosya seçilmedi.")
            return redirect("office_bot:meal_dashboard")

        excel_file = form.cleaned_data["excel_file"]
        result = meal_import.parse_workbook(excel_file)

        if not result["ok"]:
            messages.error(request, result["message"])
            return redirect("office_bot:meal_dashboard")

        saved = meal_service.save_rows(
            result["rows"], source_file=excel_file.name, replace_all=form.cleaned_data["replace_all"],
        )
        summary = f"{saved['inserted']} yeni, {saved['updated']} güncellenen menü kaydedildi."
        if result["warnings"]:
            summary += " Uyarılar: " + " ".join(result["warnings"])
        messages.success(request, summary)
        return redirect("office_bot:meal_dashboard")


class MealRemoveAllView(AdminRequiredMixin, View):
    def post(self, request):
        removed = meal_service.remove_all()
        messages.success(request, f"{removed} menü kaydı silindi.")
        return redirect("office_bot:meal_dashboard")


class MealTestActionsView(AdminRequiredMixin, View):
    """
    Yemek Sistemi yönetim ekranı: "gerçek sistem bugün ne gönderecekse" onu
    elle tetiklemek, gerekirse anketi erken kapatmak ve sonucu sıfırlamak için.

    ÖNEMLİ TASARIM KARARI: Burada gönderilen mesaj GERÇEK menü tarihini,
    GERÇEK içeriği ve GERÇEK (çalışan) butonları kullanır — ayrı, izole bir
    "test tarihi" YOKTUR. Bu ekrandan gönderilen anket, gerçek üretim anketiyle
    birebir aynı `meal_votes` kayıtlarını paylaşır; "Sonuçları Temizle" bu
    yüzden o günün GERÇEK oylarını da sıfırlar (bkz. _clear_results).

    Hangi menü gününün Discord mesajı bu ekrandan gönderildiği ve o mesajın
    channel_id/message_id'si `settings` tablosunda (MEAL_TRACKED_* anahtarları)
    tutulur; "Anketi Kapat" ve "Sonuçları Temizle" bu kayda göre çalışır.
    """

    def get(self, request):
        return render(request, "office_bot/meal_test_actions.html", self._context())

    def post(self, request):
        log.warning("[SCHEDULE-TESHIS] Endpoint=%s path=%s", request.resolver_match.view_name if request.resolver_match else "?", request.path)
        log.warning("[SCHEDULE-TESHIS] Formdan gelen TUM POST verisi=%s", dict(request.POST))

        action = request.POST.get("action")
        log.warning("[SCHEDULE-TESHIS] action alani degeri=%r", action)
        if action == "send_test_dm":
            log.warning("[DM-TESHIS] Formdan gelen User ID (request.POST)=%r", request.POST.get("discord_user_id"))

        handlers = {
            "send_menu": self._send_menu,
            "close_poll": self._close_poll,
            "clear_results": self._clear_results,
            "send_test_dm": lambda: self._send_test_dm(request.POST.get("discord_user_id")),
            "save_schedule": lambda: self._save_schedule(request.POST),
        }
        log.warning("[SCHEDULE-TESHIS] View'in kabul ettigi action degerleri=%s", list(handlers.keys()))
        handler = handlers.get(action)
        log.warning("[SCHEDULE-TESHIS] Eslesen handler=%s", handler.__name__ if hasattr(handler, "__name__") else handler)
        result = handler() if handler else {"ok": False, "message": "Geçersiz işlem."}
        if not handler:
            log.warning("[SCHEDULE-TESHIS] 'Gecersiz islem' dondu cunku action=%r, handlers icinde YOK: %s", action, list(handlers.keys()))

        if result["ok"]:
            messages.success(request, result["message"])
        else:
            messages.error(request, result["message"])
        return redirect("office_bot:meal_test_actions")

    @staticmethod
    def _tracked():
        """Bu ekrandan en son gönderilen mesajın kaydı (varsa)."""
        menu_date = settings_service.get(MEAL_TRACKED_DATE_KEY)
        if not menu_date:
            return None
        return {
            "menu_date": menu_date,
            "channel_id": settings_service.get(MEAL_TRACKED_CHANNEL_KEY),
            "message_id": settings_service.get(MEAL_TRACKED_MESSAGE_KEY),
            "closed": settings_service.get(MEAL_TRACKED_CLOSED_KEY) == "1",
        }

    def _send_menu(self):
        """
        Gerçek sistem BUGÜN hangi mesajı gönderecekse (meal_service.next_menu_date_iso
        — mealNotifier.service.js'teki announceTomorrow() ile birebir aynı hedef
        tarih hesabı) TAM OLARAK onun birebir aynısını gönderir: aynı tarih, aynı
        menü, aynı ikonlar/kalori, aynı butonlar. Tek fark en üstteki "🧪 TEST MESAJI" satırı.
        """
        menu_date = meal_service.next_menu_date_iso()
        menu = meal_service.get_by_date(menu_date)
        if not menu:
            return {
                "ok": False,
                "message": f"{menu_date} için tanımlı bir menü yok; gerçek sistem de bu tarihte mesaj göndermeyecek.",
            }

        channel_id = settings_service.get_channel_id("meal")
        if not channel_id:
            return {"ok": False, "message": "Yemek kanalı ID tanımlı değil. Discord Ayarları'ndan ekleyin."}

        counts = meal_vote_service.get_counts(menu_date)
        content = "🧪 TEST MESAJI\n\n" + meal_messages.render_announcement(
            {"menu_date": menu_date, "items": menu["items"]}, counts,
        )
        components = discord_client.build_meal_vote_components(menu_date)

        try:
            sent = discord_client.send_channel_message(channel_id, content, components=components)
        except discord_client.DiscordError as exc:
            return {"ok": False, "message": str(exc)}

        settings_service.set(MEAL_TRACKED_DATE_KEY, menu_date)
        settings_service.set(MEAL_TRACKED_CHANNEL_KEY, channel_id)
        settings_service.set(MEAL_TRACKED_MESSAGE_KEY, sent["id"])
        settings_service.set(MEAL_TRACKED_CLOSED_KEY, "0")
        return {"ok": True, "message": f"Menü Discord'a gönderildi ({menu_date})."}

    def _close_poll(self):
        """
        Discord mesajındaki butonları TAMAMEN PASİF hale getirir (Discord
        artık bu butona basılmasına izin vermez). Hiçbir ayrı bildirim/ephemeral
        mesaj gönderilmez — mesaj yalnızca kapanmış GÖRÜNÜR. Butonlar pasif
        olduğu için Discord bu mesaj için bir daha hiç interactionCreate
        göndermez; Node botundaki "anket kapandı" uyarısı da bu yüzden hiç
        tetiklenmez (ayrıca bir kod değişikliği gerekmedi).
        """
        tracked = self._tracked()
        if not tracked or not tracked["channel_id"] or not tracked["message_id"]:
            return {"ok": False, "message": "Önce menüyü gönderin; kapatılacak bir anket yok."}

        menu = meal_service.get_by_date(tracked["menu_date"])
        if not menu:
            return {"ok": False, "message": "Bu ankete ait menü artık bulunamadı."}

        counts = meal_vote_service.get_counts(tracked["menu_date"])
        content = "🧪 TEST MESAJI\n\n" + meal_messages.render_announcement(
            {"menu_date": tracked["menu_date"], "items": menu["items"]}, counts,
        )
        components = discord_client.build_meal_vote_components(tracked["menu_date"], disabled=True)

        try:
            discord_client.edit_channel_message(tracked["channel_id"], tracked["message_id"], content, components)
        except discord_client.DiscordError as exc:
            return {"ok": False, "message": str(exc)}

        settings_service.set(MEAL_TRACKED_CLOSED_KEY, "1")
        return {"ok": True, "message": "Anket kapatıldı; butonlar artık pasif."}

    def _clear_results(self):
        """
        Bu ekrandan gönderilen mesajı ve o güne ait katılım kayıtlarını
        tamamen temizler: Discord'daki mesaj silinir, o günün oyları veritabanından
        silinir, kayıt unutulur. Menünün kendisi (yemek listesi) SİLİNMEZ —
        yalnızca duyuru/anket durumu sıfırlanır.
        """
        tracked = self._tracked()
        if not tracked:
            return {"ok": True, "message": "Zaten temiz; silinecek bir kayıt yok."}

        if tracked["channel_id"] and tracked["message_id"]:
            try:
                discord_client.delete_channel_message(tracked["channel_id"], tracked["message_id"])
            except discord_client.DiscordError:
                pass  # Mesaj elle silinmiş olabilir; kaydı yine de temizle.

        removed = models.MealVote.objects.filter(menu_date=tracked["menu_date"]).delete()[0]

        for key in (MEAL_TRACKED_DATE_KEY, MEAL_TRACKED_CHANNEL_KEY, MEAL_TRACKED_MESSAGE_KEY, MEAL_TRACKED_CLOSED_KEY):
            settings_service.set(key, "")

        return {"ok": True, "message": f"Sonuçlar temizlendi ({removed} oy silindi, mesaj kaldırıldı)."}

    @staticmethod
    def _send_test_dm(discord_user_id):
        log.warning("[DM-TESHIS] View'e gelen User ID (_send_test_dm parametresi)=%r", discord_user_id)
        discord_user_id = str(discord_user_id or "").strip()
        log.warning("[DM-TESHIS] Service'e (discord_client.send_direct_message) giden User ID=%r", discord_user_id)
        if not discord_user_id:
            return {"ok": False, "message": "DM göndermek için bir Discord kullanıcı ID'si girin."}
        log.warning("[DM-TESHIS] Kullanılan fonksiyon: discord_client.send_direct_message (bkz. services/discord_client.py)")
        ok, detail = discord_client.send_direct_message(
            discord_user_id, "🧪 Bu, Office Portal yönetim ekranından gönderilen bir deneme mesajıdır.",
        )
        log.warning("[DM-TESHIS] Donen Discord cevabi: ok=%s detail=%s", ok, detail)
        return {"ok": ok, "message": detail}

    @staticmethod
    def _save_schedule(data):
        """
        Yemek bildirim saatini kaydeder. Kod içinde SABİT bir saat/cron ifadesi
        yoktur — Node tarafındaki mealScheduler.js her dakika bu AYNI
        `settings` anahtarlarını okur; burada kaydetmek, sunucu yeniden
        başlatılmadan bir sonraki dakika kontrolünde devreye girer.
        """
        time_value = str(data.get("meal_notify_time") or "").strip()
        if not _TIME_PATTERN.match(time_value):
            return {"ok": False, "message": "Geçerli bir saat girin (SS:DD, örn. 10:00)."}

        enabled = "1" if data.get("meal_notify_enabled") in ("on", "1", "true") else "0"

        settings_service.set(MEAL_SCHEDULE_TIME_KEY, time_value)
        settings_service.set(MEAL_SCHEDULE_ENABLED_KEY, enabled)

        state = "açık" if enabled == "1" else "kapalı"
        return {"ok": True, "message": f"Bildirim saati {time_value} olarak kaydedildi (otomatik gönderim {state})."}

    @staticmethod
    def _schedule_status():
        time_value = settings_service.get(MEAL_SCHEDULE_TIME_KEY, MEAL_SCHEDULE_DEFAULT_TIME)
        if not _TIME_PATTERN.match(time_value):
            time_value = MEAL_SCHEDULE_DEFAULT_TIME
        enabled = settings_service.get(MEAL_SCHEDULE_ENABLED_KEY, "1") != "0"

        last_date = meal_service.get_last_announced_date()

        # Sonraki gönderim: bugün hedef saat geçmemişse bugün, geçtiyse yarın.
        next_date = today_iso() if now_hhmm() < time_value else add_days(today_iso(), 1)

        return {
            "time": time_value,
            "enabled": enabled,
            "last_announced_date": last_date,
            "next_date": next_date,
        }

    @classmethod
    def _context(cls):
        tracked = cls._tracked()
        participation = None
        menu = None
        if tracked:
            menu = _decorate_menu(meal_service.get_by_date(tracked["menu_date"]))
            participation = meal_vote_service.get_participation(tracked["menu_date"])
            participation["yes_grouped"] = meal_vote_service.group_by_company(participation["yes"])
            participation["no_grouped"] = meal_vote_service.group_by_company(participation["no"])
            participation["pending_grouped"] = meal_vote_service.group_by_company(participation["pending"])

        return {
            "bot_configured": discord_client.is_configured(),
            "tracked": tracked,
            "menu": menu,
            "participation": participation,
            "schedule": cls._schedule_status(),
        }


class MealTestParticipationApiView(AdminRequiredMixin, View):
    """
    Yönetim ekranındaki katılım listesini CANLI tutmak için hafif bir JSON
    uç noktası: sayfa birkaç saniyede bir bunu çağırır, isim listeleri sayfa
    yenilenmeden güncellenir (bkz. meal_test_actions.html'deki polling script'i).
    """

    def get(self, request):
        from django.http import JsonResponse

        menu_date = settings_service.get(MEAL_TRACKED_DATE_KEY)
        if not menu_date:
            return JsonResponse({"tracked": False})

        participation = meal_vote_service.get_participation(menu_date)
        closed = settings_service.get(MEAL_TRACKED_CLOSED_KEY) == "1"

        def _slim_groups(entries):
            return [
                {"company": g["company"], "count": g["count"], "people": [{"name": p["name"]} for p in g["people"]]}
                for g in meal_vote_service.group_by_company(entries)
            ]

        return JsonResponse({
            "tracked": True,
            "menu_date": menu_date,
            "closed": closed,
            "yes": _slim_groups(participation["yes"]),
            "no": _slim_groups(participation["no"]),
            "pending": _slim_groups(participation["pending"]),
            "counts": participation["counts"],
        })
