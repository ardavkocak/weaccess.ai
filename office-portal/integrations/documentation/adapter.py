"""Dokumantasyon Otomasyonu (dokumantasyon-otomasyon) icin entegrasyon adapteru.

Faz 3 durumu: TAM ENTEGRASYON aktif. `scraper.py` ve `sheets_export.py`
orijinal projeden degistirilmeden kopyalanip apps.documentation icinde
Portal'in kendi view'i tarafindan dogrudan cagrilir (iframe/harici port yok).
"""
from integrations.base import BaseIntegration, IntegrationInfo, IntegrationStatus


class DocumentationIntegration(BaseIntegration):
    info = IntegrationInfo(
        key="documentation",
        name="Dokümantasyon",
        source_project="dokumantasyon-otomasyon",
        tech_stack="Django (Portal ile aynı süreç) — scraper.py/sheets_export.py aynen yeniden kullanılıyor",
        planned_mode="native_port",
        notes=(
            "Tarama ve Google Sheets'e yazma mantığı orijinal projeden "
            "değiştirilmeden kopyalandı; yalnızca Flask form akışı Django "
            "view'ına çevrildi."
        ),
    )

    def get_status(self) -> str:
        return IntegrationStatus.CONNECTED if self._deps_ok() else IntegrationStatus.NOT_CONNECTED

    def health_check(self):
        if self._deps_ok():
            return True, f"{self.info.name} Portal içinde native çalışıyor."
        return False, f"{self.info.name} için gerekli kütüphaneler (bs4/gspread) eksik."

    @staticmethod
    def _deps_ok() -> bool:
        try:
            from apps.documentation import scraper  # noqa: F401

            return True
        except ImportError:
            return False
