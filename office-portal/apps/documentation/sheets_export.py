# -*- coding: utf-8 -*-
"""Belge listesini paylaşılan bir Google Sheets dosyasına, banka adıyla yeni
bir sekme (worksheet) açarak yazar.

Kimlik doğrulama bir Google Service Account JSON anahtarı ile yapılır.
Hedef Google Sheets dosyası, bu servis hesabının e-postasıyla
("client_email" alanı, JSON içinde) düzenleyen (Editor) olarak paylaşılmış
olmalıdır.
"""

from __future__ import annotations

import json
import re

import gspread
from google.oauth2.service_account import Credentials

from .scraper import Belge

_KAPSAMLAR = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# Gruplar bu sırayla yazılır.
GRUP_SIRASI = ["Form", "Sözleşme", "Diğer"]
GRUP_BASLIKLARI = {"Form": "Formlar", "Sözleşme": "Sözleşmeler", "Diğer": "Diğer"}

SUTUN_BASLIKLARI = ["Başlık"]

# Google Sheets sekme adları 100 karakteri geçemez ve : \ / ? * [ ] içeremez.
_GECERSIZ_SEKME_KARAKTERLERI = re.compile(r"[:\\/?*\[\]]")


def _sekme_adi_temizle(banka_adi: str) -> str:
    """Banka adını geçerli bir Google Sheets sekme adına dönüştürür."""
    temiz = _GECERSIZ_SEKME_KARAKTERLERI.sub("-", banka_adi).strip()
    return temiz[:100] or "Banka"


def _spreadsheet_id_cikar(url_veya_id: str) -> str:
    """Tam Google Sheets URL'sinden veya doğrudan ID'den spreadsheet ID'sini çıkarır."""
    eslesme = re.search(r"/spreadsheets/d/([a-zA-Z0-9_-]+)", url_veya_id)
    if eslesme:
        return eslesme.group(1)
    return url_veya_id.strip()


def istemci_olustur(servis_hesabi: str) -> gspread.Client:
    """Yetkilendirilmiş bir gspread istemcisi oluşturur.

    `servis_hesabi` iki şekilde verilebilir:
    - Bir JSON dosyasının yolu (ör. "service_account.json")
    - JSON içeriğinin kendisi, tek satır metin olarak (dosyayı Docker imajına
      dahil etmeden ortam değişkeni üzerinden aktarmak için kullanışlıdır)
    """
    metin = servis_hesabi.strip()
    if metin.startswith("{"):
        kimlik_bilgileri = Credentials.from_service_account_info(
            json.loads(metin), scopes=_KAPSAMLAR
        )
    else:
        kimlik_bilgileri = Credentials.from_service_account_file(
            metin, scopes=_KAPSAMLAR
        )
    return gspread.authorize(kimlik_bilgileri)


_HYPERLINK_FORMUL_DESENI = re.compile(r'HYPERLINK\("([^"]+)"\s*;\s*"([^"]*)"\)', re.IGNORECASE)


def _mevcut_gruplari_oku(sekme: gspread.Worksheet) -> dict[str, list[tuple[str, str]]]:
    """Sekmedeki mevcut grup bloklarını (Formlar/Sözleşmeler/Diğer) okuyup
    her grup için (başlık, url) çiftleri listesi döndürür.

    Başlık hücresi "=HYPERLINK(url; başlık)" formülü olarak durduğu için normal
    okuma (FORMATTED_VALUE) yerine formülü ayıklamak amacıyla regex kullanılır.
    """
    try:
        satirlar = sekme.get_values(value_render_option="FORMULA")
    except gspread.exceptions.APIError:
        return {}

    ters_baslik_haritasi = {v: k for k, v in GRUP_BASLIKLARI.items()}
    sonuc: dict[str, list[tuple[str, str]]] = {}
    aktif_grup: str | None = None

    for satir in satirlar:
        ilk_hucre = (satir[0] if satir else "").strip()

        if ilk_hucre in ters_baslik_haritasi:
            aktif_grup = ters_baslik_haritasi[ilk_hucre]
            sonuc.setdefault(aktif_grup, [])
            continue

        if ilk_hucre == SUTUN_BASLIKLARI[0]:
            continue  # sütun başlığı satırı, veri değil

        if aktif_grup is None or not ilk_hucre:
            continue

        eslesme = _HYPERLINK_FORMUL_DESENI.search(ilk_hucre)
        if eslesme:
            url, baslik = eslesme.group(1), eslesme.group(2)
        else:
            url, baslik = ilk_hucre, ilk_hucre
        sonuc[aktif_grup].append((baslik, url))

    return sonuc


