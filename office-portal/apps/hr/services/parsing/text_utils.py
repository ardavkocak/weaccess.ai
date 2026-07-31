"""
Metin normallestirme ve bulanik (fuzzy) baslik eslestirme yardimcilari.

Farkli sirketlerin PDF'leri ayni alani onlarca farkli sekilde adlandirabilir
(Turkce karakter farklari, kisaltmalar, Ingilizce/Turkce karisimi). Bu modul
"İŞE BAŞLAMA TARİHİ" ile "Start Date"i AYNI alan olarak taniyabilmek icin
once tam/normalize eslesme, sonra alt-metin (substring) eslesme, en sonda da
bulanik (fuzzy) benzerlik denemesini sirayla uygular.
"""
from __future__ import annotations

import re

_TR_MAP = str.maketrans({
    "ç": "c", "Ç": "c", "ğ": "g", "Ğ": "g", "ı": "i", "I": "i", "İ": "i",
    "ö": "o", "Ö": "o", "ş": "s", "Ş": "s", "ü": "u", "Ü": "u",
})

try:
    from rapidfuzz import fuzz as _rf_fuzz
    _HAS_RAPIDFUZZ = True
except ImportError:  # pragma: no cover - rapidfuzz kurulu degilse difflib'e dus
    import difflib
    _HAS_RAPIDFUZZ = False


def normalize(value) -> str:
    """Kucuk harfe cevirir, Turkce karakterleri sadelestirir, bosluklari tekillestirir."""
    text = str(value or "").strip().translate(_TR_MAP).lower()
    return re.sub(r"\s+", " ", text)


def similarity(a: str, b: str) -> float:
    """0-100 arasi benzerlik orani."""
    if _HAS_RAPIDFUZZ:
        return _rf_fuzz.token_sort_ratio(a, b)
    return difflib.SequenceMatcher(None, a, b).ratio() * 100


def fuzzy_match_header(header_text: str, aliases: list[str], threshold: float = 78.0) -> bool:
    """Bir basligin, verilen alias listesinden biriyle yeterince benzer olup olmadigi."""
    norm_header = normalize(header_text)
    if not norm_header:
        return False
    for alias in aliases:
        norm_alias = normalize(alias)
        if norm_alias == norm_header or norm_alias in norm_header or norm_header in norm_alias:
            return True
        if similarity(norm_header, norm_alias) >= threshold:
            return True
    return False


def find_column(headers: list, aliases: list[str]) -> int:
    """
    Verilen basluk listesinde, alias'lardan birine (tam/alt-metin/bulanik) en iyi
    uyan sutunun index'ini dondurur. Bulunamazsa -1.
    """
    best_idx, best_score = -1, 0.0
    for i, h in enumerate(headers):
        norm_header = normalize(h)
        if not norm_header:
            continue
        for alias in aliases:
            norm_alias = normalize(alias)
            if norm_alias == norm_header:
                return i
            score = 100.0 if norm_alias in norm_header or norm_header in norm_alias else similarity(norm_header, norm_alias)
            if score > best_score:
                best_idx, best_score = i, score
    return best_idx if best_score >= 78.0 else -1
