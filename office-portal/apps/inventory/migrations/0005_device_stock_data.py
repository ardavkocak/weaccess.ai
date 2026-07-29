"""Mevcut cihazlari envanter (birim bazli) yapisindan stok (adet bazli) yapisina tasir.

Eski yapida her fiziksel cihaz ayri bir satirdi (seri no / envanter no ile).
Yeni yapida ayni urun tek satirdir ve yalnizca toplam adedi tutulur.

Strateji: mevcut cihazlar "Marka Model" adina gore gruplanir. Her grubun ilk
kaydi stok satiri olarak korunur, toplam adedi grubun eleman sayisina esitlenir
ve gruptaki diger cihazlara ait zimmet kayitlari bu satira tasinir. Boylece
hicbir zimmet kaydi kaybolmaz.
"""
from django.db import migrations

MAX_NAME_LENGTH = 150


def _stock_name(device):
    """Eski marka + model bilgisinden stok adi uretir."""
    brand = device.brand.name if device.brand_id else ""
    name = f"{brand} {device.model_name}".strip() or "Isimsiz Cihaz"
    return name[:MAX_NAME_LENGTH]


def convert_devices_to_stock(apps, schema_editor):
    Device = apps.get_model("inventory", "Device")
    Assignment = apps.get_model("inventory", "Assignment")

    groups = {}
    for device in Device.objects.select_related("brand").order_by("pk"):
        groups.setdefault(_stock_name(device), []).append(device)

    for name, devices in groups.items():
        canonical, duplicates = devices[0], devices[1:]
        canonical.name = name
        canonical.total_quantity = len(devices)
        canonical.save(update_fields=["name", "total_quantity"])

        if duplicates:
            duplicate_pks = [device.pk for device in duplicates]
            # Zimmetler once tasinir, ardindan fazla cihaz satirlari silinir.
            Assignment.objects.filter(device_id__in=duplicate_pks).update(device_id=canonical.pk)
            Device.objects.filter(pk__in=duplicate_pks).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0004_device_stock_fields"),
    ]

    operations = [
        # Birim bazli kayitlar geri getirilemeyecegi icin geri alma islemsizdir.
        migrations.RunPython(convert_devices_to_stock, migrations.RunPython.noop),
    ]
