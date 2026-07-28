"""Calisan telefon alanini kaldirir, TC Kimlik No ve Ise Giris Tarihi ekler.

Ayrica iade tutanagi icin Assignment modeline iade durumu ve hasar aciklamasi
alanlarini ekler.

tc_kimlik_no benzersiz ve zorunlu oldugu icin mevcut kayitlar once gecici bir
yer tutucu deger ile doldurulur (populate_employee_identity); bu degerler
sistem yoneticisi tarafindan gercek TC numaralari ile guncellenmelidir.
"""
import django.core.validators
from django.db import migrations, models
from django.utils import timezone

# Yer tutucu TC numaralari bu taban degerin uzerine pk eklenerek uretilir;
# boylece 11 haneli ve benzersiz kalirlar.
PLACEHOLDER_TC_BASE = 90000000000


def populate_employee_identity(apps, schema_editor):
    """Mevcut calisanlara gecici TC No ve ise giris tarihi atar."""
    Employee = apps.get_model("inventory", "Employee")
    today = timezone.localdate()
    for employee in Employee.objects.all():
        employee.tc_kimlik_no = str(PLACEHOLDER_TC_BASE + employee.pk)
        employee.hire_date = employee.created_at.date() if employee.created_at else today
        employee.save(update_fields=["tc_kimlik_no", "hire_date"])


def clear_employee_identity(apps, schema_editor):
    """Geri alma senaryosunda alanlari bosaltir (veri kaybi olmadan geri donus)."""
    Employee = apps.get_model("inventory", "Employee")
    Employee.objects.update(tc_kimlik_no=None, hire_date=None)


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0001_initial"),
    ]

    operations = [
        # 1) Alanlari once null=True olarak ekle ki mevcut satirlar bozulmasin.
        migrations.AddField(
            model_name="employee",
            name="tc_kimlik_no",
            field=models.CharField(max_length=11, null=True, verbose_name="TC Kimlik No"),
        ),
        migrations.AddField(
            model_name="employee",
            name="hire_date",
            field=models.DateField(null=True, verbose_name="Ise Giris Tarihi"),
        ),
        # 2) Mevcut kayitlari doldur.
        migrations.RunPython(populate_employee_identity, clear_employee_identity),
        # 3) Alanlari nihai (zorunlu / benzersiz) hallerine getir.
        migrations.AlterField(
            model_name="employee",
            name="tc_kimlik_no",
            field=models.CharField(
                help_text="11 haneli TC Kimlik Numarasi.",
                max_length=11,
                unique=True,
                validators=[
                    django.core.validators.RegexValidator(
                        message="TC Kimlik No 11 haneli olmali ve yalnizca rakam icermelidir.",
                        regex="^\\d{11}$",
                    )
                ],
                verbose_name="TC Kimlik No",
            ),
        ),
        migrations.AlterField(
            model_name="employee",
            name="hire_date",
            field=models.DateField(verbose_name="Ise Giris Tarihi"),
        ),
        # 4) Artik kullanilmayan telefon alanini kaldir.
        migrations.RemoveField(
            model_name="employee",
            name="phone",
        ),
        # 5) Iade tutanagi icin gereken alanlar.
        migrations.AddField(
            model_name="assignment",
            name="return_condition",
            field=models.CharField(
                blank=True,
                choices=[
                    ("undamaged", "Hasarsiz Teslim Edildi"),
                    ("damaged", "Hasarli Teslim Edildi"),
                    ("missing", "Eksik Teslim Edildi"),
                ],
                max_length=20,
                verbose_name="Iade Durumu",
            ),
        ),
        migrations.AddField(
            model_name="assignment",
            name="damage_description",
            field=models.TextField(blank=True, verbose_name="Hasar / Eksik Aciklamasi"),
        ),
    ]
