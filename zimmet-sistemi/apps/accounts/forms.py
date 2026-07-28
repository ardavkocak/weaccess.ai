"""Hesap yonetimi ile ilgili formlar (giris, profil, sifre)."""
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm

User = get_user_model()


class BootstrapFormMixin:
    """Tum form alanlarina otomatik olarak Bootstrap 5 CSS siniflari ekler."""

    def _apply_bootstrap_classes(self):
        for field_name, field in self.fields.items():
            widget = field.widget
            existing = widget.attrs.get("class", "")
            if isinstance(widget, (forms.CheckboxInput,)):
                widget.attrs["class"] = f"{existing} form-check-input".strip()
            elif isinstance(widget, (forms.Select, forms.SelectMultiple)):
                widget.attrs["class"] = f"{existing} form-select".strip()
            elif isinstance(widget, forms.FileInput):
                widget.attrs["class"] = f"{existing} form-control".strip()
            else:
                widget.attrs["class"] = f"{existing} form-control".strip()
            if field.help_text:
                widget.attrs.setdefault("title", field.help_text)


class LoginForm(BootstrapFormMixin, AuthenticationForm):
    """E-posta ve sifre ile giris formu; 'beni hatirla' secenegi icerir.

    Alan adi AuthenticationForm ile uyum icin "username" olarak kalir, ancak
    icerigi e-posta adresidir: giris yalnizca e-posta ile yapilir.
    """

    username = forms.EmailField(
        label="E-posta",
        widget=forms.EmailInput(
            attrs={"autofocus": True, "autocomplete": "email", "placeholder": "ornek@sirket.com"}
        ),
    )
    password = forms.CharField(
        label="Sifre",
        widget=forms.PasswordInput(attrs={"placeholder": "sifreniz"}),
    )
    remember_me = forms.BooleanField(label="Beni Hatirla", required=False)

    error_messages = {
        "invalid_login": "E-posta veya sifre hatali. Lutfen tekrar deneyin.",
        "inactive": "Bu hesap pasif duruma alinmis. Lutfen sistem yoneticinizle iletisime gecin.",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap_classes()


class ProfileUpdateForm(BootstrapFormMixin, forms.ModelForm):
    """Kullanicinin kendi hesap bilgilerini duzenlemesi icin form."""

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "phone_number"]
        labels = {
            "first_name": "Ad",
            "last_name": "Soyad",
            "email": "E-posta",
            "phone_number": "Telefon",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap_classes()

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        qs = User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("Bu e-posta adresi baska bir kullanici tarafindan kullaniliyor.")
        return email


class StyledPasswordChangeForm(BootstrapFormMixin, PasswordChangeForm):
    """Bootstrap uyumlu sifre degistirme formu."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap_classes()
