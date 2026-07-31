"""
Kimlik dogrulama testleri — sistem tamamen admin odakli.

Personel (staff) girisi tamamen kaldirildi (bkz. accounts.views.CustomLoginView):
dogru kimlik bilgileriyle bile olsa admin olmayan bir hesap ARTIK oturum
acamaz. Bu dosya eskiden "calisan icin otomatik hesap olusturma + personel
girisi" akisini test ediyordu; o ozellik tamamen kaldirildigi icin testler
de yeni davranisi (yalnizca admin girebilir) dogrulayacak sekilde yeniden
yazildi.
"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class AdminOnlyLoginTests(TestCase):
    """Sadece admin rolundeki hesaplar oturum acabilir."""

    def setUp(self):
        self.admin = User.objects.create_user(
            username="admin@test.com", email="admin@test.com",
            password="Admin.Sifre.2026", role=User.Role.ADMIN,
        )
        self.staff = User.objects.create_user(
            username="personel@test.com", email="personel@test.com",
            password="Personel.Sifre.2026", role=User.Role.STAFF,
        )

    def test_admin_giris_yapabilir(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "admin@test.com", "password": "Admin.Sifre.2026"},
            follow=True,
        )
        self.assertTrue(response.context["user"].is_authenticated)
        self.assertEqual(response.request["PATH_INFO"], reverse("dashboard:home"))

    def test_personel_doğru_sifreyle_bile_giris_yapamaz(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "personel@test.com", "password": "Personel.Sifre.2026"},
        )
        self.assertFalse(response.context["user"].is_authenticated)
        self.assertIn(
            "Bu sisteme erişim yetkiniz bulunmamaktadır.",
            response.context["form"].errors.get("__all__", []),
        )

    def test_personel_oturumu_hic_baslamaz(self):
        """form_valid super()'a hic ulasmadigi icin session da olusmamali."""
        self.client.post(
            reverse("accounts:login"),
            {"username": "personel@test.com", "password": "Personel.Sifre.2026"},
        )
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_pasif_admin_hesabi_giris_yapamaz(self):
        self.admin.is_active = False
        self.admin.save(update_fields=["is_active"])
        self.assertFalse(self.client.login(username="admin@test.com", password="Admin.Sifre.2026"))

    def test_yanlis_sifre_reddedilir(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "admin@test.com", "password": "yanlissifre"},
        )
        self.assertFalse(response.context["user"].is_authenticated)


class EmailOnlyLoginTests(TestCase):
    """Giris yalnizca e-posta ile yapilir; kullanici adiyla giris kapalidir."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="kullaniciadi", email="kisi@test.com",
            password="Sifre.2026", role=User.Role.ADMIN,
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


class AdminRequiredMixinDefenseInDepthTests(TestCase):
    """
    CustomLoginView personel girisini tamamen engelledigi icin bu senaryo
    normalde hic olusmaz; yine de AdminRequiredMixin'in ikinci bir savunma
    katmani olarak dogru calistigini (force_login ile session'i dogrudan
    kurarak) dogrular.
    """

    def setUp(self):
        self.staff = User.objects.create_user(
            username="personel@test.com", password="Sifre.2026", role=User.Role.STAFF
        )
        self.client.force_login(self.staff)

    def test_personel_admin_ekranlarina_erisemez(self):
        for url_name in ["inventory:device-list", "inventory:employee-list", "dashboard:home"]:
            with self.subTest(url=url_name):
                response = self.client.get(reverse(url_name))
                self.assertEqual(response.status_code, 302, f"{url_name} personel icin kilitli olmali.")
