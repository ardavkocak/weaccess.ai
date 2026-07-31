# Ofis Portali - uygulama imaji
#
# zimmet-sistemi/Dockerfile ile ayni desen: tek asamali, Django monolit.
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DJANGO_SETTINGS_MODULE=config.settings

WORKDIR /app

# postgresql-client: entrypoint'teki pg_isready icin.
# tesseract-ocr(-tur): apps.monthly_tracking (Aylik Takip) VE apps.hr (IK PDF
# parser OCR asamasi) pytesseract ile gorselleri okur.
# ghostscript: camelot'un tablo algilama motoru (lattice/stream) icin sart.
# default-jre-headless: tabula-py, PDFBox tabanli Java jar'ini calistirir.
# poppler-utils: pdf2image, PDF sayfalarini OCR icin gorsele cevirirken kullanir.
# libgl1: camelot'un opencv (cv2) bagimliligi bu paylasimli kutuphaneyi arar.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client tesseract-ocr tesseract-ocr-tur \
        ghostscript default-jre-headless poppler-utils libgl1 \
    && rm -rf /var/lib/apt/lists/*

COPY docker-entrypoint.sh .
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x /app/docker-entrypoint.sh \
    && useradd --create-home --shell /bin/bash --uid 1000 appuser \
    && mkdir -p /app/staticfiles /app/media \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "3", \
     "--timeout", "60", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
