"""
Tarih yakalama ve ayristirma.

Desteklenen formatlar: 23.09.2021 / 23/09/2021 / 23-09-2021 / 23.9.2021 /
2021-09-23 (ISO). Regex ile hem tam hucre icerigini (tablo modu) hem de bir
satirin icindeki BIRDEN FAZLA tarihi (metin-satiri modu) yakalayabilir.
"""
from __future__ import annotations

import re
from datetime import date, datetime

_DMY = re.compile(r"(?<!\d)(\d{1,2})[./-](\d{1,2})[./-](\d{4})(?!\d)")
_YMD = re.compile(r"(?<!\d)(\d{4})-(\d{1,2})-(\d{1,2})(?!\d)")


def find_all_dates(text: str) -> list[date]:
    """Bir metin (satir) icindeki TUM tarihleri, gectikleri sira ile dondurur."""
    if not text:
        return []
    matches = []
    for m in re.finditer(_DMY, text):
        d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        try:
            matches.append((m.start(), date(y, mo, d)))
        except ValueError:
            continue
    for m in re.finditer(_YMD, text):
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        try:
            matches.append((m.start(), date(y, mo, d)))
        except ValueError:
            continue
    matches.sort(key=lambda pair: pair[0])
    return [d for _, d in matches]


def parse_single_date(value) -> date | None:
    """Tek bir hucre degerini tarihe cevirir; parcalanamazsa None (silent-drop YOK, cagiran taraf loglar)."""
    if value is None:
        return None
    if isinstance(value, (date, datetime)):
        return value.date() if isinstance(value, datetime) else value
    text = str(value).strip()
    if not text:
        return None
    dates = find_all_dates(text)
    return dates[0] if dates else None


def looks_like_date_text(value) -> bool:
    return parse_single_date(value) is not None
