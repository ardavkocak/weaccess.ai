"""
Coklu-motor okuma katmani.

Her motor fonksiyonu ayni sozlesmeye uyar: basarili olursa
{"kind": "table"|"text", "engine": <isim>, ...} dondurur; basarisiz olursa
(kutuphane kurulu degil, veri bulunamadi, veya calisma zamani hatasi) None
dondurur ve nedeni logger'a yazar — pipeline bir sonraki motoru dener.

Tablo motorlari (pdfplumber/camelot/tabula) {"headers": [...], "rows": [[...]]}
seklinde YAPISAL veri dondurur (her sutun ayri) — en guvenilir yol, cunku
tarih/isim gibi alanlarin HANGI sutunda oldugu netlesir.

Metin motorlari (pymupdf, ocr) {"lines": [...]} seklinde HAM SATIR dondurur
— sutunlar netlesmedigi icin pipeline bunlari daha dusuk guvenle isler.
"""
from __future__ import annotations

import logging
import tempfile
from pathlib import Path

logger = logging.getLogger("hr.pdf_parser")


def _normalize_row(row) -> list[str]:
    return [str(c).strip() if c is not None else "" for c in row]


def pdfplumber_table_engine(file_bytes: bytes):
    try:
        import io

        import pdfplumber
    except ImportError as exc:
        logger.warning("pdfplumber kurulu degil: %s", exc)
        return None

    try:
        headers = None
        all_rows: list[list[str]] = []
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                for table in page.extract_tables() or []:
                    if not table:
                        continue
                    if headers is None:
                        headers = _normalize_row(table[0])
                        all_rows.extend(_normalize_row(r) for r in table[1:])
                    else:
                        first_row_norm = _normalize_row(table[0])
                        all_rows.extend(
                            _normalize_row(r) for r in (table[1:] if first_row_norm == headers else table)
                        )
        if not headers or not all_rows:
            logger.info("pdfplumber: tablo bulunamadi.")
            return None
        return {"kind": "table", "engine": "pdfplumber_table", "headers": headers, "rows": all_rows}
    except Exception as exc:  # noqa: BLE001
        logger.warning("pdfplumber tablo motoru hata verdi: %s", exc)
        return None


def _dataframe_to_table(df):
    headers = _normalize_row(list(df.columns))
    rows = [_normalize_row(row) for row in df.itertuples(index=False, name=None)]
    return headers, rows


def camelot_engine(file_bytes: bytes):
    try:
        import camelot
    except ImportError as exc:
        logger.warning("camelot kurulu degil: %s", exc)
        return None

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name

        tables = None
        for flavor in ("lattice", "stream"):
            try:
                candidate = camelot.read_pdf(tmp_path, pages="all", flavor=flavor)
            except Exception as exc:  # noqa: BLE001
                logger.info("camelot (%s) basarisiz: %s", flavor, exc)
                continue
            if candidate and len(candidate) > 0:
                tables = candidate
                break

        if not tables:
            logger.info("camelot: hicbir sayfada tablo algilanamadi.")
            return None

        headers, rows = _dataframe_to_table(tables[0].df)
        rows = rows[1:] if rows and rows[0] == headers else rows
        for table in tables[1:]:
            _, extra_rows = _dataframe_to_table(table.df)
            rows.extend(r for r in extra_rows if r != headers)

        if not headers or not rows:
            return None
        return {"kind": "table", "engine": "camelot", "headers": headers, "rows": rows}
    except Exception as exc:  # noqa: BLE001
        logger.warning("camelot motoru hata verdi: %s", exc)
        return None
    finally:
        if tmp_path:
            Path(tmp_path).unlink(missing_ok=True)


def tabula_engine(file_bytes: bytes):
    try:
        import tabula
    except ImportError as exc:
        logger.warning("tabula-py kurulu degil: %s", exc)
        return None

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name

        dataframes = tabula.read_pdf(tmp_path, pages="all", multiple_tables=True, silent=True)
        if not dataframes:
            logger.info("tabula: hicbir sayfada tablo algilanamadi.")
            return None

        headers, rows = _dataframe_to_table(dataframes[0])
        for df in dataframes[1:]:
            _, extra_rows = _dataframe_to_table(df)
            rows.extend(r for r in extra_rows if r != headers)

        if not headers or not rows:
            return None
        return {"kind": "table", "engine": "tabula", "headers": headers, "rows": rows}
    except Exception as exc:  # noqa: BLE001
        logger.warning("tabula motoru hata verdi: %s", exc)
        return None
    finally:
        if tmp_path:
            Path(tmp_path).unlink(missing_ok=True)


def pymupdf_text_engine(file_bytes: bytes):
    try:
        import fitz  # PyMuPDF
    except ImportError as exc:
        logger.warning("PyMuPDF kurulu degil: %s", exc)
        return None

    try:
        lines: list[str] = []
        with fitz.open(stream=file_bytes, filetype="pdf") as doc:
            for page in doc:
                text = page.get_text("text") or ""
                lines.extend(line for line in text.splitlines() if line.strip())
        if not lines:
            logger.info("PyMuPDF: sayfalarda metin bulunamadi (taranmis PDF olabilir).")
            return None
        return {"kind": "text", "engine": "pymupdf_text", "lines": lines}
    except Exception as exc:  # noqa: BLE001
        logger.warning("PyMuPDF motoru hata verdi: %s", exc)
        return None


def ocr_engine(file_bytes: bytes):
    try:
        import pytesseract
        from pdf2image import convert_from_bytes
    except ImportError as exc:
        logger.warning("OCR bagimliliklari (pdf2image/pytesseract) kurulu degil: %s", exc)
        return None

    try:
        images = convert_from_bytes(file_bytes)
        lines: list[str] = []
        for image in images:
            text = pytesseract.image_to_string(image, lang="tur+eng") or ""
            lines.extend(line for line in text.splitlines() if line.strip())
        if not lines:
            logger.info("OCR: sayfalardan hicbir metin cikarilamadi.")
            return None
        return {"kind": "text", "engine": "ocr", "lines": lines}
    except Exception as exc:  # noqa: BLE001
        logger.warning("OCR motoru hata verdi: %s", exc)
        return None


# Sirasiyla denenecek motorlar (kullanicinin istedigi pipeline sirasi).
ENGINE_PIPELINE = [
    pdfplumber_table_engine,
    camelot_engine,
    tabula_engine,
    pymupdf_text_engine,
    ocr_engine,
]
