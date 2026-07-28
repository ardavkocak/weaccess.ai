"""Ozel Django middleware bilesenleri."""
from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.functional import cached_property

from .utils import set_current_request


class CurrentRequestMiddleware:
    """Aktif istegi thread-local depoda tutar.

    Bu sayede models.py icindeki sinyal (signals.py) fonksiyonlari,
    view fonksiyonuna parametre olarak request gecirilmeden de
    islemi yapan kullaniciya ve IP adresine erisebilir.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        set_current_request(request)
        try:
            response = self.get_response(request)
        finally:
            set_current_request(None)
        return response


class ForcePasswordChangeMiddleware:
    """must_change_password bayragi acik olan hesaplari sifre degistirmeye zorlar.

    Calisan eklenirken uretilen otomatik sifre (ad + 123) tahmin edilebilir
    oldugundan, hesap sahibi kendi sifresini belirleyene kadar diger sayfalara
    erisimi engellenir.

    Sifre degistirme sayfasinin kendisi, cikis islemi ve statik/medya istekleri
    disarida birakilir; aksi halde kullanici sonsuz yonlendirme dongusune girer.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    @cached_property
    def exempt_paths(self):
        """Bayrak acikken bile erisilebilen adresler."""
        return {
            reverse("accounts:password_change"),
            reverse("accounts:logout"),
            reverse("accounts:login"),
        }

    def _is_exempt(self, request):
        if request.path in self.exempt_paths:
            return True
        # Statik ve medya dosyalari sayfa gezinmesi degildir; yonlendirilirse
        # sifre degistirme sayfasi stilsiz/gorselsiz acilir.
        for prefix in (settings.STATIC_URL, settings.MEDIA_URL):
            if prefix and request.path.startswith(prefix):
                return True
        return False

    def __call__(self, request):
        user = getattr(request, "user", None)
        if (
            user is not None
            and user.is_authenticated
            and getattr(user, "must_change_password", False)
            and not self._is_exempt(request)
        ):
            messages.warning(
                request,
                "Guvenliginiz icin devam etmeden once sifrenizi degistirmelisiniz.",
            )
            return redirect("accounts:password_change")
        return self.get_response(request)


class ActivityTrackingMiddleware:
    """Kullanicinin son goruldugu zamani gunceller."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.user.is_authenticated:
            from django.utils import timezone

            request.user.last_seen = timezone.now()
            request.user.save(update_fields=["last_seen"])
        return response
