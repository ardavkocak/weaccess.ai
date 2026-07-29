"""
Dosyalardan veri cikaran parser fonksiyonlari — aylik-takip/parser.js'in
Python portu.

ONEMLI RISK NOTU: PDF koordinat tabanli cikarma (pdf_personel_cikar) ve OCR
tabanli izin okuma (gorsel_ocr + izin_kayitlari_cikar) cok spesifik bir
belge sablonuna (Nevisoft/ATAP "Muafiyet Raporu") ve OCR ciktisina
dayanir. Bu port, orijinal JS algoritmasini (koordinat pencereleri,
regex'ler) BIREBIR takip eder, ancak GERCEK ORNEK DOSYALARLA test
EDILEMEMISTIR (repoda ornek PDF/gorsel yok). Uretime almadan once gercek
belgelerle dogrulanmalidir.

Kutuphane karsiliklari:
  pdfjs-dist (coordinate)  -> pdfplumber (extract_words, ayni PDF nokta
                               uzayinda x0/x1; "top" pdfjs'in y'sinin
                               tersine ust-alt yonlu calisir)
  mammoth (docx duz metin) -> python-docx (paragraf birlestirme, yaklasik)
  tesseract.js (OCR)       -> pytesseract + Pillow (sistemde tesseract
                               ikili dosyasi ve 'tur' dil verisi gerekir)
"""
from __future__ import annotations

import re
from datetime import date, timedelta

from .hesaplama import GUNLUK_SAAT

AD_GURULTU = re.compile(
    r"^(Evet|Hayır|Gönderilmedi|Reddedildi|Onaylandı|Araştırmacı|Destek|İşlemler|Proje|Ar-?Ge)\b|-\s*20\d{2}|Personel|Toplam|Süre",
    re.IGNORECASE,
)


def sayiya(s) -> float:
    if s is None:
        return 0.0
    try:
        return float(str(s).replace(".", "").replace(",", "."))
    except ValueError:
        return 0.0


def pdf_personel_cikar(file_obj):
    """
    Muafiyet Raporu PDF'inden personel listesini koordinat bazli cikarir.

    Sutunlar (PDF nokta uzayinda, sayfa solundan itibaren x):
      x~47  Sira No · x~70 TC Kimlik No (11 hane) · x~107 Adi Soyadi
      x~576 Bolgede Bulunma Suresi · x~628 Muafiyet Saati · x~762 Toplam Sure
    """
    import pdfplumber

    personeller = []
    with pdfplumber.open(file_obj) as pdf:
        for page in pdf.pages:
            words = page.extract_words(use_text_flow=False, keep_blank_chars=False)
            items = [{"s": w["text"].strip(), "x": w["x0"], "top": w["top"]} for w in words if w["text"].strip()]

            tc_tokenlar = [i for i in items if 60 <= i["x"] <= 95 and re.fullmatch(r"\d{11}", i["s"])]

            for tc_t in tc_tokenlar:
                sira_tok = next(
                    (i for i in items if 38 <= i["x"] <= 60 and re.fullmatch(r"\d{1,3}", i["s"]) and abs(i["top"] - tc_t["top"]) < 6),
                    None,
                )
                if not sira_tok:
                    continue

                isim_adaylari = [
                    i for i in items
                    if 100 <= i["x"] <= 132
                    and re.search(r"[A-Za-zÇĞİÖŞÜçğıöşü]", i["s"])
                    and not AD_GURULTU.search(i["s"])
                    and tc_t["top"] - 12 <= i["top"] <= tc_t["top"] + 3
                ]

                def en_yakin_tc(item):
                    return min(tc_tokenlar, key=lambda t: abs(t["top"] - item["top"]))

                isim_tok = sorted(
                    (i for i in isim_adaylari if en_yakin_tc(i) is tc_t),
                    key=lambda i: (i["top"], i["x"]),
                )

                def sutun_saat(x_min, x_max):
                    tok = [i for i in items if x_min <= i["x"] <= x_max and re.fullmatch(r"[\d.,]+", i["s"]) and abs(i["top"] - tc_t["top"]) < 6]
                    return sayiya(tok[-1]["s"]) if tok else 0

                bolgede_saat = sutun_saat(560, 600)
                muafiyet_saat = sutun_saat(612, 652)
                toplam_saat = sutun_saat(745, 795)
                toplam_tok_var = any(
                    745 <= i["x"] <= 795 and re.fullmatch(r"[\d.,]+", i["s"]) and abs(i["top"] - tc_t["top"]) < 6
                    for i in items
                )

                if not isim_tok or not toplam_tok_var:
                    continue

                isim = re.sub(r"\s+", " ", " ".join(t["s"] for t in isim_tok)).strip()

                personeller.append({
                    "sira": int(sira_tok["s"]), "tc": tc_t["s"], "isim": isim,
                    "toplam_saat": toplam_saat, "bolgede_saat": bolgede_saat, "muafiyet_saat": muafiyet_saat,
                })

    personeller.sort(key=lambda p: p["sira"])
    return personeller