def sheets_e_yaz(
    belgeler: list[Belge],
    spreadsheet_url_veya_id: str,
    banka_adi: str,
    servis_hesabi: str,
) -> str:
    """Belgeleri, banka adı ile adlandırılmış yeni/mevcut bir sekmeye yazar.

    `servis_hesabi`: JSON dosya yolu veya JSON içeriğinin kendisi
    (bkz. `istemci_olustur`).

    Sekme zaten varsa (ör. aynı bankanın daha önce başka bir sayfasından —
    "Sözleşmeler", "Formlar" vb. — çekilmiş verisi varsa), mevcut gruplar
    korunur: yeni gelen belgelerin kategorisiyle eşleşen grup güncellenir,
    eşleşmeyen gruplar olduğu gibi kalır. Böylece aynı bankanın farklı
    sayfalarından art arda çekim yapılabilir, önceki veri kaybolmaz.

    Döndürür: yazılan sekmenin doğrudan URL'si.
    """
    istemci = istemci_olustur(servis_hesabi)
    spreadsheet_id = _spreadsheet_id_cikar(spreadsheet_url_veya_id)
    tablo = istemci.open_by_key(spreadsheet_id)

    sekme_adi = _sekme_adi_temizle(banka_adi)
    sutun_sayisi = len(SUTUN_BASLIKLARI)

    try:
        sekme = tablo.worksheet(sekme_adi)
        mevcut_gruplar = _mevcut_gruplari_oku(sekme)
        sekme.clear()
    except gspread.WorksheetNotFound:
        sekme = tablo.add_worksheet(title=sekme_adi, rows=20, cols=sutun_sayisi)
        mevcut_gruplar = {}

    belgeler_kategoriye_gore: dict[str, list[Belge]] = {grup: [] for grup in GRUP_SIRASI}
    for belge in belgeler:
        belgeler_kategoriye_gore.setdefault(belge.kategori, []).append(belge)

    # Yeni çekilen belgelerde bulunan kategoriler mevcut grupların üzerine
    # yazılır (güncellenir); yeni çekimde hiç bulunmayan ama sekmede zaten
    # var olan kategoriler (ör. önceki sayfadan gelen Sözleşmeler) korunur.
    for grup, kayitlar in mevcut_gruplar.items():
        if belgeler_kategoriye_gore.get(grup):
            continue  # bu grup yeni veriyle güncellenecek, eskisini atla
        belgeler_kategoriye_gore[grup] = [
            Belge(baslik=baslik, url=url, tur="", kategori=grup) for baslik, url in kayitlar
        ]

    satirlar: list[list[str]] = []
    # Kalın yazılacak satır numaralarını (grup başlığı ve sütun başlığı) topla.
    grup_baslik_satirlari: list[int] = []
    sutun_baslik_satirlari: list[int] = []

    for grup in GRUP_SIRASI:
        grup_belgeleri = belgeler_kategoriye_gore.get(grup, [])
        if not grup_belgeleri:
            continue

        satirlar.append([GRUP_BASLIKLARI[grup]])
        grup_baslik_satirlari.append(len(satirlar))

        satirlar.append(list(SUTUN_BASLIKLARI))
        sutun_baslik_satirlari.append(len(satirlar))

        for belge in grup_belgeleri:
            baslik_kacisli = belge.baslik.replace('"', '""')
            baglanti_formulu = f'=HYPERLINK("{belge.url}"; "{baslik_kacisli}")'
            satirlar.append([baglanti_formulu])

        satirlar.append([""])  # gruplar arası boşluk

    if not satirlar:
        satirlar = [[""]]

    if sekme.row_count < len(satirlar):
        sekme.resize(rows=len(satirlar) + 5, cols=sutun_sayisi)

    sekme.update(
        values=satirlar, range_name="A1", value_input_option="USER_ENTERED"
    )

    for satir_no in grup_baslik_satirlari:
        sekme.format(f"A{satir_no}", {
            "textFormat": {"bold": True, "fontSize": 12, "foregroundColor": {"red": 1, "green": 1, "blue": 1}},
            "backgroundColor": {"red": 0.122, "green": 0.306, "blue": 0.471},
        })
    for satir_no in sutun_baslik_satirlari:
        sekme.format(f"A{satir_no}", {
            "textFormat": {"bold": True, "foregroundColor": {"red": 0.122, "green": 0.306, "blue": 0.471}},
            "backgroundColor": {"red": 0.851, "green": 0.886, "blue": 0.953},
        })

    return f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit#gid={sekme.id}"
