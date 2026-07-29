"""Metin yardimcilari — ofis-gorev-takibi/src/utils/text.js'in Python portu."""
_TR_MAP = str.maketrans({
    "ı": "i", "İ": "i", "I": "i",
    "ş": "s", "Ş": "s",
    "ğ": "g", "Ğ": "g",
    "ü": "u", "Ü": "u",
    "ö": "o", "Ö": "o",
    "ç": "c", "Ç": "c",
})


def normalize_tr(value) -> str:
    """'MERCİMEK ÇORBA' -> 'mercimek corba'"""
    text = str(value or "").translate(_TR_MAP).lower()
    return " ".join(text.split())
