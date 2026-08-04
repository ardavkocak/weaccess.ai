import sys

from django.apps import AppConfig


class OfficeBotConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.office_bot"
    label = "office_bot"
    verbose_name = "Görev Takibi ve Yemek Sistemi"

    def ready(self):
        # manage.py ile calisan komutlarda (migrate, makemigrations, shell,
        # test vb.) zamanlayici BASLATILMAZ — yalnizca gercek web sureci
        # (gunicorn/runserver) icinde calisir (bkz. apps.hr.apps ayni desen).
        if "manage.py" in sys.argv[0]:
            return
        from . import scheduler

        scheduler.start()
