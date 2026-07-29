"""Ayar servisi — settings.service.js'in Python portu."""
from __future__ import annotations

import re

from ..models import Settings

SETTING_KEYS = {
    "discord_bot_token": {"label": "Discord Bot Token", "sensitive": True},
    "discord_guild_id": {"label": "Discord Sunucu (Guild) ID", "sensitive": False},
    "discord_duty_channel_id": {"label": "Görev Kanalı ID", "sensitive": False},
    "discord_meal_channel_id": {"label": "Yemek Kanalı ID", "sensitive": False},
    "company_name": {"label": "Şirket Adı", "sensitive": False},
}

# İki sistem (görev + yemek) aynı botu, farklı kanalları kullanır.
CHANNEL_KEYS = {
    "duty": {"setting_key": "discord_duty_channel_id", "label": "Görev kanalı"},
    "meal": {"setting_key": "discord_meal_channel_id", "label": "Yemek kanalı"},
}

SNOWFLAKE_PATTERN = re.compile(r"^\d{17,20}$")


def get(key, fallback=""):
    row = Settings.objects.filter(pk=key).first()
    return row.value if row else fallback


def get_channel_id(channel_key):
    meta = CHANNEL_KEYS.get(channel_key)
    if not meta:
        raise ValueError(f"Bilinmeyen kanal anahtarı: {channel_key}")
    return get(meta["setting_key"])


def get_all():
    return dict(Settings.objects.values_list("key", "value"))


def get_masked_settings():
    all_settings = get_all()
    masked = dict(all_settings)
    for key, meta in SETTING_KEYS.items():
        if meta["sensitive"] and all_settings.get(key):
            masked[key] = f"••••••••••••{all_settings[key][-4:]}"
    return masked


def is_set(key):
    return bool(get(key))


def set(key, value):
    Settings.objects.update_or_create(pk=key, defaults={"value": str(value or "")})


def validate_discord_settings(data):
    """Discord Ayarları sayfası: guild/kanal ID'leri + bot token."""
    errors = []
    to_save = {}

    guild_id = str(data.get("discord_guild_id") or "").strip()
    if guild_id and not SNOWFLAKE_PATTERN.match(guild_id):
        errors.append("Discord Sunucu (Guild) ID yalnızca rakamlardan oluşmalı ve 17-20 haneli olmalıdır.")
    else:
        to_save["discord_guild_id"] = guild_id

    for meta in CHANNEL_KEYS.values():
        channel_id = str(data.get(meta["setting_key"]) or "").strip()
        if channel_id and not SNOWFLAKE_PATTERN.match(channel_id):
            errors.append(f"{meta['label']} ID yalnızca rakamlardan oluşmalı ve 17-20 haneli olmalıdır.")
        else:
            to_save[meta["setting_key"]] = channel_id

    # Token bos birakilirsa mevcut deger korunur (maskeli deger geri yazilmasin diye).
    token = str(data.get("discord_bot_token") or "").strip()
    if token:
        to_save["discord_bot_token"] = token

    if errors:
        return errors, None
    return [], to_save


def validate_general_settings(data):
    """Günlük Ayarlar sayfası: şirket adı."""
    errors = []
    company_name = str(data.get("company_name") or "").strip()
    if not company_name:
        errors.append("Şirket adı boş bırakılamaz.")
    elif len(company_name) > 100:
        errors.append("Şirket adı en fazla 100 karakter olabilir.")
    if errors:
        return errors, None
    return [], {"company_name": company_name}


def save_settings(data):
    for key, value in data.items():
        set(key, value)


def clear_token():
    set("discord_bot_token", "")
