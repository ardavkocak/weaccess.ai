"""Ilk kurulum sonrasi sistemi test edilebilir hale getiren ornek veri komutu.

Kullanim:
    python manage.py seed_data            # veritabani bossa ornek veri olusturur
    python manage.py seed_data --reset    # mevcut ornek verileri silip yeniden olusturur
"""
import random
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from faker import Faker

from apps.inventory import services
from apps.inventory.models import ActivityLog, Assignment, Company, Device, Employee

User = get_user_model()
fake = Faker("tr_TR")

COMPANIES = ["Craniocatch", "Engelsiz Ceviri", "Nevisoft"]

# (cihaz adi, toplam adet) ciftleri: sistem stok mantigiyla calisir.
DEVICES = [
    ("Apple MacBook Air M4", 5),
    ("Apple MacBook Pro M4", 4),
    ("Dell Latitude 5540", 6),
    ("Lenovo ThinkPad E16", 7),
    ("HP EliteBook 840", 4),
    ("Lenovo Mouse", 12),
    ("Logitech Kablosuz Klavye", 10),
    ("Dell 24 inc Monitor", 8),
    ("HP Masaustu Bilgisayar", 5),
    ("Apple iPhone 15", 3),
    ("Samsung Galaxy Tab S9", 3),
    ("HP LaserJet Yazici", 2),
    ("Jabra Kulaklik", 9),
    ("Anker USB-C Hub", 6),
]


class Command(BaseCommand):
    help = "Sistemi test etmek icin ornek sirket, calisan, cihaz stogu ve zimmet verisi olusturur."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Mevcut ornek verileri silip yeniden olusturur (superuser hesaplari korunur).",
        )

    def handle(self, *args, **options):
        if options["reset"]:
            self._reset_data()
        elif Company.objects.exists():
            self.stdout.write(self.style.WARNING("Veritabaninda zaten veri mevcut. Islem atlaniyor."))
            self.stdout.write(self.style.WARNING("Yeniden olusturmak icin: python manage.py seed_data --reset"))
            return

        with transaction.atomic():
            admin_user = self._create_admin()
            companies = self._create_companies()
            employees = self._create_employees(companies)
            self._create_staff_accounts(employees)
            devices = self._create_devices()
            self._create_assignments(employees, devices, admin_user)

        self.stdout.write(self.style.SUCCESS("Ornek veriler basariyla olusturuldu."))
        self.stdout.write(self.style.SUCCESS("Admin girisi -> kullanici adi: admin | sifre: Admin12345!"))
        self.stdout.write(self.style.SUCCESS("Personel girisi -> ornek: e-posta adresleri | sifre: Personel12345!"))

    # ------------------------------------------------------------------
    def _reset_data(self):
        self.stdout.write("Mevcut ornek veriler siliniyor...")
        Assignment.objects.all().delete()
        Device.objects.all().delete()
        Employee.objects.all().delete()
        Company.objects.all().delete()
        ActivityLog.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()

    def _create_admin(self):
        admin_user, created = User.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@zimmetsistemi.local",
                "first_name": "Sistem",
                "last_name": "Yoneticisi",
                "role": User.Role.ADMIN,
                "is_staff": True,
                "is_superuser": True,
            },
        )
        if created:
            admin_user.set_password("Admin12345!")
            admin_user.save()
        return admin_user

    def _create_companies(self):
        return [Company.objects.get_or_create(name=name)[0] for name in COMPANIES]

    def _create_employees(self, companies, total=25):
        employees = []
        used_emails = set(Employee.objects.values_list("email", flat=True))
        used_tc_numbers = set(Employee.objects.values_list("tc_kimlik_no", flat=True))
        today = timezone.localdate()
        for _ in range(total):
            first_name = fake.first_name()
            last_name = fake.last_name()
            employees.append(
                Employee.objects.create(
                    first_name=first_name,
                    last_name=last_name,
                    email=self._unique_email(first_name, last_name, used_emails),
                    tc_kimlik_no=self._unique_tc_kimlik_no(used_tc_numbers),
                    hire_date=today - timedelta(days=random.randint(30, 3650)),
                    company=random.choice(companies),
                    is_active=True,
                )
            )
        return employees

    @staticmethod
    def _unique_email(first_name, last_name, used_emails):
        base = f"{first_name}.{last_name}".lower().replace(" ", "")
        base = (
            base.replace("ı", "i").replace("ğ", "g").replace("ü", "u")
            .replace("ş", "s").replace("ö", "o").replace("ç", "c")
        )
        email = f"{base}@sirket.com.tr"
        counter = 1
        while email in used_emails:
            email = f"{base}{counter}@sirket.com.tr"
            counter += 1
        used_emails.add(email)
        return email

    @staticmethod
    def _unique_tc_kimlik_no(used_tc_numbers):
        """Ornek veri icin 11 haneli, benzersiz (gercek olmayan) bir TC No uretir."""
        while True:
            value = str(random.randint(10_000_000_000, 99_999_999_999))
            if value not in used_tc_numbers:
                used_tc_numbers.add(value)
                return value

    def _create_staff_accounts(self, employees, count=8):
        for employee in random.sample(employees, min(count, len(employees))):
            username = employee.email.split("@")[0]
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": employee.email,
                    "first_name": employee.first_name,
                    "last_name": employee.last_name,
                    "role": User.Role.STAFF,
                },
            )
            if created:
                user.set_password("Personel12345!")
                user.save()
            employee.user = user
            employee.save(update_fields=["user"])

    def _create_devices(self):
        return [
            Device.objects.create(name=name, total_quantity=quantity) for name, quantity in DEVICES
        ]

    def _create_assignments(self, employees, devices, admin_user, total=30):
        today = timezone.localdate()
        created_assignments = []

        for _ in range(total):
            # Stogu tukenmis cihazlar zimmetlenemeyecegi icin her turda yeniden secilir.
            available = [device for device in devices if device.available_count > 0]
            if not available:
                break
            device = random.choice(available)
            assigned_date = today - timedelta(days=random.randint(1, 400))
            created_assignments.append(
                services.assign_device(
                    employee=random.choice(employees),
                    device=device,
                    assigned_by=admin_user,
                    assigned_date=assigned_date,
                    expected_return_date=assigned_date + timedelta(days=random.choice([180, 365, 730])),
                    notes="Ornek zimmet kaydi.",
                )
            )

        # Olusturulan zimmetlerin bir kismini iade edilmis olarak isaretle; cogunlugu
        # hasarsiz, bir kismi hasarli/eksik olsun ki iade tutanagi da test edilebilsin.
        return_sample = random.sample(created_assignments, k=max(1, len(created_assignments) // 3))
        for assignment in return_sample:
            condition = random.choices(
                [
                    Assignment.ReturnCondition.UNDAMAGED,
                    Assignment.ReturnCondition.DAMAGED,
                    Assignment.ReturnCondition.MISSING,
                ],
                weights=[75, 18, 7],
            )[0]
            damaged = condition != Assignment.ReturnCondition.UNDAMAGED
            services.return_device(
                assignment=assignment,
                returned_by=admin_user,
                return_notes="Ornek iade kaydi.",
                return_condition=condition,
                damage_description=fake.sentence(nb_words=8) if damaged else "",
            )
