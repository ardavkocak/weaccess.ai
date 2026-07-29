"""Yemek menüsü duyuru metni — discord/mealMessages.js'in Python portu.

Örnek çıktı:

  🍽️ **Yarının Yemek Menüsü**

  📅 23 Temmuz 2026 Perşembe

  🥣 Mercimek Çorbası (120 kcal)
  🍗 Tavuk Sote (420 kcal)
  🍚 Pirinç Pilavı (310 kcal)
  🥗 Mevsim Salata (70 kcal)

  Yarın yemek yiyecek misiniz? Lütfen aşağıdaki butonlardan birini seçiniz.

  🍽️ **Katılım Durumu**

  ✅ Yiyeceğim (18)
  ❌ Yemeyeceğim (5)
"""
from __future__ import annotations

import re

from .messages import day_label
from .date_utils import format_long_tr
from .text_utils import normalize_tr

# Kalıplar ASCII yazılır (bkz. text_utils.normalize_tr): menüler çoğunlukla
# TAMAMI BÜYÜK HARF gelir ve Türkçe'de büyük/küçük harf dönüşümü "İ/I" sorunu
# yüzünden güvenilir değildir. Sıra ÖNEMLİDİR: ilk eşleşen kural kazanır.
ICON_RULES = [
    (re.compile(r"corba"), "🥣"),
    (re.compile(r"salata|sogus|piyaz"), "🥗"),
    (re.compile(r"pilav|bulgur|makarna|eriste|spagetti|spaghetti|penne|noodle"), "🍚"),
    (re.compile(
        r"tatli|balli|pasta|baklava|sutlac|kek|puding|helva|revani|magnolia|"
        r"supangle|trilece|browni|muhallebi|panna|asure|kunefe|profiterol"
    ), "🍰"),
    (re.compile(r"meyve|elma|portakal|karpuz|uzum|muz|kavun"), "🍎"),
    (re.compile(r"ayran|yogurt|cacik|kefir|sut(?!lac)"), "🥛"),
    (re.compile(r"tavuk|pilic|hindi|shnitzel|sniztel"), "🍗"),
    (re.compile(r"balik|hamsi|somon|levrek|palamut"), "🐟"),
    (re.compile(r"kofte|\bet\b|etli|kebap|kebabi|biftek|kavurma|sote|tava|sarma|kilis|bahcivan"), "🥩"),
    (re.compile(r"bore[kg]|pogaca|pide|lahmacun|manti|gozleme"), "🥧"),
    (re.compile(r"pizza|burger|sandvic|tost"), "🍔"),
    (re.compile(r"fasulye|nohut|mercimek|bakla|turlu|sebze|dolma|musakka|ispanak|bezelye|patlican|begendi"), "🥘"),
    (re.compile(r"patates|kizartma"), "🍟"),
    (re.compile(r"mesrubat|cay|kahve|icecek|limonata|komposto|soda|kola"), "🥤"),
]

COUNTS_HEADING = "🍽️ **Katılım Durumu**"


def icon_for(dish: str) -> str:
    text = normalize_tr(dish)
    for pattern, icon in ICON_RULES:
        if pattern.search(text):
            return icon
    return "🍽️"


def render_counts(counts=None) -> str:
    counts = counts or {}
    yes = counts.get("yes", 0)
    no = counts.get("no", 0)
    return "\n".join([
        COUNTS_HEADING,
        "",
        f"✅ Yiyeceğim ({yes})",
        f"❌ Yemeyeceğim ({no})",
    ])


def total_kcal(items) -> int | None:
    """Menüdeki tüm yemeklerin kalori toplamı; hiçbirinde kalori yoksa None."""
    values = [item.get("kcal") for item in items if item.get("kcal") is not None]
    return sum(values) if values else None


def render_announcement(menu, counts=None) -> str:
    """
    @param menu   {"menu_date": "YYYY-MM-DD", "items": [{"name", "kcal"}, ...]}
    @param counts {"yes": int, "no": int}
    """
    date_line = format_long_tr(menu["menu_date"])
    day = day_label(menu["menu_date"])

    dishes = "\n".join(
        f"{icon_for(item['name'])} {item['name']}" + (f" ({item['kcal']} kcal)" if item.get("kcal") is not None else "")
        for item in menu["items"]
    )

    return "\n".join([
        f"🍽️ **{day['genitive']} Yemek Menüsü**",
        "",
        f"📅 {date_line}",
        "",
        dishes,
        "",
        f"{day['plain']} yemek yiyecek misiniz? Lütfen aşağıdaki butonlardan birini seçiniz.",
        "",
        render_counts(counts),
    ])
