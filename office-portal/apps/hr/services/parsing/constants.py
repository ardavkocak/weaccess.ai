"""
IK PDF parser icin sabitler: sutun basligi es anlamlilari (farkli sirketlerin
farkli isimlendirmelerine dayanikli olmak icin) ve "calisma modeli" gibi
tarih olmayan ama tarih sutununa yazilmis olabilecek belirteçler.
"""
from __future__ import annotations

# Her mantiksal alan icin bilinen tum basluk varyasyonlari (kucuk/buyuk harf
# ve Turkce karakter farklari normalize edilerek karsilastirilir; ayrica
# text_utils.fuzzy_match_header ile bulanik eslesme de denenir).
HEADER_ALIASES: dict[str, list[str]] = {
    "full_name": [
        "ad soyad", "adsoyad", "isim soyisim", "isim", "ad", "soyad", "adi",
        "personel", "personel adi", "calisan adi", "employee", "employee name",
        "name", "full name", "isim-soyisim",
    ],
    "department": [
        "departman", "department", "birim", "bolum", "sube", "ekip",
    ],
    "role": [
        "rol", "unvan", "rol / unvan", "rol/unvan", "pozisyon", "position",
        "title", "role", "job title", "gorev",
    ],
    "hire_date": [
        "ise giris tarihi", "isegiris tarihi", "ise giris", "ise baslama tarihi",
        "isebaslama tarihi", "ise baslama", "baslama tarihi", "baslangic tarihi",
        "baslangic", "hire date", "hire", "start date", "employment date",
        "employment start", "ise girdigi tarih",
    ],
    "work_model": [
        "calisma modeli", "calisma sekli", "calisma tipi", "work model",
        "work type", "employment type", "location type", "calisma duzeni",
    ],
    "birth_date": [
        "dogum tarihi", "dogumtarihi", "dogum", "birth date", "birth",
        "birthdate", "dogum gunu", "date of birth",
    ],
    "blood_type": [
        "kan grubu", "kan", "blood type", "blood group", "blood",
    ],
    "allergy_info": [
        "alerji bilgisi", "alerji", "alerjiler", "allergy", "allergies",
        "alerjik durum",
    ],
}

# Tarih sutununda gorunebilen, GERCEK bir tarih OLMAYAN ama is modeli/istihdam
# programi bilgisi tasiyan metinler. Bunlar bulundugunda hire_date=None
# birakilir, deger work_model alanina tasinir (sessizce atilmaz).
WORK_MODEL_MARKERS = [
    "iskur", "stajyer", "stajyer (iskur)", "uzaktan", "hibrit", "ofis",
    "tam zamanli", "yari zamanli", "remote", "hybrid", "onsite", "on-site",
    "part-time", "full-time", "parttime", "fulltime",
]

# Beklenen (ciktida gorunen) alan sirasi.
OUTPUT_FIELDS = [
    "full_name", "department", "role", "hire_date", "work_model",
    "birth_date", "blood_type", "allergy_info",
]

# Guven skoru hesaplanirken "doluluk" acisindan degerlendirilen alanlar
# (full_name haric — bir kaydin var olmasi icin zaten zorunlu).
CONFIDENCE_FIELDS = ["department", "role", "hire_date", "birth_date", "blood_type", "allergy_info"]

# Motor guvenilirlik carpanlari (dusuk guvenilirlikli motorlar puani asagi ceker).
ENGINE_RELIABILITY = {
    "pdfplumber_table": 1.0,
    "camelot": 0.95,
    "tabula": 0.95,
    "pymupdf_text": 0.85,
    "pdfplumber_text": 0.85,
    "ocr": 0.7,
}
