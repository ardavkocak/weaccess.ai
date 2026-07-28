"""Proje genelinde kullanilan yardimci fonksiyonlar."""
import re
import threading

_thread_locals = threading.local()

# Turkce karakterlerin ASCII karsiliklari. Buyuk harfler de eslendigi icin
# donusum str.lower()'dan ONCE yapilmalidir: Python'da "İ".lower() tek bir "i"
# degil, "i" + birlesik nokta (U+0307) uretir ve sifreyi sessizce bozar.
TURKISH_ASCII_MAP = str.maketrans(
    {
        "ç": "c", "Ç": "c",
        "ğ": "g", "Ğ": "g",
        "ı": "i", "I": "i", "İ": "i",
        "ö": "o", "Ö": "o",
        "ş": "s", "Ş": "s",
        "ü": "u", "Ü": "u",
    }
)

# Otomatik uretilen sifrelerin sonuna eklenen sabit ek: "ozge" -> "ozge123".
AUTO_PASSWORD_SUFFIX = "123"


def turkish_to_ascii(text):
    """Turkce karakterleri ASCII karsiliklarina cevirip kucuk harfe indirir."""
    if not text:
        return ""
    return text.translate(TURKISH_ASCII_MAP).lower()


def normalize_name(text):
    """Bir adi kullanici adi / sifre uretimine uygun sade bicime indirger.

    Turkce karakterler ASCII'ye cevrilir, harf ve rakam disindaki her sey
    (bosluk, tire, noktalama) atilir: "Ayşe-Nur" -> "aysenur".
    """
    return re.sub(r"[^a-z0-9]", "", turkish_to_ascii(text))


def generate_employee_password(first_name):
    """Calisanin adindan otomatik sifre uretir: ad + 123.

    Ornek: "Özge" -> "ozge123", "Ahmet" -> "ahmet123", "Şule" -> "sule123".
    Ad hic ASCII harf icermiyorsa (beklenmeyen durum) sifre "kullanici123" olur;
    boylece sifre asla yalnizca "123" gibi bos bir degere dusmez.
    """
    return f"{normalize_name(first_name) or 'kullanici'}{AUTO_PASSWORD_SUFFIX}"


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
