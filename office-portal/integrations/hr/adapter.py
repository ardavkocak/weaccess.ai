"""IK Otomasyonu (ik-otomasyon) icin entegrasyon adapteru.

Faz 3 durumu: TAM ENTEGRASYON aktif. apps.hr, orijinal projenin is
mantigini (Excel okuma, tarih kurallari, hatirlatma) Python'a portlayip
Portal'in kendi veritabaninda calisiyor. Iframe veya harici port yok.
"""
from integrations.base import BaseIntegration, IntegrationInfo, IntegrationStatus


class HrIntegration(BaseIntegration):
    info = IntegrationInfo(
        key="hr",
        name="İK Otomasyonu",
        source_project="ik-otomasyon",
        tech_stack="Django (Portal ile aynı süreç, PostgreSQL)",
        planned_mode="native_port",
        notes=(
            "Excel okuma, tarih kurallari (dogum gunu/yil donumu) ve "
            "hatirlatma mantigi Python'a portlanip apps.hr icinde native "
            "olarak calisiyor. Gunluk hatirlatma e-postasi icin "
            "'send_hr_reminders' management komutu OS cron/systemd "
            "timer ile is gunlerinde 09:00'da calistirilmali."
        ),
    )

    def get_status(self) -> str:
        return IntegrationStatus.CONNECTED if self._db_ok() else IntegrationStatus.NOT_CONNECTED

    def health_check(self):
        if self._db_ok():
            return True, f"{self.info.name} Portal içinde native çalışıyor."
        return False, f"{self.info.name} veritabanı bağlantısı kurulamadı."

    @staticmethod
    def _db_ok() -> bool:
        try:
            from apps.hr.models import HrSettings

            HrSettings.objects.exists()
            return True
        except Exception:
            return False
