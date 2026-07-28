"""Stok yapisi icin yeni Device alanlarini ekler (sema adimi).

Veri tasima 0005'te, eski alanlarin kaldirilmasi 0006'da yapilir. PostgreSQL
ayni islem (transaction) icinde hem veri degistirip hem ALTER TABLE
calistirilmasina izin vermedigi icin ("pending trigger events") bu adimlar
bilerek ayri migration dosyalarina bolunmustur.
"""
from django.db import migrations, models

MAX_NAME_LENGTH = 150


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0003_company_employee_company"),
    ]

    operations = [
        # Stok mantiginda ayni cihaz birden fazla kisiye zimmetlenebilir.
        migrations.RemoveConstraint(
            model_name="assignment",
            name="unique_active_assignment_per_device",
        ),
        # Kaldirilacak alanlara bagli indeksler once dusurulur.
        migrations.RemoveIndex(model_name="device", name="inventory_d_status_458222_idx"),
        migrations.RemoveIndex(model_name="device", name="inventory_d_serial__ed8962_idx"),
        migrations.RemoveIndex(model_name="device", name="inventory_d_invento_8051a7_idx"),
        # Yeni alanlar once gevsek tanimla eklenir ki mevcut satirlar bozulmasin.
        migrations.AddField(
            model_name="device",
            name="name",
            field=models.CharField(max_length=MAX_NAME_LENGTH, null=True, verbose_name="Cihaz Adi"),
        ),
        migrations.AddField(
            model_name="device",
            name="total_quantity",
            field=models.PositiveIntegerField(default=1, verbose_name="Toplam Adet"),
        ),
    ]
