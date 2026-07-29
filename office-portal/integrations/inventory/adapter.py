"""Zimmet Sistemi (zimmet-sistemi) icin entegrasyon adapteru.

Faz 2 durumu: TAM ENTEGRASYON aktif. apps.accounts/apps.inventory/
apps.dashboard portale kopyalanip Portal'in kendi Django projesine
(paylasilan veritabani ile) dahil edildi — bu yuzden diger modullerin
aksine "salt-okunur" veya "canli embed" degil, dogrudan ayni surecte
calisan bir Django uygulamasidir. health_check burada gercek bir
veritabani sorgusu deneyerek baglantiyi dogrular.
"""
from integrations.base import BaseIntegration, IntegrationInfo, IntegrationStatus


class InventoryIntegration(BaseIntegration):
    info = IntegrationInfo(
        key="inventory",
        name="Zimmet Yönetimi",
        source_project="zimmet-sistemi",
        tech_stack="Django 5 + PostgreSQL",
        planned_mode="shared_db",
        notes=(
            "Portal ile ayni framework (Django), ayni surecte, ayni "
            "veritabaninda calisir. apps.accounts.User portalin ortak "
            "kimlik dogrulama kaynagidir."
        ),
    )

    def get_status(self) -> str:
        return IntegrationStatus.CONNECTED if self._db_ok() else IntegrationStatus.NOT_CONNECTED

    def health_check(self):
        if self._db_ok():
            return True, f"{self.info.name} veritabanına bağlı (paylaşılan Django projesi)."
        return False, f"{self.info.name} veritabanı bağlantısı kurulamadı."

    @staticmethod
    def _db_ok() -> bool:
        try:
            from apps.inventory.models import Company

            Company.objects.exists()
            return True
        except Exception:
            return False