def word_personel_cikar(file_obj):
    """Word (.docx) yedek yolu: ham metinden 'Ad Soyad ... 108,85' satirlarini dener."""
    from docx import Document

    doc = Document(file_obj)
    personeller = []
    isim_pattern = re.compile(r"([A-ZÇĞİÖŞÜ][a-zçğıöşü]+(?:\s+[A-ZÇĞİÖŞÜ][A-Za-zÇĞİÖŞÜçğıöşü]+)+)")
    sayi_pattern = re.compile(r"\d+(?:,\d+)?")

    for para in doc.paragraphs:
        satir = para.text
        isim_m = isim_pattern.search(satir)
        sayilar = sayi_pattern.findall(satir)
        if isim_m and sayilar:
            personeller.append({"isim": isim_m.group(1).strip(), "toplam_saat": sayiya(sayilar[-1])})
    return personeller


def gorsel_ocr(file_obj) -> str:
    """Gorselden OCR ile ham metin okur (Turkce + Ingilizce). Tesseract binary gerektirir."""
    import pytesseract
    from PIL import Image

    image = Image.open(file_obj)
    return pytesseract.image_to_string(image, lang="tur+eng") or ""


def tarih_parse(s: str):
    m = re.search(r"(\d{1,2})[./-](\d{1,2})[./-](\d{4})", s)
    if not m:
        return None
    try:
        return date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
    except ValueError:
        return None


def iso_tarih(d: date) -> str:
    return d.isoformat()


def aralik_is_gunu(bas: date, bit: date, resmi_set=None) -> int:
    g = 0
    d = bas
    while d < bit:
        hafta_ici = d.weekday() < 5
        resmi_mi = resmi_set is not None and iso_tarih(d) in resmi_set
        if hafta_ici and not resmi_mi:
            g += 1
        d += timedelta(days=1)
    return g


_YARIM_GUN_PATTERN = re.compile(r"yar[ıi]m\s*g[üu]n", re.IGNORECASE)
_SAATLIK_PATTERN = re.compile(r"(\d+(?:[.,]\d+)?)\s*saat", re.IGNORECASE)


def _is_gunu_hesapla(bas: date, bit: date, tip: str, resmi_set=None):
    """
    Bir izin kaydının GÜN karşılığını hesaplar. Öncelik sırası:
      1. Tip metninde "Yarım Gün" geçiyorsa → 0.5 gün (tarih aralığından BAĞIMSIZ,
         çünkü yarım günlük izinlerde başlangıç=bitiş aynı gün olabilir ve
         aralık hesabı 0 döner — bu, yarım/saatlik izinlerin daha önce YANLIŞ
         hesaplandığı asıl noktadır).
      2. Tip metninde "X Saat" geçiyorsa → X / GUNLUK_SAAT gün (saatlik izin).
      3. Aksi halde tam gün(ler) aralığı: aralik_is_gunu().

    @returns (is_gunu: float, hesap_tipi: 'yarim_gun'|'saatlik'|'tam_gun')
    """
    if _YARIM_GUN_PATTERN.search(tip):
        return 0.5, "yarim_gun"

    saat_m = _SAATLIK_PATTERN.search(tip)
    if saat_m:
        saat_degeri = sayiya(saat_m.group(1))
        return round(saat_degeri / GUNLUK_SAAT, 2), "saatlik"

    return aralik_is_gunu(bas, bit, resmi_set), "tam_gun"


