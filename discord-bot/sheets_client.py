"""
Google Sheets'ten "Sales Pipeline" tablosunu okuyup her satır için
kararlı bir benzersiz anahtar (row_key) üreten katman.

Aynı firma adı birden fazla kez geçebildiği için (örn. görseldeki Valeo, ESBAŞ
gibi hem kamera hem araç teklifi olan firmalar), satırı tek başına "Firma"
alanıyla değil; Firma + Teklif Tarihi + Kamera Sayısı + Araç Sayısı
kombinasyonuyla ayırt ediyoruz. Bu da aynı kalırsa satır "aynı fırsat" sayılır.
"""
import gspread
from google.oauth2.service_account import Credentials

import config

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

_client = None


def _get_client():
    global _client
    if _client is None:
        creds = Credentials.from_service_account_file(
            config.GOOGLE_SERVICE_ACCOUNT_FILE, scopes=SCOPES
        )
        _client = gspread.authorize(creds)
    return _client


def _make_row_key(row: dict) -> str:
    parts = [
        row.get(config.COL_FIRMA, "").strip(),
        row.get(config.COL_TEKLIF_TARIHI, "").strip(),
        row.get(config.COL_KAMERA, "").strip(),
        row.get(config.COL_ARAC, "").strip(),
    ]
    return "|".join(parts)


def fetch_rows(spreadsheet_id: str | None = None, worksheet_name: str | None = None) -> dict:
    """
    Sheet'i okur, her satırı row_key -> row(dict) eşlemesi olarak döner.
    Boş "Firma" hücreli satırlar atlanır (tamamen boş satırlar dahil).

    spreadsheet_id / worksheet_name verilmezse config.py'deki (.env kaynaklı)
    varsayılanlar kullanılır. Guild bazlı /ayar sheet komutuyla değiştirilen
    değerler storage.py üzerinden buraya parametre olarak geçirilir.
    """
    client = _get_client()
    sh = client.open_by_key(spreadsheet_id or config.SPREADSHEET_ID)
    ws = sh.worksheet(worksheet_name or config.WORKSHEET_NAME)
    records = ws.get_all_records()  # ilk satırı başlık kabul eder

    result = {}
    for record in records:
        firma = str(record.get(config.COL_FIRMA, "")).strip()
        if not firma:
            continue
        normalized = {col: str(record.get(col, "")).strip() for col in config.REQUIRED_COLUMNS}
        row_key = _make_row_key(normalized)
        # Aynı anahtar tekrar ederse (nadir durum) sıra numarası ekleyerek ayır
        base_key = row_key
        suffix = 2
        while row_key in result:
            row_key = f"{base_key}#{suffix}"
            suffix += 1
        result[row_key] = normalized
    return result
