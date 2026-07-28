"""Otomatik hesap olusturma ve ilk giriste sifre degistirme zorunlulugu testleri."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.inventory.models import Company, Employee
from common.utils import generate_employee_password

User = get_user_model()


class PasswordGenerationTests(TestCase):
    """Sifre kurali: calisanin adi + 123, Turkce karakterler ASCII'ye cevrilir."""

    def test_ornek_kurallar(self):
        self.assertEqual(generate_employee_password("Özge"), "ozge123")
        self.assertEqual(generate_employee_password("Ahmet"), "ahmet123")
        self.assertEqual(generate_employee_password("Mehmet"), "mehmet123")

    def test_turkce_karakterler(self):
        for ad, beklenen in [
            ("Şule", "sule123"),
            ("Çağla", "cagla123"),
            ("Gülşen", "gulsen123"),
            ("İbrahim", "ibrahim123"),
            ("Işıl", "isil123"),
            ("Ümit", "umit123"),
        ]:
            with self.subTest(ad=ad):
                self.assertEqual(generate_employee_password(ad), beklenen)

    def test_buyuk_harf_ve_bosluk(self):
        self.assertEqual(generate_employee_password("ÖZGE"), "ozge123")
        self.assertEqual(generate_employee_password("Ayşe Nur"), "aysenur123")


