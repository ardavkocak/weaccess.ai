"""Kimlik dogrulama ve profil yonetimi view'lari."""
from django.contrib import messages
from django.contrib.auth import get_user_model, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
)
from django.shortcuts import redirect, render
from django.urls import reverse_lazy

from apps.inventory.forms import EmployeePhotoForm

from .forms import LoginForm, ProfileUpdateForm, StyledPasswordChangeForm

User = get_user_model()


def clear_must_change_password(user):
    """Kullanici kendi sifresini belirledikten sonra zorunlulugu kaldirir."""
    if user.must_change_password:
        user.must_change_password = False
        user.save(update_fields=["must_change_password"])


class CustomLoginView(LoginView):
    """Kullanici adi/e-posta ile giris; role gore yonlendirme ve 'beni hatirla' destegi."""

    template_name = "registration/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        response = super().form_valid(form)
        if not form.cleaned_data.get("remember_me"):
            self.request.session.set_expiry(0)
        messages.success(self.request, f"Hos geldiniz, {self.request.user.get_full_name() or self.request.user.username}!")
        return response

    def get_success_url(self):
        user = self.request.user
        if user.is_admin_role:
            return reverse_lazy("dashboard:home")
        return reverse_lazy("inventory:my-assignments")


class CustomLogoutView(LogoutView):
    """Cikis yapildiginda bilgi mesaji gosterir."""

    next_page = reverse_lazy("accounts:login")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.info(request, "Basariyla cikis yaptiniz.")
        return super().dispatch(request, *args, **kwargs)


@login_required
def profile_view(request):
    """Kullanicinin kendi hesap bilgilerini ve (varsa) calisan fotografini duzenledigi sayfa."""
    user = request.user
    employee = getattr(user, "employee_profile", None)

    profile_form = ProfileUpdateForm(instance=user)
    photo_form = EmployeePhotoForm(instance=employee) if employee else None

    if request.method == "POST":
        if "update_profile" in request.POST:
            profile_form = ProfileUpdateForm(request.POST, instance=user)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, "Profil bilgileriniz basariyla guncellendi.")
                return redirect("accounts:profile")
        elif "update_photo" in request.POST and employee:
            photo_form = EmployeePhotoForm(request.POST, request.FILES, instance=employee)
            if photo_form.is_valid():
                photo_form.save()
                messages.success(request, "Profil fotografiniz guncellendi.")
                return redirect("accounts:profile")

    context = {
        "profile_form": profile_form,
        "photo_form": photo_form,
        "employee": employee,
    }
    return render(request, "accounts/profile.html", context)


@login_required
def password_change_view(request):
    """Kullanicinin kendi sifresini degistirdigi sayfa."""
    # Otomatik sifreyle olusturulan hesaplar buraya zorunlu olarak yonlendirilir;
    # sablonun durumu aciklayabilmesi icin bayragi baslangicta okuruz.
    was_forced = request.user.must_change_password
    if request.method == "POST":
        form = StyledPasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            clear_must_change_password(user)
            update_session_auth_hash(request, user)
            messages.success(request, "Sifreniz basariyla degistirildi.")
            return redirect("accounts:profile")
    else:
        form = StyledPasswordChangeForm(user=request.user)
    return render(
        request,
        "accounts/password_change.html",
        {"form": form, "password_change_required": was_forced},
    )


class StyledPasswordResetView(PasswordResetView):
    template_name = "registration/password_reset_form.html"
    email_template_name = "registration/password_reset_email.html"
    subject_template_name = "registration/password_reset_subject.txt"
    success_url = reverse_lazy("accounts:password_reset_done")


class StyledPasswordResetDoneView(PasswordResetDoneView):
    template_name = "registration/password_reset_done.html"


class StyledPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = "registration/password_reset_confirm.html"
    success_url = reverse_lazy("accounts:password_reset_complete")

    def form_valid(self, form):
        """E-posta ile sifre sifirlayan kullanici da kendi sifresini belirlemis olur.

        Bayrak burada temizlenmezse, otomatik sifresini sifirlama baglantisiyla
        degistiren calisan giristen sonra yine sifre degistirme sayfasina takilir.
        """
        response = super().form_valid(form)
        clear_must_change_password(form.user)
        return response


class StyledPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = "registration/password_reset_complete.html"
