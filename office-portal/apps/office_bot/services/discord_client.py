"""
Discord REST istemcisi — discord/bot.js'in Python portu.

ONEMLI MIMARI KARAR: discord.js bir GATEWAY (WebSocket) baglantisi kurar ve
surekli acik kalir; bu, Django'nun istek/yanit (request/response) modeline
uygun degildir. Bunun yerine bu modul Discord'un HTTP REST API'sini
(https://discord.com/api/v10) dogrudan `requests` ile kullanir:
  - Bot bilgisi/sunucu/kanal sorgulama (baglanti testi)
  - Kanala veya DM'e mesaj gonderme (butonlu/butonsuz)
  - Var olan bir mesaji duzenleme

BUTON TIKLAMALARI (interactionCreate) BU MODULDE YOKTUR: bir kullanicinin
"Evet/Hayir" butonuna basmasi Discord'un GATEWAY uzerinden bildirdigi bir
olaydir; bunu almak icin surekli acik bir baglanti (veya genel-erisimli bir
Interactions Endpoint URL) gerekir. Orijinal Node botu (ofis-gorev-takibi,
degistirilmeden calismaya devam eder) zaten bu gateway baglantisina sahiptir
ve TUM buton tiklamalarini islemeye devam eder — Portal'in gonderdigi
mesajlar da dahil (Discord, interaction'lari gonderene degil, uygulamanin
o an bagli olan gateway oturumuna yonlendirir). Bu sayede Portal'dan
gonderilen "Görev Onayını Başlat" mesajindaki butonlara basildiginda,
zaten calisan Node botu bunu normal sekilde isler.
"""
from __future__ import annotations

import logging

import requests

from . import settings_service

API_BASE = "https://discord.com/api/v10"
TIMEOUT = 10

log = logging.getLogger("office_bot.discord_client")


class DiscordError(Exception):
    """Kullaniciya gosterilebilir, Turkce bir Discord hatasi."""


def _headers():
    token = settings_service.get("discord_bot_token")
    if not token:
        raise DiscordError("Discord bot token tanımlı değil. Ayarlar sayfasından ekleyin.")
    return {"Authorization": f"Bot {token}", "Content-Type": "application/json"}


def _friendly(response: requests.Response) -> str:
    try:
        data = response.json()
        message = data.get("message", response.text)
    except ValueError:
        message = response.text

    if response.status_code == 401:
        return "Discord bot token geçersiz. Ayarlar sayfasından doğru token'ı girin."
    if "Missing Access" in message or "Missing Permissions" in message:
        return "Botun bu kanala mesaj gönderme yetkisi yok. Kanal izinlerini kontrol edin."
    if "Unknown Channel" in message:
        return "Kanal bulunamadı. Kanal ID'sini kontrol edin ve botun sunucuya ekli olduğundan emin olun."
    if "Unknown Guild" in message:
        return "Sunucu bulunamadı. Guild ID'sini kontrol edin ve botun bu sunucuya ekli olduğundan emin olun."
    return f"Discord hatası ({response.status_code}): {message}"


def build_components(flow_id, step, disabled=False):
    """buildConfirmButtons'in REST karsiligi: Evet/Hayir butonlu action row."""
    return [
        {
            "type": 1,  # ACTION_ROW
            "components": [
                {
                    "type": 2,  # BUTTON
                    "style": 3,  # SUCCESS (yesil)
                    "label": "Evet",
                    "emoji": {"name": "✅"},
                    "custom_id": f"dc:{flow_id}:{step}:y",
                    "disabled": disabled,
                },
                {
                    "type": 2,
                    "style": 4,  # DANGER (kirmizi)
                    "label": "Hayır",
                    "emoji": {"name": "❌"},
                    "custom_id": f"dc:{flow_id}:{step}:n",
                    "disabled": disabled,
                },
            ],
        }
    ]


def build_meal_vote_components(menu_date, disabled=False):
    """buildVoteButtons'ın (mealComponents.js) REST karşılığı. customId: mv:<menuDate>:<y|n>."""
    return [
        {
            "type": 1,  # ACTION_ROW
            "components": [
                {
                    "type": 2,
                    "style": 3,  # SUCCESS
                    "label": "Yiyeceğim",
                    "emoji": {"name": "🟢"},
                    "custom_id": f"mv:{menu_date}:y",
                    "disabled": disabled,
                },
                {
                    "type": 2,
                    "style": 4,  # DANGER
                    "label": "Yemeyeceğim",
                    "emoji": {"name": "🔴"},
                    "custom_id": f"mv:{menu_date}:n",
                    "disabled": disabled,
                },
            ],
        }
    ]


