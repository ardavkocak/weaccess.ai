"""
Genel amacli IK PDF ayristirma orkestratoru.

Motorlari sirasiyla dener (bkz. engines.ENGINE_PIPELINE): pdfplumber tablo ->
camelot -> tabula -> PyMuPDF metin -> OCR (Tesseract). Ilk basarili motorun
sonucu kullanilir. "Basarili" = en az bir satirin Ad Soyad sutunu tanindi ve
en az bir calisan kaydi uretildi.

Hicbir calisan SESSIZCE atlanmaz: her calisan icin okunamayan her alan
`warnings` listesine tek tek yazilir (bkz. asagida `_build_records`), ayrica
her calisana bir okuma guven skoru (`confidence`) atanir.
"""
from __future__ import annotations

import logging
import re

from .confidence import compute_confidence
from .constants import HEADER_ALIASES, OUTPUT_FIELDS, WORK_MODEL_MARKERS
from .date_utils import find_all_dates, parse_single_date
from .engines import ENGINE_PIPELINE
from .row_merge import merge_wrapped_rows
from .text_utils import find_column, normalize

logger = logging.getLogger("hr.pdf_parser")

FIELD_LABELS = {
    "full_name": "Ad Soyad",
    "department": "Departman",
    "role": "Rol/Unvan",
    "hire_date": "İşe Giriş Tarihi",
    "work_model": "Çalışma Modeli",
    "birth_date": "Doğum Tarihi",
    "blood_type": "Kan Grubu",
    "allergy_info": "Alerji Bilgisi",
}

_LINE_SPLITTER = re.compile(r"\s{2,}|\t+")


def _lines_to_pseudo_table(lines: list[str]):
    """Sutun çizgisi olmayan ham metin satırlarını, 2+ boşluk/TAB ayracıyla sözde bir tabloya çevirir."""
    if not lines:
        return None, None
    rows = [_LINE_SPLITTER.split(line.strip()) for line in lines]
    return rows[0], rows[1:]


def _map_columns(headers: list[str]) -> dict[str, int]:
    return {field: find_column(headers, aliases) for field, aliases in HEADER_ALIASES.items()}


def _cell(row: list, idx: int) -> str:
    return str(row[idx]).strip() if 0 <= idx < len(row) and row[idx] else ""


def _build_records(headers: list[str], rows: list[list], engine: str):
    """
    @returns (records, warnings, missing_columns) — `records` None ise bu motorun
    çıktısı kullanılamaz demektir (isim sütunu hiç tanınamadı), pipeline bir
    sonraki motoru dener.
    """
    col = _map_columns(headers)
    name_col = col["full_name"]
    if name_col < 0:
        return None, [], []

    missing_columns = [
        FIELD_LABELS[field] for field in OUTPUT_FIELDS
        if field != "full_name" and col[field] < 0
    ]

    rows = merge_wrapped_rows(rows, name_col)

    records = []
    warnings = []
    for row in rows:
        if not any(str(c or "").strip() for c in row):
            continue
        full_name = _cell(row, name_col)
        if not full_name:
            continue

        department = _cell(row, col["department"])
        role = _cell(row, col["role"])
        blood_type = _cell(row, col["blood_type"])
        allergy_info = _cell(row, col["allergy_info"])

        hire_raw = _cell(row, col["hire_date"])
        hire_date = parse_single_date(hire_raw) if hire_raw else None
        work_model = _cell(row, col["work_model"])

        # Bazi PDF'lerde tablo hucreleri gercek sutun sinirinda degil, KARAKTER
        # bazinda kesiliyor (orn. bir onceki hucredeki "...Yöneticisi" kelimesinin
        # son 2 harfi bu hucreye tasip "si01.07.2025" olarak cikiyor). Tarih zaten
        # (?<!\d) regex'i sayesinde dogru ayiklanir; kalan bas harfleri sessizce
        # ATILMAZ, bir onceki (rol) alanina geri eklenir.
        if hire_date and hire_raw:
            leak_match = re.match(r"^([^\d]{1,6})\d", hire_raw)
            if leak_match:
                leaked_text = leak_match.group(1)
                if role and not role.endswith(leaked_text):
                    role = f"{role}{leaked_text}"
                    warnings.append(
                        f"Tarih hücresinin başında taşan metin ('{leaked_text}') rol alanına geri eklendi: {full_name}"
                    )

        if hire_raw and not hire_date and not work_model:
            norm = normalize(hire_raw)
            if any(marker in norm for marker in WORK_MODEL_MARKERS):
                work_model = hire_raw
            else:
                warnings.append(f"İşe giriş tarihi tanınamadı ('{hire_raw}'): {full_name}")
        if not hire_raw:
            warnings.append(f"İşe giriş tarihi bulunamadı: {full_name}")

        birth_raw = _cell(row, col["birth_date"])
        birth_date = parse_single_date(birth_raw) if birth_raw else None
        if not birth_raw:
            warnings.append(f"Doğum tarihi bulunamadı: {full_name}")

        # Guvenlik agi: sutun eslemesi basarisiz olup iki tarih de bulunamadiysa,
        # TUM satirda kac tarih oldugunu say. Kullanicinin kurali: iki tarih
        # varsa ilk=ise girisi, ikinci=dogum. Tek tarih varsa HANGI alan
        # oldugu belirsizdir; sessizce atanmaz, sadece belirsizlik loglanir.
        if not hire_date and not birth_date:
            all_dates = find_all_dates(" ".join(str(c) for c in row if c))
            if len(all_dates) >= 2:
                hire_date, birth_date = all_dates[0], all_dates[1]
            elif len(all_dates) == 1:
                warnings.append(
                    f"Satırda tek bir tarih bulundu, işe giriş mi doğum tarihi mi olduğu "
                    f"belirsiz olduğu için atanmadı ({all_dates[0].isoformat()}): {full_name}"
                )

        if col["blood_type"] >= 0 and not blood_type:
            warnings.append(f"Kan grubu bulunamadı: {full_name}")
        if col["allergy_info"] >= 0 and not allergy_info:
            warnings.append(f"Alerji bilgisi bulunamadı: {full_name}")
        if col["department"] >= 0 and not department:
            warnings.append(f"Departman bulunamadı: {full_name}")
        if col["role"] >= 0 and not role:
            warnings.append(f"Rol/Unvan bulunamadı: {full_name}")

        record = {
            "full_name": full_name,
            "department": department,
            "role": role,
            "hire_date": hire_date,
            "work_model": work_model,
            "birth_date": birth_date,
            "blood_type": blood_type,
            "allergy_info": allergy_info,
        }
        record["confidence"] = compute_confidence(record, engine)
        records.append(record)

    return records, warnings, missing_columns


