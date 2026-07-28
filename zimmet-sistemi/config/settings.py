"""
Zimmet ve Envanter Yonetim Sistemi icin Django ayarlari.
Django 5.x ile uyumludur ve tum ortam degiskenleri .env dosyasindan okunur.
"""
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, False),
)
environ.Env.read_env(BASE_DIR / ".env")

# ---------------------------------------------------------------------------
# Guvenlik
# ---------------------------------------------------------------------------
SECRET_KEY = env("SECRET_KEY", default="django-insecure-development-key-change-me")
DEBUG = env.bool("DEBUG", default=True)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["127.0.0.1", "localhost"])
# Reverse proxy arkasinda HTTPS uzerinden gelen POST istekleri icin (orn. login,
# form gonderimleri) Django'nun guvendigi origin'ler burada tanimlanir. Sema
# (https://) zorunludur, aksi halde Django CSRF dogrulamasinda dikkate almaz.
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])

# ---------------------------------------------------------------------------
# Uygulamalar
# ---------------------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    # Proje uygulamalari
    "apps.accounts",
    "apps.inventory",
    "apps.dashboard",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # WhiteNoise statik dosyalari uygulama sunucusundan (gunicorn) servis eder.
    # SecurityMiddleware'den hemen SONRA, diger her seyden ONCE gelmelidir.
    # Boylece DEBUG kapatildiginda da CSS/JS ayri bir web sunucusu gerekmeden
    # calismaya devam eder.
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "common.middleware.CurrentRequestMiddleware",
    "common.middleware.ForcePasswordChangeMiddleware",
    "common.middleware.ActivityTrackingMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "common.context_processors.sidebar_context",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# ---------------------------------------------------------------------------
# Veritabani (PostgreSQL)
# ---------------------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("DB_NAME", default="zimmet_db"),
        "USER": env("DB_USER", default="zimmet_user"),
        "PASSWORD": env("DB_PASSWORD", default="zimmet_pass"),
        "HOST": env("DB_HOST", default="127.0.0.1"),
        "PORT": env("DB_PORT", default="5432"),
        "CONN_MAX_AGE": 60,
        "ATOMIC_REQUESTS": True,
    }
}

# ---------------------------------------------------------------------------
# Sifre dogrulama
# ---------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

AUTH_USER_MODEL = "accounts.User"
# Giris yalnizca e-posta ile yapilir. Varsayilan ModelBackend bilerek listede
# degildir: bulunsaydi kullanici adiyla giris onun uzerinden yine mumkun olurdu.
# EmailModelBackend ModelBackend'den turedigi icin izin/yetki sorgulari korunur.
AUTHENTICATION_BACKENDS = [
    "apps.accounts.backends.EmailModelBackend",
]

LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "dashboard:home"
LOGOUT_REDIRECT_URL = "accounts:login"

# ---------------------------------------------------------------------------
# Uluslararasilastirma
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "tr"
TIME_ZONE = env("TIME_ZONE", default="Europe/Istanbul")
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# Statik ve medya dosyalari
# ---------------------------------------------------------------------------
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# WhiteNoise dosyalari sikistirarak (gzip/brotli) sunar. Manifest'li surum
# bilerek kullanilmaz: manifest, collectstatic calismadan once `{% static %}`
# etiketini hataya dusurur ve yerel gelistirmeyi kirilgan hale getirir.
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# Oturum ayarlari ("Beni hatirla" ozelligi icin)
# ---------------------------------------------------------------------------
SESSION_COOKIE_AGE = 60 * 60 * 24 * 14  # 14 gun
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# ---------------------------------------------------------------------------
# E-posta ayarlari (sifremi unuttum ozelligi icin)
# ---------------------------------------------------------------------------
EMAIL_BACKEND = env("EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = env("EMAIL_HOST", default="smtp.gmail.com")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="Zimmet Sistemi <noreply@zimmet.local>")

# ---------------------------------------------------------------------------
# Mesaj cercevesi - Bootstrap uyumu
# ---------------------------------------------------------------------------
from django.contrib.messages import constants as messages_constants  # noqa: E402

MESSAGE_TAGS = {
    messages_constants.DEBUG: "secondary",
    messages_constants.INFO: "info",
    messages_constants.SUCCESS: "success",
    messages_constants.WARNING: "warning",
    messages_constants.ERROR: "danger",
}

# ---------------------------------------------------------------------------
# Sayfalama ve proje sabitleri
# ---------------------------------------------------------------------------
PAGE_SIZE = 15

# ---------------------------------------------------------------------------
# Guvenlik baslıklari (production icin)
# ---------------------------------------------------------------------------
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