def send_channel_message(channel_id, content=None, flow_id=None, step=None, components=None, embeds=None):
    payload = {}
    if content is not None:
        payload["content"] = content
    if embeds is not None:
        payload["embeds"] = embeds
    if components is not None:
        payload["components"] = components
    elif flow_id is not None:
        payload["components"] = build_components(flow_id, step or 0)
    resp = requests.post(f"{API_BASE}/channels/{channel_id}/messages", headers=_headers(), json=payload, timeout=TIMEOUT)
    log.warning(
        "[DM-TESHIS] POST /channels/%s/messages -> status=%s body=%s",
        channel_id, resp.status_code, resp.text[:500],
    )
    if not resp.ok:
        raise DiscordError(_friendly(resp))
    return resp.json()


def edit_channel_message(channel_id, message_id, content, components=None):
    payload = {"content": content, "components": components or []}
    resp = requests.patch(
        f"{API_BASE}/channels/{channel_id}/messages/{message_id}", headers=_headers(), json=payload, timeout=TIMEOUT
    )
    if not resp.ok:
        raise DiscordError(_friendly(resp))
    return resp.json()


def delete_channel_message(channel_id, message_id):
    """Bir kanal mesajını siler. Mesaj zaten yoksa (404) sessizce başarılı sayılır."""
    resp = requests.delete(f"{API_BASE}/channels/{channel_id}/messages/{message_id}", headers=_headers(), timeout=TIMEOUT)
    if not resp.ok and resp.status_code != 404:
        raise DiscordError(_friendly(resp))


def open_dm_channel(user_id):
    log.warning("[DM-TESHIS] open_dm_channel() cagrildi. Discord API'ye gonderilen user_id=%r", user_id)
    resp = requests.post(
        f"{API_BASE}/users/@me/channels", headers=_headers(), json={"recipient_id": user_id}, timeout=TIMEOUT
    )
    log.warning(
        "[DM-TESHIS] POST /users/@me/channels -> status=%s body=%s",
        resp.status_code, resp.text[:500],
    )
    if not resp.ok:
        raise DiscordError(_friendly(resp))
    return resp.json()["id"]


def send_direct_message(user_id, content=None, embeds=None):
    """
    Hata firlatmaz — DM basarisiz olursa (ok, message) doner (dutyNotifier.service.js
    ile ayni sozlesme). Node botunun bot.js -> sendDirectMessage() fonksiyonunun
    REST karsiligidir: ikisi de AYNI iki Discord REST cagrisini yapar:
      1) POST /users/@me/channels  {recipient_id: user_id}   (discord.js: user.send() -> createDM())
      2) POST /channels/{channel_id}/messages {content}       (discord.js: dmChannel.send())
    Node tarafi bunu bir discord.js Client uzerinden (Gateway baglantili) yapar,
    burasi dogrudan HTTP ile yapar; Discord API seviyesinde ikisi ayni istektir.

    `embeds` verilirse (orn. yemek sonuc bildirimi) mesaj bir Discord Embed
    olarak gonderilir; `content` de birlikte verilebilir ama zorunlu degildir.
    """
    log.warning("[DM-TESHIS] send_direct_message() cagrildi. Fonksiyon adi=discord_client.send_direct_message, gelen user_id=%r", user_id)
    try:
        channel_id = open_dm_channel(user_id)
        log.warning("[DM-TESHIS] DM kanali acildi: channel_id=%s", channel_id)
        result = send_channel_message(channel_id, content, embeds=embeds)
        log.warning("[DM-TESHIS] Mesaj gonderildi. Discord mesaj id=%s", result.get("id"))
        return True, "Özel mesaj gönderildi."
    except DiscordError as exc:
        log.warning("[DM-TESHIS] BASARISIZ: %s", exc)
        return False, str(exc)
    except requests.RequestException as exc:
        log.warning("[DM-TESHIS] AG HATASI: %s", exc)
        return False, f"Discord sunucularına ulaşılamıyor: {exc}"


def is_configured():
    return bool(settings_service.get("discord_bot_token"))
