"""
Tum entegrasyon adapterlerinin tek kayit noktasi.

Portal, hangi modulun hangi adapter'a karsilik geldigini bilmek
istediginde yalnizca bu dosyadaki `get_integration()` fonksiyonunu
cagirir; kaynak projeye dair her sey (yol, teknoloji, baglanti modu)
ilgili adapter'in icinde kalir.
"""
from integrations.discordbot.adapter import DiscordBotIntegration
from integrations.documentation.adapter import DocumentationIntegration
from integrations.hr.adapter import HrIntegration
from integrations.inventory.adapter import InventoryIntegration
from integrations.monthly_tracking.adapter import MonthlyTrackingIntegration
from integrations.office_bot.adapter import OfficeBotIntegration

_REGISTRY = {
    "inventory": InventoryIntegration(),
    "office_bot": OfficeBotIntegration(),
    "hr": HrIntegration(),
    "monthly_tracking": MonthlyTrackingIntegration(),
    "documentation": DocumentationIntegration(),
    "discordbot": DiscordBotIntegration(),
}


def get_integration(key):
    """Verilen anahtara karsilik gelen adapter'i dondurur, yoksa None."""
    return _REGISTRY.get(key)


def all_integrations():
    """Tum kayitli adapterleri dondurur (ileride genel bir durum sayfasi icin)."""
    return list(_REGISTRY.values())
