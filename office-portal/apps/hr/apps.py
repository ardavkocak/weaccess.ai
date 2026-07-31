import sys

from django.apps import AppConfig


class HrConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.hr"
    label = "hr"
    verbose_name = "İK Otomasyonu"

    def ready(self):
        # manage.py ile calisan komutlarda (migrate, makemigrations, shell,
        # test vb.) zamanlayici BASLATILMAZ — yalnizca gercek web sureci
        # (gunicorn/runserver) icinde calisir.
        if "manage.py" in sys.argv[0]:
            return
        from . import scheduler

        scheduler.start()