class EmployeeAccountCreationTests(TestCase):
    """Admin calisan ekledinde hesabin otomatik olusmasi ve calisanin giris yapabilmesi."""

    def setUp(self):
        self.company = Company.objects.create(name="Test Sirket")
        self.admin = User.objects.create_user(
            username="testadmin", password="AdminSifre.2026", role=User.Role.ADMIN
        )
        self.client.force_login(self.admin)

    def _yeni_calisan_ekle(self, first_name="Özge", email="ozge@test.com", tc="12345678901"):
        return self.client.post(
            reverse("inventory:employee-create"),
            {
                "first_name": first_name,
                "last_name": "Celik",
                "email": email,
                "tc_kimlik_no": tc,
                "hire_date": "2026-07-16",
                "company": self.company.pk,
                "is_active": "on",
            },
        )

    def test_calisan_eklenince_hesap_otomatik_olusur(self):
        response = self._yeni_calisan_ekle()
        self.assertEqual(response.status_code, 302)

        employee = Employee.objects.get(email="ozge@test.com")
        self.assertIsNotNone(employee.user, "Calisan icin otomatik hesap olusturulmali.")
        self.assertEqual(employee.user.username, "ozge@test.com")
        self.assertEqual(employee.user.role, User.Role.STAFF)
        self.assertTrue(employee.user.check_password("ozge123"))

    def test_sifre_veritabanina_hashlenerek_yazilir(self):
        """Sifre alani duz metin degil, dogrulanabilir bir hash tutmalidir."""
        self._yeni_calisan_ekle()
        user = Employee.objects.get(email="ozge@test.com").user
        self.assertNotEqual(user.password, "ozge123", "Sifre duz metin saklanmamali.")
        self.assertTrue(user.password.startswith("pbkdf2_"), "Django hash algoritmasi kullanilmali.")
        self.assertTrue(user.check_password("ozge123"))
        self.assertFalse(user.check_password("yanlis"))

    def test_calisan_uretilen_sifreyle_giris_yapabilir(self):
        self._yeni_calisan_ekle()
        self.assertTrue(self.client.login(username="ozge@test.com", password="ozge123"))

    def test_ayni_isimde_ikinci_calisan_da_ilk_denemede_giris_yapar(self):
        """Ayni ada sahip iki calisanin giris bilgileri birbirine karismamalidir."""
        self._yeni_calisan_ekle(first_name="Ahmet", email="a1@test.com", tc="11111111111")
        self._yeni_calisan_ekle(first_name="Ahmet", email="a2@test.com", tc="22222222222")

        for mail in ["a1@test.com", "a2@test.com"]:
            with self.subTest(mail=mail):
                client = self.client.__class__()
                self.assertTrue(
                    client.login(username=mail, password="ahmet123"),
                    f"{mail}: ad+123 sifresiyle giris yapilamadi.",
                )
        # Kullanici adlari e-posta oldugundan cakisma ve sayi eki olusmaz.
        adlar = set(
            Employee.objects.filter(email__in=["a1@test.com", "a2@test.com"])
            .values_list("user__username", flat=True)
        )
        self.assertEqual(adlar, {"a1@test.com", "a2@test.com"})

    def test_admin_panelinden_eklenen_calisanin_da_hesabi_olusur(self):
        """Hesap olusturma view'a degil model katmanina baglidir."""
        employee = Employee.objects.create(
            first_name="Özge", last_name="Celik", email="sinyal@test.com",
            tc_kimlik_no="44444444444", hire_date="2026-07-16", company=self.company,
        )
        employee.refresh_from_db()
        self.assertIsNotNone(employee.user, "Sinyal hesabi olusturmali.")
        self.assertTrue(employee.user.check_password("ozge123"))

    def test_mevcut_hesabi_olan_calisanin_sifresi_sifirlanmaz(self):
        """Guncelleme sinyali tekrar tetiklense de mevcut sifre korunmalidir."""
        mevcut = User.objects.create_user(
            username="mevcut", password="Eski.Sifre.2026", role=User.Role.STAFF
        )
        employee = Employee.objects.create(
            first_name="Ahmet", last_name="Var", email="var@test.com",
            tc_kimlik_no="55555555555", hire_date="2026-07-16",
            company=self.company, user=mevcut,
        )
        employee.first_name = "Ahmet Guncel"
        employee.save()
        mevcut.refresh_from_db()
        self.assertTrue(mevcut.check_password("Eski.Sifre.2026"))
        self.assertFalse(mevcut.must_change_password)

    def test_calisan_silinince_hesabi_da_silinir(self):
        """Silinen calisanin hesabi ortada kalmamalidir (e-posta cakismasi olusur)."""
        self._yeni_calisan_ekle()
        employee = Employee.objects.get(email="ozge@test.com")
        user_id = employee.user_id
        employee.delete()
        self.assertFalse(User.objects.filter(pk=user_id).exists(), "Hesap da silinmeli.")

    def test_silinen_calisan_ayni_e_postayla_yeniden_eklenebilir(self):
        """Sahipsiz hesap kalmadigi icin ayni e-posta yeniden kullanilabilir."""
        self._yeni_calisan_ekle()
        Employee.objects.get(email="ozge@test.com").delete()
        self._yeni_calisan_ekle()

        self.assertEqual(User.objects.filter(email="ozge@test.com").count(), 1,
                         "Ayni e-postaya sahip ikinci hesap olusmamali.")
        client = self.client.__class__()
        self.assertTrue(client.login(username="ozge@test.com", password="ozge123"))

    def test_personel_calisan_ekleyemez(self):
        """Hesap olusturma yetkisi yalnizca adminde kalmalidir."""
        personel = User.objects.create_user(
            username="personel", password="Sifre.2026", role=User.Role.STAFF
        )
        self.client.force_login(personel)
        response = self._yeni_calisan_ekle(email="yetkisiz@test.com", tc="33333333333")
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Employee.objects.filter(email="yetkisiz@test.com").exists())


