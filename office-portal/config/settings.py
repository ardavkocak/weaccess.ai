"""
Ofis Portali - Django ayarlari.

Bu proje, weaccess.ai calisma alanindaki bagimsiz otomasyon projelerini
(Zimmet Sistemi, Ofis Gorev Takibi, IK Otomasyonu, Aylik Takip,
Dokumantasyon Otomasyonu) tek bir kurumsal arayuz altinda birlestirmeyi
hedefleyen "kabuk" (shell) uygulamadir.

Faz 2 durumu: Zimmet Sistemi'nin apps.accounts / apps.inventory /
apps.dashboard uygulamalari buraya KOPYALANARAK entegre edildi (orijinal
zimmet-sistemi/ klasoru degistirilmedi). Bu nedenle:

- AUTH_USER_MODEL artik Zimmet'in "accounts.User" modelidir (e-posta ile
  giris, rol tabanli). Portal henuz gercek kullanici icermedigi icin bu
  karar simdi, bedelsizken alindi (bkz. entegrasyon plani).
- Veritabani PostgreSQL'dir; ama zimmet-sistemi'nin KENDI yerel
  veritabanina (zimmet_db, gercek calisan verisi icerir) DEGIL, portal
  icin ayrilmis izole bir veritabanina (office_portal_db) baglanir. Ayni
  semayi paylasilan canli veritabanina baglamak ayri, onay gerektiren bir
  karardir.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.environ.get("SECRET_KEY", "django-insecure-office-portal-dev-key-change-me")
DEBUG = os.environ.get("DEBUG", "True") == "True"
ALLOWED_HOSTS = [h.strip() for h in os.environ.get("ALLOWED_HOSTS", "127.0.0.1,localhost").split(",") if h.strip()]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "portal",
    # --- Zimmet Sistemi entegrasyonu (Faz 2) ---
    "apps.accounts",
    "apps.inventory",
    "apps.dashboard",
    # --- Faz 3: tum moduller Portal'in kendi sayfalari (iframe/harici port yok) ---
    "apps.office_bot",
    "apps.hr",
    "apps.monthly_tracking",
    "apps.documentation",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # WhiteNoise statik dosyalari uygulama sunucusundan (gunicorn) servis eder.
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # --- Zimmet Sistemi entegrasyonu (Faz 2) ---
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
                # Sidebar'daki "Operasyonlar" modul listesini her sayfaya
                # tek noktadan saglar (bkz. portal/modules.py).
                "portal.context_processors.sidebar_modules",
                # Zimmet entegrasyonu: bekleyen iade / bildirim sayaclari.
                "common.context_processors.sidebar_context",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# Portal icin izole PostgreSQL veritabani (bkz. modul docstring'i).
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DB_NAME", "office_portal_db"),
        "USER": os.environ.get("DB_USER", "office_portal_user"),
        "PASSWORD": os.environ.get("DB_PASSWORD", "office_portal_pass"),
        "HOST": os.environ.get("DB_HOST", "127.0.0.1"),
        "PORT": os.environ.get("DB_PORT", "5432"),
        "CONN_MAX_AGE": 60,
    },
    # --- Faz 3: Ofis Gorev Takibi entegrasyonu ---
    # apps.office_bot'un modelleri BU dosyaya (orijinal ofis-gorev-takibi
    # projesinin KENDI SQLite'i) dogrudan okur/yazar. Discord bot + cron ayni
    # dosyayi kendi surecinde kullanmaya devam eder (bkz. apps/office_bot/router.py).
    "office_bot": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.environ.get(
            "OFFICE_BOT_DB_PATH",
            str((BASE_DIR / ".." / "ofis-gorev-takibi" / "data" / "ofis.sqlite").resolve()),
        ),
        # Node botu (better-sqlite3) aynı dosyaya eşzamanlı yazıyor. Varsayılan
        # sqlite3 zaman aşımı 5sn'dir ama Python'un kendi kilit bekleme süresini
        # de aynı büyüklükte tutmak, iki sürecin birbirini "database is locked"
        # ile anında reddetmesi yerine kısa süreli çakışmalarda beklemesini
        # sağlar (bkz. ofis-gorev-takibi/src/database/connection.js busy_timeout).
        "OPTIONS": {"timeout": 5},
    },
}

DATABASE_ROUTERS = ["apps.office_bot.router.OfficeBotRouter"]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --- Zimmet Sistemi entegrasyonu (Faz 2): ozel kullanici modeli + e-posta girisi ---
AUTH_USER_MODEL = "accounts.User"
AUTHENTICATION_BACKENDS = [
    "apps.accounts.backends.EmailModelBackend",
]

LANGUAGE_CODE = "tr"
TIME_ZONE = os.environ.get("TIME_ZONE", "Europe/Istanbul")
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

# WhiteNoise dosyalari sikistirarak (gzip) sunar.
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "portal:dashboard"
LOGOUT_REDIRECT_URL = "accounts:login"

# --- E-posta (sifremi unuttum ozelligi icin) ---
EMAIL_BACKEND = os.environ.get("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = os.environ.get("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "True") == "True"
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "Ofis Portali <noreply@ofisportali.local>")

# --- Mesaj cercevesi - Bootstrap uyumu ---
from django.contrib.messages import constants as messages_constants  # noqa: E402

MESSAGE_TAGS = {
    messages_constants.DEBUG: "secondary",
    messages_constants.INFO: "info",
    messages_constants.SUCCESS: "success",
    messages_constants.WARNING: "warning",
    messages_constants.ERROR: "danger",
}

PAGE_SIZE = 15

if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
