"""Envanter view'lari icin yetkilendirme ve ortak davranis mixinleri."""
from django import forms
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect


class HtmlDateInput(forms.DateInput):
    """HTML5 tarih secici; degeri daima ISO (YYYY-MM-DD) biciminde basar.

    <input type="date"> yalnizca ISO bicimini kabul eder. LANGUAGE_CODE "tr"
    oldugu icin Django varsayilan olarak "16/07/2026" gibi yerellestirilmis bir
    deger basar; tarayici bunu cozemedigi icin alan BOS gorunur ve kayitli tarih
    kaybolur. format sabitlenerek bu onlenir.
    """

    input_type = "date"

    def __init__(self, attrs=None):
        super().__init__(attrs=attrs, format="%Y-%m-%d")


class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Sayfaya yalnizca 'admin' rolundeki kullanicilarin erisimine izin verir.

    Sistem artik tamamen admin odakli oldugu icin (bkz. accounts.CustomLoginView)
    admin olmayan biri hicbir zaman oturum acamaz; bu kontrol yine de savunma
    amacli korunur (orn. rolu sonradan degistirilen, halihazirda oturumu acik
    bir hesap gibi kenar durumlar icin).
    """

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_admin_role

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            messages.error(self.request, "Bu sayfaya erisim yetkiniz bulunmuyor.")
            return redirect("dashboard:home")
        return super().handle_no_permission()


class BootstrapFormMixin:
    """ModelForm alanlarina otomatik olarak Bootstrap 5 CSS siniflari uygular."""

    def _apply_bootstrap_classes(self):
        from django import forms as dj_forms

        for field in self.fields.values():
            widget = field.widget
            existing = widget.attrs.get("class", "")
            # RadioSelect/CheckboxSelectMultiple birer Select degildir; tekil
            # kutucuklar gibi form-check-input sinifini kullanirlar.
            if isinstance(widget, (dj_forms.CheckboxInput, dj_forms.RadioSelect)):
                widget.attrs["class"] = f"{existing} form-check-input".strip()
            elif isinstance(widget, (dj_forms.Select, dj_forms.SelectMultiple)):
                widget.attrs["class"] = f"{existing} form-select".strip()
            else:
                widget.attrs["class"] = f"{existing} form-control".strip()
