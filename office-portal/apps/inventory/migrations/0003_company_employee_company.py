"""Sirket (Company) modelini ekler; calisanlari departman yerine sirkete baglar.

Mevcut calisanlar, kaynak departmanlariyla bir eslesme kurulamayacagi icin
tanimli sirketlere sirayla (round-robin) dagitilir; dagilim, kayitlarin pk
sirasina gore deterministiktir. Calisanlarin gercek sirketleri daha sonra
admin panelinden duzeltilebilir.
"""
from django.db import migrations, models
import django.db.models.deletion

DEFAULT_COMPANIES = ["Craniocatch", "Engelsiz Ceviri", "Nevisoft"]


def create_companies_and_assign_employees(apps, schema_editor):
    Company = apps.get_model("inventory", "Company")
    Employee = apps.get_model("inventory", "Employee")

    companies = [Company.objects.get_or_create(name=name)[0] for name in DEFAULT_COMPANIES]

    for index, employee in enumerate(Employee.objects.order_by("pk")):
        employee.company = companies[index % len(companies)]
        employee.save(update_fields=["company"])


def remove_companies(apps, schema_editor):
    Company = apps.get_model("inventory", "Company")
    Employee = apps.get_model("inventory", "Employee")
    Employee.objects.update(company=None)
    Company.objects.filter(name__in=DEFAULT_COMPANIES).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0002_employee_tc_hire_date_assignment_return_condition"),
    ]

    operations = [
        migrations.CreateModel(
            name="Company",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Olusturulma Tarihi")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Guncellenme Tarihi")),
                ("name", models.CharField(max_length=100, unique=True, verbose_name="Sirket Adi")),
            ],
            options={
                "verbose_name": "Sirket",
                "verbose_name_plural": "Sirketler",
                "ordering": ["name"],
            },
        ),
        # 1) Once null=True olarak ekle ki mevcut satirlar bozulmasin.
        migrations.AddField(
            model_name="employee",
            name="company",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="employees",
                to="inventory.company",
                verbose_name="Sirket",
            ),
        ),
        # 2) Sirketleri olustur ve mevcut calisanlari dagit.
        migrations.RunPython(create_companies_and_assign_employees, remove_companies),
        # 3) Alani zorunlu hale getir.
        migrations.AlterField(
            model_name="employee",
            name="company",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="employees",
                to="inventory.company",
                verbose_name="Sirket",
            ),
        ),
        # 4) Artik kullanilmayan alanlari kaldir.
        migrations.RemoveField(model_name="employee", name="department"),
        migrations.RemoveField(model_name="employee", name="position"),
    ]
