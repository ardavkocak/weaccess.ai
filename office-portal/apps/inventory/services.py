"""Envanter uygulamasinin temel is mantigi (zimmetleme, iade, aktivite kaydi).

View katmanini sade tutmak ve kurallarin tek bir yerde toplanmasini saglamak
icin zimmetleme/iade gibi coklu adim gerektiren islemler burada tanimlanir.

Stok mantigi: cihazin toplam adedi hicbir zaman degismez. Bosta adet, toplam
adetten aktif zimmet sayisi cikarilarak hesaplanir; bu nedenle zimmet/iade
islemleri ayrica bir sayac guncellemez, yalnizca Assignment kaydi olusturur ya
da kapatir.
"""
from django.core.exceptions import ValidationError
from django.db import transaction
from django.urls import reverse
from django.utils import timezone

from .models import ActivityLog, Assignment, Device, Notification


def log_activity(user, action_type, description, ip_address=None):
    """Sisteme yeni bir ActivityLog kaydi ekler."""
    return ActivityLog.objects.create(
        user=user if (user and user.is_authenticated) else None,
        action_type=action_type,
        description=description,
        ip_address=ip_address,
    )


def notify_user(user, title, message, link=""):
    """Bir kullaniciya bildirim olusturur. Kullanici None ise sessizce atlanir."""
    if user is None:
        return None
    return Notification.objects.create(user=user, title=title, message=message, link=link)


def notify_admins(title, message, link=""):
    """Sistemdeki tum admin kullanicilarina bildirim gonderir."""
    from django.contrib.auth import get_user_model

    User = get_user_model()
    admins = User.objects.filter(role=User.Role.ADMIN, is_active=True)
    Notification.objects.bulk_create(
        [Notification(user=admin, title=title, message=message, link=link) for admin in admins]
    )


def _merge_item_quantities(items):
    """(cihaz, adet) ciftlerini cihaz bazinda toplar, satir sirasini korur.

    Ayni cihaz formda birden fazla satirda secilmis olabilir; stok kontrolunun
    dogru calismasi icin adetler tek kalemde toplanmalidir.
    """
    merged = {}
    for device, quantity in items:
        if quantity < 1:
            raise ValidationError(f"{device} icin adet en az 1 olmalidir.")
        if device.pk in merged:
            merged[device.pk] = (device, merged[device.pk][1] + quantity)
        else:
            merged[device.pk] = (device, quantity)
    return list(merged.values())


@transaction.atomic
def assign_devices(
    *, employee, items, assigned_by, assigned_date=None, expected_return_date=None, notes="", ip_address=None
):
    """Bir calisana ayni islemde birden fazla cihazi (adetleriyle) zimmetler.

    Her cihazin stogu ayri ayri kontrol edilir; herhangi biri icin bosta adet
    yetersizse hicbir kayit olusturulmaz (islem tumuyle geri alinir).

    Stok mantigi degismez: her adet icin bir Assignment kaydi olusturulur,
    bosta adet yine "toplam adet - aktif zimmet sayisi" olarak hesaplanir.

    Args:
        items: [(Device, adet), ...] listesi.

    Returns:
        Olusturulan Assignment kayitlari (satir sirasiyla).
    """
    merged_items = _merge_item_quantities(items)
    if not merged_items:
        raise ValidationError("En az bir cihaz secilmelidir.")

    # Es zamanli isteklerde kilitlenme (deadlock) olmamasi icin cihaz satirlari
    # daima ayni sirayla (pk) kilitlenir.
    locked_devices = {
        device.pk: device
        for device in Device.objects.select_for_update()
        .filter(pk__in=[device.pk for device, _ in merged_items])
        .order_by("pk")
    }

    # Once tum stoklar dogrulanir; boylece yetersiz stokta kismi kayit olusmaz.
    for device, quantity in merged_items:
        locked = locked_devices[device.pk]
        if locked.available_count < quantity:
            raise ValidationError(
                f"{locked} icin yeterli stok yok. Bosta: {locked.available_count} adet, "
                f"istenen: {quantity} adet."
            )

    assignments = []
    for device, quantity in merged_items:
        locked = locked_devices[device.pk]
        for _ in range(quantity):
            assignment = Assignment(
                employee=employee,
                device=locked,
                assigned_date=assigned_date or timezone.localdate(),
                expected_return_date=expected_return_date,
                notes=notes,
                assigned_by=assigned_by,
            )
            assignment.full_clean()
            assignment.save()
            assignments.append(assignment)

        log_activity(
            assigned_by,
            ActivityLog.ActionType.ASSIGN,
            f"{locked} ({quantity} adet) {employee} adli calisana zimmetlendi.",
            ip_address,
        )

    summary = ", ".join(f"{device} ({quantity} adet)" for device, quantity in merged_items)
    notify_user(
        employee.user,
        "Yeni Zimmet Olusturuldu",
        f"Uzerinize zimmetlendi: {summary}"[:255],
        link=reverse("inventory:my-assignments"),
    )
    return assignments


def assign_device(
    *, employee, device, assigned_by, assigned_date=None, expected_return_date=None, notes="", ip_address=None
):
    """Tek bir cihazdan bir adet zimmetler (assign_devices icin ince sarmalayici)."""
    return assign_devices(
        employee=employee,
        items=[(device, 1)],
        assigned_by=assigned_by,
        assigned_date=assigned_date,
        expected_return_date=expected_return_date,
        notes=notes,
        ip_address=ip_address,
    )[0]


@transaction.atomic
def return_device(
    *, assignment, returned_by, return_notes="", return_condition="", damage_description="", ip_address=None
):
    """Bir zimmet kaydini iade olarak isaretler; adet otomatik stoga doner.

    Iade durumu (hasarsiz/hasarli/eksik) yalnizca iade tutanagina yazilmak uzere
    kaydedilir; toplam adet hicbir kosulda degismez.
    """
    assignment = Assignment.objects.select_for_update().get(pk=assignment.pk)

    if assignment.returned:
        raise ValidationError("Bu zimmet kaydi zaten iade edilmis.")

    assignment.returned = True
    assignment.returned_date = timezone.localdate()
    assignment.return_notes = return_notes
    assignment.return_condition = return_condition
    assignment.damage_description = damage_description
    assignment.returned_by = returned_by
    assignment.save(
        update_fields=[
            "returned",
            "returned_date",
            "return_notes",
            "return_condition",
            "damage_description",
            "returned_by",
            "updated_at",
        ]
    )

    device = assignment.device
    log_activity(
        returned_by,
        ActivityLog.ActionType.RETURN,
        f"{device} cihazi {assignment.employee} tarafindan iade edildi.",
        ip_address,
    )
    # Cihaz detay sayfasi yalnizca adminlere acik oldugu icin personel kendi
    # zimmet ekranina yonlendirilir.
    notify_user(
        assignment.employee.user,
        "Cihaz Iadesi Alindi",
        f"{device} cihazinin iadesi basariyla alindi.",
        link=reverse("inventory:my-assignments"),
    )
    return assignment
