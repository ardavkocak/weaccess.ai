"""Aylik Takip (aylik-takip) icin entegrasyon adapteru.

Faz 3 durumu: TAM ENTEGRASYON aktif. Hesaplama, PDF/OCR mantigi Python'a
portlanip apps.monthly_tracking icinde native calisiyor (iframe/harici
port yok). Durum kontrolu, gerekli kutuphanelerin (pdfplumber, pytesseract)
yuklu olup olmadigini dogrular.
"""
from integrations.base import BaseIntegration, IntegrationInfo, IntegrationStatus


class MonthlyTrackingIntegration(BaseIntegration):
    info = IntegrationInfo(
        key="monthly_tracking",
        name="Çalışma Saati Hesaplama",
        source_project="aylik-takip",
        tech_stack="Django (Portal ile aynı süreç) + pdfplumber + pytesseract",
        planned_mode="native_port",
        notes=(
            "PDF koordinat tabanlı personel çıkarma ve OCR tabanlı izin "
            "okuma, orijinal JS algoritması birebir takip edilerek "
            "Python'a portlandı. GERÇEK ÖRNEK BELGELERLE doğrulanmadı — "
            "bkz. entegrasyon raporu."
        ),
    )

    def get_status(self) -> str:
        return IntegrationStatus.CONNECTED if self._deps_ok() else IntegrationStatus.NOT_CONNECTED

    def health_check(self):
        if self._deps_ok():
            return True, f"{self.info.name} Portal içinde native çalışıyor."
        return False, f"{self.info.name} için gerekli kütüphaneler (pdfplumber/pytesseract) eksik."

    @staticmethod
    def _deps_ok() -> bool:
        try:
            import pdfplumber  # noqa: F401
            import pytesseract  # noqa: F401

            return True
        except ImportError:
            return False
