"""Stok yapisina gecisin son adimi: alanlari kesinlestirir, envanter alanlarini siler.

Veri tasima 0005'te tamamlandigi icin bu adimda cihaz adi zorunlu ve benzersiz
hale getirilebilir.
"""
import django.core.validators
from django.db import migrations, models

MAX_NAME_LENGTH = 150


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0005_device_stock_data"),
    ]

    operations = [
        migrations.AlterField(
            model_name="device",
            name="name",
            field=models.CharField(max_length=MAX_NAME_LENGTH, unique=True, verbose_name="Cihaz Adi"),
        ),
        migrations.AlterField(
            model_name="device",
            name="total_quantity",
            field=models.PositiveIntegerField(
                default=1,
                validators=[django.core.validators.MinValueValidator(0)],
                verbose_name="Toplam Adet",
            ),
        ),
        # Envanter (birim bazli) mantigina ait alanlar tamamen kaldirilir.
        migrations.RemoveField(model_name="device", name="category"),
        migrations.RemoveField(model_name="device", name="brand"),
        migrations.RemoveField(model_name="device", name="model_name"),
        migrations.RemoveField(model_name="device", name="serial_number"),
        migrations.RemoveField(model_name="device", name="inventory_number"),
        migrations.RemoveField(model_name="device", name="purchase_date"),
        migrations.RemoveField(model_name="device", name="purchase_price"),
        migrations.RemoveField(model_name="device", name="warranty_end_date"),
        migrations.RemoveField(model_name="device", name="description"),
        migrations.RemoveField(model_name="device", name="photo"),
        migrations.RemoveField(model_name="device", name="status"),
        migrations.RemoveField(model_name="device", name="invoice_file"),
        migrations.RemoveField(model_name="device", name="warranty_document"),
        migrations.RemoveField(model_name="device", name="qr_code"),
        migrations.RemoveField(model_name="device", name="barcode"),
        migrations.AlterModelOptions(
            name="device",
            options={"ordering": ["name"], "verbose_name": "Cihaz", "verbose_name_plural": "Cihazlar"},
        ),
        migrations.AddIndex(
            model_name="device",
            index=models.Index(fields=["name"], name="inventory_d_name_59f036_idx"),
        ),
    ]
