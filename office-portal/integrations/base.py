"""
Tum entegrasyon adapterlerinin ortak temeli.

Bu katman, Office Portal'in mevcut bagimsiz projelerle (Zimmet Sistemi,
Ofis Gorev Takibi, IK Otomasyonu, Aylik Takip, Dokumantasyon Otomasyonu)
nasil konusacagini tanimlayan SOZLESMEDIR. Bu asamada hicbir adapter
gercek bir baglanti kurmaz; hepsi "henuz baglanmadi" durumunu dondurur.

Ileride bir modul gercek entegrasyona gectiginde yalnizca ilgili
adapter'in metodlari doldurulur; Sidebar/Header/Dashboard/View katmani
degismeden kalir. Bu sayede "entegrasyon" ile "gorunum" birbirinden
tamamen ayrisir.
"""
from __future__ import annotations

from dataclasses import dataclass


class IntegrationStatus:
    """Bir entegrasyonun olabilecegi uc durum."""

    NOT_CONNECTED = "not_connected"
    PARTIAL = "partial"
    CONNECTED = "connected"

    LABELS = {
        NOT_CONNECTED: "Bağlantı kurulmadı",
        PARTIAL: "Kısmi entegrasyon",
        CONNECTED: "Bağlı",
    }


@dataclass
class IntegrationInfo:
    """Bir adapter'in kendini tanittigi sabit meta veri (kod degil, belge amacli)."""

    key: str
    name: str
    source_project: str  # weaccess.ai kokune gore relatif klasor adi
    tech_stack: str
    planned_mode: str  # "shared_db" | "api" | "reverse_proxy" | "tbd"
    notes: str = ""


class BaseIntegration:
    """Her modul entegrasyon adapterinin uygulamasi gereken ortak arayuz."""

    info: IntegrationInfo = None

    def get_status(self) -> str:
        """Su anki baglanti durumu. Varsayilan: hic baglanmadi."""
        return IntegrationStatus.NOT_CONNECTED

    def health_check(self):
        """(basarili_mi, mesaj) dondurur. Gercek baglanti kurulana kadar sabit kalir."""
        return False, f"{self.info.name} için entegrasyon henüz kurulmadı."

    def get_dashboard_summary(self) -> list:
        """Dashboard'da gosterilecek istatistik kartlari (baglaninca doldurulur)."""
        return []
