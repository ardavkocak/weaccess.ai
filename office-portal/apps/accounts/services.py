"""Calisan kayitlarindan otomatik kullanici hesabi olusturma is mantigi.

Yeni bir calisan yalnizca admin tarafindan eklenir; kayit sirasinda o calisan
icin giris yapabilecegi bir User hesabi da otomatik olusturulur. Admin sifre
belirlemez: sifre calisanin adindan turetilir (ad + 123).
"""
from django.contrib.auth import get_user_model

from common.utils import generate_employee_password


def generate_unique_username(employee):
    """Calisanin giris kullanici adini uretir: e-posta adresi.

    Kullanici adi bilerek e-postadir. Onceki surumde ad kullaniliyordu ("ahmet")
    ve ayni ada sahip ikinci calisanda sona sayi ekleniyordu ("ahmet2"); bu
    durumda kullanici adi ile sifre birbirini tutmuyordu (kullanici adi "ahmet2",
    sifre "ahmet123") ve calisan giris yapamiyordu. E-posta Employee uzerinde
    benzersiz oldugundan cakisma olusmaz ve giris bilgisi tahmin gerektirmez.

    Beklenmedik bicimde bu e-posta baska bir hesapta kullaniciadi olarak kayitliysa
    (ornegin elle acilmis bir hesap) sona sayi eklenir; boylece kayit hicbir kosulda
    IntegrityError ile dusmez.
    """
    User = get_user_model()
    base = employee.email.strip().lower()
    username = base
    counter = 2
    while User.objects.filter(username__iexact=username).exists():
        username = f"{base}.{counter}"
        counter += 1
    return username


def create_user_for_employee(employee):
    """Calisan icin otomatik kullanici hesabi olusturur ve calisana baglar.

    Sifre calisanin adindan uretilir ("Özge" -> "ozge123") ve tahmin edilebilir
    oldugu icin ilk giriste degistirilmesi zorunlu kilinir. Calisanin zaten bir
    hesabi varsa hicbir sey yapilmaz; boylece bu fonksiyon guvenle tekrar
    cagrilabilir.

    (user, raw_password) dondurur; hesap zaten varsa (None, None).
    """
    User = get_user_model()
    if employee.user_id:
        return None, None

    raw_password = generate_employee_password(employee.first_name)
    user = User(
        username=generate_unique_username(employee),
        email=employee.email,
        first_name=employee.first_name,
        last_name=employee.last_name,
        role=User.Role.STAFF,
        must_change_password=True,
    )
    # Sifre daima set_password ile yazilir: duz metin atanirsa alan hash yerine
    # sifrenin kendisini tutar ve check_password her zaman False doner.
    user.set_password(raw_password)
    user.save()

    # Calisani hesaba baglarken save() yerine update() kullanilir: bu fonksiyon
    # Employee post_save sinyalinden de cagrildigi icin save() sinyali yeniden
    # tetikler ve her yeni calisan icin gereksiz bir "guncelleme" kaydi dusurur.
    employee.user = user
    type(employee).objects.filter(pk=employee.pk).update(user=user)
    return user, raw_password
