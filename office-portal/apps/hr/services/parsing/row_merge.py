"""
Satir/hucre birlestirme.

Bazi PDF'lerde uzun bir hucre metni (orn. "Satış & İş Geliştirme Uzmanı")
tabloda IKI SATIRA bolunmus sekilde cikar:

    Satış & İş Geliştirme
    Uzmanı

Bu modul, "devam satiri" olarak tanınan (isim sutunu bos, cok az sayida
dolu hucresi olan, hicbir hucresinde tarih gecmeyen) satirlari bir onceki
GERCEK satirla birlestirir.
"""
from __future__ import annotations

from .date_utils import looks_like_date_text


def _is_continuation_row(row: list, name_col: int) -> bool:
    non_empty = [c for c in row if str(c or "").strip()]
    if not non_empty:
        return False
    name_cell = str(row[name_col]).strip() if 0 <= name_col < len(row) else ""
    if name_cell:
        return False
    if len(non_empty) > 2:
        return False
    if any(looks_like_date_text(c) for c in non_empty):
        return False
    return True


def merge_wrapped_rows(rows: list[list], name_col: int) -> list[list]:
    """Devam satirlarini bir onceki satirla birlestirip tek bir satir listesi dondurur."""
    merged: list[list] = []
    for row in rows:
        if merged and _is_continuation_row(row, name_col):
            prev = merged[-1]
            width = max(len(prev), len(row))
            prev.extend([""] * (width - len(prev)))
            for idx in range(width):
                extra = str(row[idx]).strip() if idx < len(row) and row[idx] else ""
                if not extra:
                    continue
                current = str(prev[idx]).strip() if idx < len(prev) and prev[idx] else ""
                prev[idx] = f"{current} {extra}".strip() if current else extra
            continue
        merged.append(list(row))
    return merged
