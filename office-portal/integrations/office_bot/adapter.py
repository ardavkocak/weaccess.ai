"""Ofis Gorev Takibi (ofis-gorev-takibi) icin entegrasyon adapteru.

Faz 3 durumu: TAM ENTEGRASYON aktif. apps.office_bot, orijinal projenin
SQLite dosyasina Django ORM (unmanaged modeller + router) uzerinden
DOGRUDAN okur/yazar. Orijinal Express sureci (Discord bot + cron) kendi
surecinde, ayni dosyada calismaya devam eder; iframe veya harici port
yonlendirmesi yoktur (bkz. apps/office_bot/router.py).
"""
from integrations.base import BaseIntegration, IntegrationInfo, IntegrationStatus


class OfficeBotIntegration(BaseIntegration):
    info = IntegrationInfo(
        key="office_bot",
        name="Ofis Görev Takibi",
        source_project="ofis-gorev-takibi",
        tech_stack="Django ORM (Portal ile aynı süreç) + paylaşılan SQLite",
        planned_mode="native_port",
        notes=(
            "Personel/ayarlar/geçmiş/yemek menüsü CRUD'ı Portal'da native "
            "çalışır; Discord bot ve cron orijinal Node sürecinde, aynı "
            "SQLite dosyasını okuyarak değişmeden çalışmaya devam eder."
        ),
    )

    def get_status(self) -> str:
        return IntegrationStatus.CONNECTED if self._db_ok() else IntegrationStatus.NOT_CONNECTED

    def health_check(self):
        if self._db_ok():
            return True, f"{self.info.name} Portal içinde native çalışıyor (paylaşılan SQLite)."
        return False, (
            f"{self.info.name} veritabanına ulaşılamadı. Orijinal uygulamayı "
            "(ofis-gorev-takibi) en az bir kez çalıştırın."
        )

    @staticmethod
    def _db_ok() -> bool:
        try:
            from apps.office_bot.models import DutyType

            DutyType.objects.exists()
            return True
        except Exception:
            return False
