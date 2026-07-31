"""Her calisan kaydi icin okuma guven skoru (0-100)."""
from __future__ import annotations

from .constants import CONFIDENCE_FIELDS, ENGINE_RELIABILITY


def compute_confidence(record: dict, engine: str) -> int:
    """
    Taban skor: doldurulmus alan orani (full_name haric, o zaten zorunlu).
    work_model, hire_date bulunamayip yerine gecerli bir belirteç
    atandiginda kismi doluluk sayilir (yari puan) — tamamen bos degil ama
    tam bir tarih de degil.
    """
    filled = 0.0
    for field in CONFIDENCE_FIELDS:
        if record.get(field):
            filled += 1.0
    if not record.get("hire_date") and record.get("work_model"):
        filled += 0.5

    base = filled / len(CONFIDENCE_FIELDS)
    reliability = ENGINE_RELIABILITY.get(engine, 0.8)
    score = round(base * reliability * 100)
    return max(0, min(100, score))
