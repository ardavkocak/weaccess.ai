"""Proje genelinde kullanilan yardimci fonksiyonlar."""
import threading

_thread_locals = threading.local()


def set_current_request(request):
    """Aktif HTTP istegini thread-local depoya kaydeder."""
    _thread_locals.request = request


def get_current_request():
    """Aktif HTTP istegini dondurur (sinyaller icinde kullanilir)."""
    return getattr(_thread_locals, "request", None)


def get_current_user():
    """Aktif oturum acmis kullaniciyi dondurur, yoksa None."""
    request = get_current_request()
    if request is not None and hasattr(request, "user") and request.user.is_authenticated:
        return request.user
    return None


def get_client_ip(request):
    """İstemcinin gercek IP adresini proxy/header bilgisinden cikarir."""
    if request is None:
        return None
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")
