"""E-posta adresi ile giris yapmayi saglayan kimlik dogrulama backendi."""
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

User = get_user_model()


class EmailModelBackend(ModelBackend):
    """Kullanicilarin YALNIZCA e-posta adresleriyle giris yapmasina izin verir.

    Kullanici adi ile giris bilerek desteklenmez. Otomatik olusturulan hesaplarda
    kullanici adi calisanin adindan turetiliyordu; ayni ada sahip ikinci calisanda
    sona sayi eklendigi icin ("ahmet2") kullanici adi tahmin edilemez hale geliyor
    ve calisanlar giris yapamiyordu. E-posta ise Employee uzerinde benzersizdir ve
    admin tarafindan zaten biliniyordur.

    Bu backendin tek basina yeterli olmasi icin settings.AUTHENTICATION_BACKENDS
    listesinde varsayilan ModelBackend BULUNMAMALIDIR; aksi halde kullanici adi ile
    giris o backend uzerinden yine mumkun olur. Izin/yetki sorgulari (has_perm vb.)
    ModelBackend'den miras alinir, dolayisiyla kaybolmaz.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        # AuthenticationForm alani "username" adini tasir; icerigi e-postadir.
        email = username if username is not None else kwargs.get("email")
        if email is None or password is None:
            return None

        candidates = list(User.objects.filter(email__iexact=email.strip()))
        for user in candidates:
            if user.check_password(password) and self.user_can_authenticate(user):
                return user

        if not candidates:
            # Kullanici bulunamadiginda da hash hesaplanir; aksi halde yanit
            # suresi farki, hangi e-postalarin kayitli oldugunu ele verir.
            User().set_password(password)
        return None
