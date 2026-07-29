"""Aylik ozet hesaplama — aylik-takip/hesaplama.js'in birebir Python portu."""
from __future__ import annotations

import calendar

from .resmi_tatiller import ayin_resmi_tatilleri

GUNLUK_SAAT = 9


def ayin_is_gunu_sayisi(yil: int, ay: int) -> int:
    gun_sayisi = calendar.monthrange(yil, ay)[1]
    return sum(1 for g in range(1, gun_sayisi + 1) if _tarih_haftaici(yil, ay, g))


def _tarih_haftaici(yil, ay, gun):
    import datetime

    return datetime.date(yil, ay, gun).weekday() < 5  # Pazartesi=0..Cuma=4


def personel_ozet(*, isim, calisma_saat, izin_gun, is_gunu, resmi_gun):
    # izin_gun artik yarim gun/saatlik izinler yuzunden ondalikli olabilir
    # (orn. 4.5) — goruntulemede gereksiz uzun ondalik kalmasin diye yuvarlanir.
    izin_gun = round(izin_gun * 100) / 100
    izin_saat = izin_gun * GUNLUK_SAAT
    resmi_saat = resmi_gun * GUNLUK_SAAT

    calisma_gerekli_gun = max(0, is_gunu - resmi_gun)
    gerekli_saat = calisma_gerekli_gun * GUNLUK_SAAT

    fark = round((calisma_saat + izin_saat - gerekli_saat) * 100) / 100

    return {
        "isim": isim,
        "calisma_saat": round(calisma_saat * 100) / 100,
        "izin_gun": izin_gun,
        "izin_saat": izin_saat,
        "resmi_gun": resmi_gun,
        "resmi_saat": resmi_saat,
        "calisma_gerekli_gun": calisma_gerekli_gun,
        "gerekli_saat": round(gerekli_saat * 100) / 100,
        "fark": fark,
        "durum": "tam" if abs(fark) < 0.01 else ("fazla" if fark > 0 else "eksik"),
    }


def aylik_ozet(*, personeller, izinler, isim_eslesir, yil, ay):
    is_gunu = ayin_is_gunu_sayisi(yil, ay)
    resmi_tatiller = ayin_resmi_tatilleri(yil, ay)
    resmi_hafta_ici = [t for t in resmi_tatiller if t["hafta_ici"]]
    resmi_gun = len(resmi_hafta_ici)

    satirlar = []
    for per in personeller:
        kendi_izinleri = [iz for iz in izinler if isim_eslesir(per["isim"], iz["isim"])]
        izin_gun = sum(iz.get("is_gunu", 0) for iz in kendi_izinleri)
        ozet = personel_ozet(
            isim=per["isim"], calisma_saat=per["toplam_saat"],
            izin_gun=izin_gun, is_gunu=is_gunu, resmi_gun=resmi_gun,
        )
        ozet.update({
            "sira": per.get("sira"),
            "bolgede_saat": per.get("bolgede_saat"),
            "muafiyet_saat": per.get("muafiyet_saat"),
            "izin_kayitlari": kendi_izinleri,
        })
        satirlar.append(ozet)

    eslesmeyen_izinler = [
        iz for iz in izinler if not any(isim_eslesir(per["isim"], iz["isim"]) for per in personeller)
    ]

    return {
        "yil": yil, "ay": ay, "gunluk_saat": GUNLUK_SAAT,
        "ayin_is_gunu": is_gunu, "resmi_gun": resmi_gun, "resmi_saat": resmi_gun * GUNLUK_SAAT,
        "resmi_tatiller": resmi_hafta_ici, "resmi_tatiller_tum": resmi_tatiller,
        "personeller": satirlar, "eslesmeyen_izinler": eslesmeyen_izinler,
    }
