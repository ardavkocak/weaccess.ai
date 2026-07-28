# Zimmet ve Envanter Yonetim Sistemi - uygulama imaji
#
# Proje bir Django monolitidir: arayuz sunucu tarafinda render edilir, ayri bir
# frontend build adimi yoktur. Bu yuzden tek asamali sade bir imaj yeterlidir.
FROM python:3.13-slim

# PYTHONDONTWRITEBYTECODE: imaj icinde .pyc uretilmez (gereksiz katman sismesi)
# PYTHONUNBUFFERED   : log satirlari tamponlanmadan `docker compose logs`e duser
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DJANGO_SETTINGS_MODULE=config.settings

WORKDIR /app

# psycopg2-binary, Pillow ve reportlab hazir wheel ile kurulduklari icin derleme
# araci gerekmez. postgresql-client yalnizca entrypoint'teki `pg_isready` ile
# veritabaninin hazir olmasini beklemek icin kurulur.
RUN apt-get update \
    && apt-get install -y --no-install-recommends postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Bagimliliklar koddan ONCE kopyalanir: kod degistiginde pip katmani yeniden
# kurulmaz, imaj yeniden insasi ciddi olcude hizlanir.
COPY docker-entrypoint.sh .
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kod imaja kopyalanir: bind mount OLMADAN (orn. production) imaj kendi kendine
# calisir. Gelistirmede docker-compose'daki `.:/app` bind mount bu katmanin
# uzerine binerek host'taki guncel kodu kullandirir.
COPY . .

# Uygulama root olarak calismaz. UID bilerek 1000'e sabitlenir: tum host
# klasorleri (.:/app dahil staticfiles ve media) bind mount olarak baglanir ve
# Linux'ta konteynerdeki kullanicinin UID'i host'taki klasor sahibiyle
# eslesmezse migrate/collectstatic ve fotograf yukleme "permission denied"
# verir. 1000, Linux sunucularda ilk olusturulan kullanicinin standart UID'idir
# ve bu proje host'undaki `ubuntu` kullanicisiyla birebir ayni. Bu sayede
# konteynerin bind mount icinde urettigi dosyalar da host'ta root'a degil
# dogrudan `ubuntu`ya ait olur.
RUN chmod +x /app/docker-entrypoint.sh \
    && useradd --create-home --shell /bin/bash --uid 1000 appuser \
    && mkdir -p /app/staticfiles /app/media \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

# Entrypoint veritabanini bekler, migrate ve collectstatic calistirir; ardindan
# asagidaki CMD'yi exec eder. Boylece `docker compose up` disinda hicbir manuel
# adim gerekmez.
ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "3", \
     "--timeout", "60", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
