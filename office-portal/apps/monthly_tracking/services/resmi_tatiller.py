"""Turkiye resmi tatilleri — aylik-takip/resmiTatiller.js'in birebir Python portu."""
from __future__ import annotations

from datetime import date

RESMI_TATILLER = {
    2025: [
        ("2025-01-01", "Yılbaşı"),
        ("2025-03-30", "Ramazan Bayramı 1. Gün"),
        ("2025-03-31", "Ramazan Bayramı 2. Gün"),
        ("2025-04-01", "Ramazan Bayramı 3. Gün"),
        ("2025-04-23", "Ulusal Egemenlik ve Çocuk Bayramı"),
        ("2025-05-01", "Emek ve Dayanışma Günü"),
        ("2025-05-19", "Atatürkü Anma, Gençlik ve Spor Bayramı"),
        ("2025-06-06", "Kurban Bayramı 1. Gün"),
        ("2025-06-07", "Kurban Bayramı 2. Gün"),
        ("2025-06-08", "Kurban Bayramı 3. Gün"),
        ("2025-06-09", "Kurban Bayramı 4. Gün"),
        ("2025-07-15", "Demokrasi ve Milli Birlik Günü"),
        ("2025-08-30", "Zafer Bayramı"),
        ("2025-10-29", "Cumhuriyet Bayramı"),
    ],
    2026: [
        ("2026-01-01", "Yılbaşı"),
        ("2026-03-20", "Ramazan Bayramı 1. Gün"),
        ("2026-03-21", "Ramazan Bayramı 2. Gün"),
        ("2026-03-22", "Ramazan Bayramı 3. Gün"),
        ("2026-04-23", "Ulusal Egemenlik ve Çocuk Bayramı"),
        ("2026-05-01", "Emek ve Dayanışma Günü"),
        ("2026-05-19", "Atatürkü Anma, Gençlik ve Spor Bayramı"),
        ("2026-05-27", "Kurban Bayramı 1. Gün"),
        ("2026-05-28", "Kurban Bayramı 2. Gün"),
        ("2026-05-29", "Kurban Bayramı 3. Gün"),
        ("2026-05-30", "Kurban Bayramı 4. Gün"),
        ("2026-07-15", "Demokrasi ve Milli Birlik Günü"),
        ("2026-08-30", "Zafer Bayramı"),
        ("2026-10-29", "Cumhuriyet Bayramı"),
    ],
    2027: [
        ("2027-01-01", "Yılbaşı"),
        ("2027-03-09", "Ramazan Bayramı 1. Gün"),
        ("2027-03-10", "Ramazan Bayramı 2. Gün"),
        ("2027-03-11", "Ramazan Bayramı 3. Gün"),
        ("2027-04-23", "Ulusal Egemenlik ve Çocuk Bayramı"),
        ("2027-05-01", "Emek ve Dayanışma Günü"),
        ("2027-05-16", "Kurban Bayramı 1. Gün"),
        ("2027-05-17", "Kurban Bayramı 2. Gün"),
        ("2027-05-18", "Kurban Bayramı 3. Gün"),
        ("2027-05-19", "Atatürkü Anma, Gençlik ve Spor Bayramı / Kurban Bayramı 4. Gün"),
        ("2027-07-15", "Demokrasi ve Milli Birlik Günü"),
        ("2027-08-30", "Zafer Bayramı"),
        ("2027-10-29", "Cumhuriyet Bayramı"),
    ],
    2028: [
        ("2028-01-01", "Yılbaşı"),
        ("2028-02-27", "Ramazan Bayramı 1. Gün"),
        ("2028-02-28", "Ramazan Bayramı 2. Gün"),
        ("2028-02-29", "Ramazan Bayramı 3. Gün"),
        ("2028-04-23", "Ulusal Egemenlik ve Çocuk Bayramı"),
        ("2028-05-01", "Emek ve Dayanışma Günü"),
        ("2028-05-05", "Kurban Bayramı 1. Gün"),
        ("2028-05-06", "Kurban Bayramı 2. Gün"),
        ("2028-05-07", "Kurban Bayramı 3. Gün"),
        ("2028-05-08", "Kurban Bayramı 4. Gün"),
        ("2028-05-19", "Atatürkü Anma, Gençlik ve Spor Bayramı"),
        ("2028-07-15", "Demokrasi ve Milli Birlik Günü"),
        ("2028-08-30", "Zafer Bayramı"),
        ("2028-10-29", "Cumhuriyet Bayramı"),
    ],
}


def ayin_resmi_tatilleri(yil: int, ay: int):
    liste = RESMI_TATILLER.get(yil, [])
    sonuc = []
    for tarih_str, ad in liste:
        d = date.fromisoformat(tarih_str)
        if d.year == yil and d.month == ay:
            sonuc.append({"tarih": tarih_str, "ad": ad, "hafta_ici": d.weekday() < 5})
    return sonuc


def resmi_tatil_seti(*yillar):
    result = set()
    for yil in yillar:
        for tarih_str, _ in RESMI_TATILLER.get(yil, []):
            result.add(tarih_str)
    return result
