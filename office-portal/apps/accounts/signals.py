"""Kullanici giris/cikis olaylarini ActivityLog kaydina yazan sinyaller."""
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.dispatch import receiver

from common.utils import get_client_ip


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    from apps.inventory.models import ActivityLog

    ActivityLog.objects.create(
        user=user,
        action_type=ActivityLog.ActionType.LOGIN,
        description=f"{user} sisteme giris yapti.",
        ip_address=get_client_ip(request),
    )


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    from apps.inventory.models import ActivityLog

    if user is None:
        return
    ActivityLog.objects.create(
        user=user,
        action_type=ActivityLog.ActionType.LOGOUT,
        description=f"{user} sistemden cikis yapti.",
        ip_address=get_client_ip(request),
    )


@receiver(user_login_failed)
def log_user_login_failed(sender, credentials, request=None, **kwargs):
    from apps.inventory.models import ActivityLog

    username = credentials.get("username", "bilinmiyor")
    ActivityLog.objects.create(
        user=None,
        action_type=ActivityLog.ActionType.OTHER,
        description=f"Basarisiz giris denemesi: '{username}'",
        ip_address=get_client_ip(request),
    )