def parse_employees(file_bytes: bytes) -> dict:
    """
    @returns {
        "employees": [{full_name, department, role, hire_date, work_model,
                       birth_date, blood_type, allergy_info, confidence}, ...],
        "warnings": [...],           # eksik/belirsiz alanlarin tam listesi
        "missing_columns": [...],    # PDF'te hic bulunamayan sutun basliklari
        "engine_used": "pdfplumber_table" | "camelot" | ... ,
        "low_confidence": [(full_name, confidence), ...],  # %80 altindakiler
    }
    Hicbir motor basarili olmazsa ValueError firlatir (sessizce bos donmez).
    """
    for engine_fn in ENGINE_PIPELINE:
        result = engine_fn(file_bytes)
        if result is None:
            continue

        if result["kind"] == "table":
            headers, rows = result["headers"], result["rows"]
        else:
            headers, rows = _lines_to_pseudo_table(result["lines"])
            if headers is None:
                continue

        engine_name = result["engine"]
        records, warnings, missing_columns = _build_records(headers, rows, engine_name)

        if not records:
            logger.info("%s motoru veri döndürdü ama 'Ad Soyad' sütunu tanınamadı, sıradaki motor deneniyor.", engine_name)
            continue

        for record in records:
            logger.info(
                "Okunan çalışan [%s, güven=%%%d]: ad=%r departman=%r rol=%r "
                "ise_girisi=%s calisma_modeli=%r dogum=%s kan=%r alerji=%r",
                engine_name, record["confidence"], record["full_name"], record["department"],
                record["role"], record["hire_date"], record["work_model"], record["birth_date"],
                record["blood_type"], record["allergy_info"],
            )
        for warning in warnings:
            logger.warning(warning)

        low_confidence = [(r["full_name"], r["confidence"]) for r in records if r["confidence"] < 80]

        logger.info(
            "PDF ayrıştırma tamamlandı: motor=%s, %d çalışan okundu, %d uyarı, %d düşük güvenli kayıt.",
            engine_name, len(records), len(warnings), len(low_confidence),
        )

        return {
            "employees": records,
            "warnings": warnings,
            "missing_columns": missing_columns,
            "engine_used": engine_name,
            "low_confidence": low_confidence,
        }

    raise ValueError(
        "PDF hiçbir motorla okunamadı (pdfplumber, camelot, tabula, PyMuPDF metin, OCR hepsi "
        "denendi). Dosyanın bozuk olmadığından ve en az bir 'Ad Soyad' benzeri sütun/etiket "
        "içerdiğinden emin olun."
    )
