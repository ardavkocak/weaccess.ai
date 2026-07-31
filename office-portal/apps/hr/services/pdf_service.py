"""
PDF'ten çalışan listesi çıkaran servis — ince bir sarmalayıcı.

Gerçek ayrıştırma mantığı artık `apps.hr.services.parsing` paketindeki
genel amaçlı, çok motorlu (pdfplumber → camelot → tabula → PyMuPDF → OCR)
pipeline'da yaşıyor (bkz. parsing/pipeline.py). Bu dosya yalnızca dosya
baytlarını okuyup pipeline'a verir ve sonucu view'ların beklediği biçime
çevirir; tek bir sabit tablo yapısına bağımlı DEĞİLDİR.
"""
from __future__ import annotations

from .parsing import parse_employees


def read_employees_from_pdf(uploaded_file) -> dict:
    """
    @returns {
        "employees": [{full_name, department, role, hire_date, work_model,
                       birth_date, blood_type, allergy_info, confidence}, ...],
        "warnings": [...],           # eksik/belirsiz her alan için ayrı satır
        "missing_columns": [...],    # PDF'te hiç bulunamayan sütun başlıkları
        "engine_used": str,          # kullanılan motorun adı
        "low_confidence": [(full_name, confidence), ...],
    }
    hire_date/birth_date `datetime.date` nesnesi ya da None olarak döner.
    """
    uploaded_file.seek(0)
    file_bytes = uploaded_file.read()
    return parse_employees(file_bytes)
