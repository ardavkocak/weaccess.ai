"""Model degisikliklerini otomatik olarak ActivityLog'a yazan sinyaller.

Assignment (zimmet) olusturma/iade islemleri kendine ozgu, daha aciklayici
mesajlar urettigi icin services.py icinde ayrica loglanir; burada tekrar
loglanmaz (cift kayit olusmamasi icin).
"""
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from common.utils import get_client_ip, get_current_request, get_current_user
from .models import ActivityLog, Company, Device, Employee


def _log(action_type, description):
    request = get_current_request()
    ActivityLog.objects.create(
        user=get_current_user(),
        action_type=action_type,
        description=description,
        ip_address=get_client_ip(request),
    )


@receiver(post_save, sender=Company)
@receiver(post_save, sender=Employee)
@receiver(post_save, sender=Device)
def log_model_saved(sender, instance, created, **kwargs):
    action = ActivityLog.ActionType.CREATE if created else ActivityLog.ActionType.UPDATE
    verb = "olusturuldu" if created else "guncellendi"
    _log(action, f"{sender._meta.verbose_name}: '{instance}' {verb}.")


@receiver(post_delete, sender=Company)
@receiver(post_delete, sender=Employee)
@receiver(post_delete, sender=Device)
def log_model_deleted(sender, instance, **kwargs):
    _log(ActivityLog.ActionType.DELETE, f"{sender._meta.verbose_name}: '{instance}' silindi.")