class GercekGirisFormuAkisiTests(TestCase):
    """Uctan uca akis: admin calisan ekler -> calisan GERCEK giris formundan girer.

    Bu sinif bilerek client.login() kullanmaz; kimlik dogrulamayi dogrudan cagirmak
    giris formunu, yonlendirmeleri ve middleware zincirini atlar ve gercek hatalari
    gizler.
    """

    ORNEKLER = [
        ("Özge", "ozge123"),
        ("Ahmet", "ahmet123"),
        ("Mehmet", "mehmet123"),
        ("Şule", "sule123"),
        ("İbrahim", "ibrahim123"),
        ("Çağla", "cagla123"),
        ("Işıl", "isil123"),
    ]

    def setUp(self):
        self.company = Company.objects.create(name="Sirket")
        self.admin = User.objects.create_user(
            username="admin1", password="Admin.Sifre.2026", role=User.Role.ADMIN
        )

    def _admin_calisan_ekler(self, ad, mail, tc):
        client = self.client.__class__()
        client.force_login(self.admin)
        response = client.post(reverse("inventory:employee-create"), {
            "first_name": ad, "last_name": "Soyad", "email": mail,
            "tc_kimlik_no": tc, "hire_date": "2026-07-16",
            "company": self.company.pk, "is_active": "on",
        })
        self.assertEqual(response.status_code, 302, f"{ad} eklenemedi.")
        return Employee.objects.get(email=mail)

    def test_her_yeni_kullanici_ilk_denemede_giris_yapar(self):
        for i, (ad, sifre) in enumerate(self.ORNEKLER):
            with self.subTest(ad=ad):
                employee = self._admin_calisan_ekler(ad, f"u{i}@test.com", f"1234567890{i}")
                client = self.client.__class__()
                response = client.post(
                    reverse("accounts:login"),
                    {"username": employee.email, "password": sifre},
                    follow=True,
                )
                self.assertTrue(
                    response.context["user"].is_authenticated,
                    f"{ad}: '{sifre}' sifresiyle ILK DENEMEDE giris yapilamadi.",
                )
                # Giris basarili olduktan sonra sifre degistirme ekranina zorlanir.
                self.assertEqual(response.request["PATH_INFO"], reverse("accounts:password_change"))

    def test_yanlis_sifre_reddedilir(self):
        employee = self._admin_calisan_ekler("Özge", "ozge@test.com", "12345678901")
        client = self.client.__class__()
        response = client.post(
            reverse("accounts:login"),
            {"username": employee.email, "password": "yanlissifre"},
        )
        self.assertFalse(response.context["user"].is_authenticated)

    def test_tam_dongu_giris_sifre_degistir_normal_kullanim(self):
        employee = self._admin_calisan_ekler("Özge", "ozge@test.com", "12345678901")
        client = self.client.__class__()

        # 1) Uretilen sifreyle giris
        client.post(reverse("accounts:login"),
                    {"username": employee.email, "password": "ozge123"})
        # 2) Diger sayfalar kilitli
        self.assertRedirects(
            client.get(reverse("inventory:my-assignments")),
            reverse("accounts:password_change"),
        )
        # 3) Kendi sifresini belirler
        client.post(reverse("accounts:password_change"), {
            "old_password": "ozge123",
            "new_password1": "Guclu.Sifre.2026",
            "new_password2": "Guclu.Sifre.2026",
        })
        # 4) Artik serbest
        self.assertEqual(client.get(reverse("inventory:my-assignments")).status_code, 200)
        # 5) Cikip yeni sifresiyle tekrar girebilir
        client.post(reverse("accounts:logout"))
        response = client.post(reverse("accounts:login"),
                               {"username": employee.email, "password": "Guclu.Sifre.2026"},
                               follow=True)
        self.assertTrue(response.context["user"].is_authenticated)
        self.assertEqual(response.request["PATH_INFO"], reverse("inventory:my-assignments"))
        # 6) Eski baslangic sifresi artik gecmez
        client.post(reverse("accounts:logout"))
        response = client.post(reverse("accounts:login"),
                               {"username": employee.email, "password": "ozge123"})
        self.assertFalse(response.context["user"].is_authenticated)


