from django.apps import AppConfig


class MonthlyTrackingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.monthly_tracking"
    label = "monthly_tracking"
    verbose_name = "Aylık Takip"
