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


@receiver(post_delete, sender=Employee)
def delete_login_account_with_employee(sender, instance, **kwargs):
    """Calisan silindiginde giris hesabini da siler.

    Employee.user alani on_delete=SET_NULL'dur; bu yalnizca KULLANICI silindiginde
    calisandaki bagi bosaltir, tersi degil. Bu yuzden calisan silindiginde hesap
    ortada kalir ve ayni e-postayla yeni calisan eklenince ayni adrese sahip iki
    hesap olusarak e-posta ile girisi belirsiz hale getirirdi.
    """
    if not instance.user_id:
        return
    from django.contrib.auth import get_user_model

    get_user_model().objects.filter(pk=instance.user_id).delete()


@receiver(post_save, sender=Employee)
def create_login_account_for_employee(sender, instance, created, **kwargs):
    """Yeni calisan hangi yoldan eklenirse eklensin giris hesabini olusturur.

    Kural bilerek model katmanindadir. Yalnizca "Yeni Calisan Ekle" ekranina
    bagli kalsaydi, Django admin panelinden, kabuktan veya toplu ice aktarmayla
    eklenen calisan hesapsiz kalir ve sisteme hic giris yapamazdi.

    Hesabi zaten olan calisanlar (ve ad/soyad guncellemeleri) atlanir; bu yuzden
    mevcut kayitlarin sifreleri hicbir kosulda sifirlanmaz.
    """
    if not created or instance.user_id:
        return
    from apps.accounts.services import create_user_for_employee

    create_user_for_employee(instance)