class EmailOnlyLoginTests(TestCase):
    """Giris yalnizca e-posta ile yapilir; kullanici adiyla giris kapalidir."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="kullaniciadi", email="kisi@test.com",
            password="Sifre.2026", role=User.Role.STAFF,
        )

    def test_e_posta_ile_giris_yapilir(self):
        self.assertTrue(self.client.login(username="kisi@test.com", password="Sifre.2026"))

    def test_e_posta_buyuk_kucuk_harf_duyarsiz(self):
        self.assertTrue(self.client.login(username="KISI@TEST.COM", password="Sifre.2026"))

    def test_kullanici_adiyla_giris_YAPILAMAZ(self):
        self.assertFalse(
            self.client.login(username="kullaniciadi", password="Sifre.2026"),
            "Kullanici adiyla giris kapali olmali.",
        )

    def test_giris_formu_kullanici_adini_reddeder(self):
        """Form e-posta bekler; kullanici adi bicim dogrulamasina takilir."""
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "kullaniciadi", "password": "Sifre.2026"},
        )
        self.assertFalse(response.context["user"].is_authenticated)

    def test_pasif_hesap_giris_yapamaz(self):
        self.user.is_active = False
        self.user.save(update_fields=["is_active"])
        self.assertFalse(self.client.login(username="kisi@test.com", password="Sifre.2026"))



class ForcePasswordChangeTests(TestCase):
    """Otomatik sifreli hesap, kendi sifresini belirleyene kadar kilitli kalmalidir."""

    def setUp(self):
        self.company = Company.objects.create(name="Test Sirket")
        admin = User.objects.create_user(
            username="testadmin", password="AdminSifre.2026", role=User.Role.ADMIN
        )
        self.client.force_login(admin)
        self.client.post(
            reverse("inventory:employee-create"),
            {
                "first_name": "Özge",
                "last_name": "Celik",
                "email": "ozge@test.com",
                "tc_kimlik_no": "12345678901",
                "hire_date": "2026-07-16",
                "company": self.company.pk,
                "is_active": "on",
            },
        )
        self.employee = Employee.objects.get(email="ozge@test.com")

    def test_yeni_hesapta_bayrak_acik(self):
        self.assertTrue(self.employee.user.must_change_password)

    def test_sifre_degistirmeden_diger_sayfalara_erisemez(self):
        client = self.client.__class__()
        client.login(username="ozge@test.com", password="ozge123")
        response = client.get(reverse("inventory:my-assignments"))
        self.assertRedirects(response, reverse("accounts:password_change"))

    def test_sifre_degistirince_serbest_kalir(self):
        client = self.client.__class__()
        client.login(username="ozge@test.com", password="ozge123")
        client.post(
            reverse("accounts:password_change"),
            {
                "old_password": "ozge123",
                "new_password1": "Guclu.Sifre.2026",
                "new_password2": "Guclu.Sifre.2026",
            },
        )
        self.employee.user.refresh_from_db()
        self.assertFalse(self.employee.user.must_change_password)
        self.assertEqual(client.get(reverse("inventory:my-assignments")).status_code, 200)

    def test_mevcut_kullanicilar_zorlanmaz(self):
        """Bayrak varsayilan olarak kapali; guncelleme oncesi hesaplar etkilenmez.

        Kullanici adi eski yapida (ad) kalsa bile giris e-posta ile yapilir.
        """
        mevcut = User.objects.create_user(
            username="eskikullanici", email="eski@test.com",
            password="Sifre.2026", role=User.Role.STAFF,
        )
        self.assertFalse(mevcut.must_change_password)
        client = self.client.__class__()
        self.assertTrue(client.login(username="eski@test.com", password="Sifre.2026"))
        self.assertEqual(client.get(reverse("inventory:my-assignments")).status_code, 200)


class AvailableDevicesReadOnlyTests(TestCase):
    """Bostaki Cihazlar sayfasi personel icin salt okunur olmalidir."""

    def setUp(self):
        self.personel = User.objects.create_user(
            username="personel", password="Sifre.2026", role=User.Role.STAFF
        )
        self.client.force_login(self.personel)
        self.url = reverse("inventory:available-devices")

    def test_personel_goruntuleyebilir(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_yalnizca_bosta_cihazlar_listelenir(self):
        from apps.inventory.models import Assignment, Device

        bosta = Device.objects.create(name="Bosta Cihaz", total_quantity=2)
        dolu = Device.objects.create(name="Tamami Zimmette", total_quantity=1)
        company = Company.objects.create(name="Sirket")
        employee = Employee.objects.create(
            first_name="Ali", last_name="Veli", email="ali@test.com",
            tc_kimlik_no="99999999999", hire_date="2026-07-16", company=company,
        )
        Assignment.objects.create(employee=employee, device=dolu, returned=False)

        listelenen = [d.name for d in self.client.get(self.url).context_data["devices"]]
        self.assertIn(bosta.name, listelenen)
        self.assertNotIn(dolu.name, listelenen, "Tamami zimmetteki cihaz listelenmemeli.")

    def test_post_kabul_edilmez(self):
        """Sayfa salt okunurdur: hicbir degisiklik istegi kabul etmez."""
        self.assertEqual(self.client.post(self.url, {}).status_code, 405)

    def test_personel_cihaz_yonetim_ekranlarina_erisemez(self):
        for isim in ["device-list", "device-create", "assignment-create", "employee-list"]:
            with self.subTest(url=isim):
                response = self.client.get(reverse(f"inventory:{isim}"))
                self.assertEqual(response.status_code, 302, "Personel yonetim ekranina girememeli.")
