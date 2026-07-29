"""Stok yapisina gecisle birlikte kullanimdan kalkan modelleri siler.

* Department  -> yerini Company aldi (bkz. 0003).
* Brand / DeviceCategory -> cihaz adi tek alanda tutuldugu icin gereksiz.
* Maintenance -> stok mantiginda tekil birim bakimi izlenmiyor.

Bu modellere ait tablolar ve kayitli veriler kalici olarak silinir.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0006_device_stock_cleanup"),
    ]

    operations = [
        # Department.manager -> Employee FK'si, model silinmeden once dusurulur.
        migrations.RemoveField(model_name="department", name="manager"),
        migrations.RemoveField(model_name="maintenance", name="device"),
        migrations.DeleteModel(name="Maintenance"),
        migrations.DeleteModel(name="Department"),
        migrations.DeleteModel(name="Brand"),
        migrations.DeleteModel(name="DeviceCategory"),
        migrations.AlterField(
            model_name="activitylog",
            name="action_type",
            field=models.CharField(
                choices=[
                    ("create", "Olusturma"),
                    ("update", "Guncelleme"),
                    ("delete", "Silme"),
                    ("login", "Giris"),
                    ("logout", "Cikis"),
                    ("assign", "Zimmetleme"),
                    ("return", "Iade"),
                    ("other", "Diger"),
                ],
                max_length=20,
                verbose_name="Islem Tipi",
            ),
        ),
    ]