def izin_kayitlari_cikar(metin: str, resmi_set=None):
    satirlar = [s for s in metin.splitlines() if s.strip()]
    kayitlar = []
    # Aynı izin kaydı (aynı kişi + aynı tarih aralığı) OCR metninde birden
    # fazla kez geçebilir (görsel iki kez taranmış, özet satırı tekrar etmiş
    # vb.) — bu durumda izin İKİ KEZ SAYILMASIN diye görülen kayıtlar burada
    # izlenir.
    gorulen = set()
    tarih_pattern = re.compile(r"\d{1,2}[./-]\d{1,2}[./-]\d{4}")

    for satir in satirlar:
        tarihler = tarih_pattern.findall(satir)
        if len(tarihler) < 3:
            continue

        bitis_str = tarihler[-1]
        baslangic_str = tarihler[-2]
        bas = tarih_parse(baslangic_str)
        bit = tarih_parse(bitis_str)
        if not bas or not bit:
            continue

        izin_idx = satir.find(baslangic_str)
        on_bolum = satir[:izin_idx] if izin_idx >= 0 else satir
        kelimeler = [
            w for w in on_bolum.split()
            if re.fullmatch(r"[A-Za-zÇĞİÖŞÜçğıöşü]{2,}", w) and not re.search(r"gmail|hotmail|outlook|com|nevisoft", w, re.IGNORECASE)
        ]
        isim = re.sub(r"\s+", " ", " ".join(kelimeler[-3:])).strip()

        sonrasi = satir[satir.rfind(bitis_str) + len(bitis_str):]
        tip = re.sub(r"\s+", " ", re.sub(r"[Nn]evisoft", "", sonrasi)).strip()

        # Mükerrer kayıt kontrolü: aynı isim (ASCII/lower normalize) + aynı
        # başlangıç/bitiş tarihi ikinci kez görülürse atlanır.
        anahtar = (asciiye(isim).lower(), baslangic_str, bitis_str)
        if anahtar in gorulen:
            continue
        gorulen.add(anahtar)

        is_gunu, hesap_tipi = _is_gunu_hesapla(bas, bit, tip, resmi_set)

        kayitlar.append({
            "isim": isim, "baslangic": baslangic_str, "bitis": bitis_str,
            "is_gunu": is_gunu, "hesap_tipi": hesap_tipi, "tip": tip or "İzin",
        })

    return kayitlar


_TR_ASCII_MAP = str.maketrans({"ş": "s", "Ş": "s", "ç": "c", "Ç": "c", "ğ": "g", "Ğ": "g", "ö": "o", "Ö": "o", "ü": "u", "Ü": "u", "ı": "i", "İ": "i"})


def asciiye(s: str) -> str:
    return str(s).translate(_TR_ASCII_MAP)


def _isim_tokenlari(s):
    s = asciiye(str(s).lower())
    s = re.sub(r"[^a-z\s]", " ", s)
    return sorted(t for t in s.split() if t)


def isim_eslesir(a: str, b: str) -> bool:
    """
    İki ismin aynı kişiye ait olup olmadığını GÜVENLİ biçimde karşılaştırır.

    ÖNEMLİ DÜZELTME: Eski kural, kısa (tek kelimelik) isimlerde TEK ortak
    kelime yeterli sayıyordu (`min(2, min(uzunluk))`). Bu, OCR'ın soyadını
    kaçırdığı durumlarda ("Ahmet" gibi yaygın bir ad tek başına kalırsa)
    PDF'teki YANLIŞ bir "Ahmet ..." personeliyle eşleşmesine yol açabiliyordu
    — yani izin görselindeki bilgiler PDF'teki YANLIŞ kişiye eşleşebiliyordu.
    Artık: HER İKİ isim de en az 2 kelimeden oluşmuyorsa (soyad OCR'da
    kaybolmuşsa) otomatik EŞLEŞTİRME YAPILMAZ — bu kayıt "eşleşmeyen izinler"
    listesine düşer ve admin'e açıkça gösterilir; sessizce yanlış kişiye
    yazılmaz.
    """
    ta, tb = _isim_tokenlari(a), _isim_tokenlari(b)
    if not ta or not tb:
        return False

    # Her iki taraf da tek kelimeyse (örn. ikisi de yalnızca "Ahmet" olarak
    # okunmuşsa) birebir aynı olmaları şartıyla eşleşir — bu son derece dar
    # bir durumdur ve yanlış pozitif riski taşımaz.
    if len(ta) == 1 and len(tb) == 1:
        return ta == tb

    # Aksi halde GÜVENİLİR eşleşme için her iki isimde de en az 2 kelime VE
    # en az 2 ortak kelime aranır. Taraflardan biri tek kelimeyse (soyad
    # eksikse) kasıtlı olarak eşleştirilmez — belirsiz durumda sessizce
    # yanlış eşleştirmektense hiç eşleştirmemek tercih edilir.
    if len(ta) < 2 or len(tb) < 2:
        return False

    ortak = [t for t in ta if t in tb]
    return len(ortak) >= 2
