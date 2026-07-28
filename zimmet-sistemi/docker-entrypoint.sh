#!/usr/bin/env bash
#
# Konteyner acilis adimlari: veritabanini bekle -> migrate -> collectstatic.
# Bu dosya sayesinde `docker compose up` disinda manuel bir komut gerekmez.
set -euo pipefail

DB_HOST="${DB_HOST:-db}"
DB_PORT="${DB_PORT:-5432}"
DB_USER="${DB_USER:-zimmet_user}"

# compose'daki healthcheck zaten veritabani hazir olana kadar bekletir; buradaki
# dongu ikinci bir guvencedir (ornegin `docker compose up web` ile tek servis
# baslatildiginda ya da veritabani kisa sureligine yeniden baslatildiginda).
echo "==> PostgreSQL bekleniyor (${DB_HOST}:${DB_PORT})..."
for i in $(seq 1 60); do
    if pg_isready -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" >/dev/null 2>&1; then
        echo "==> PostgreSQL hazir."
        break
    fi
    if [ "${i}" -eq 60 ]; then
        echo "HATA: PostgreSQL 60 saniyede hazir olmadi (${DB_HOST}:${DB_PORT})." >&2
        exit 1
    fi
    sleep 1
done

echo "==> Veritabani migrate ediliyor..."
python manage.py migrate --noinput

# collectstatic acilista calisir, imaj insasinda DEGIL: staticfiles bir named
# volume'dur ve volume, imajdaki dizinin uzerine baglanir. Build sirasinda
# toplanan dosyalar calisma aninda volume tarafindan golgelenirdi.
echo "==> Statik dosyalar toplaniyor..."
python manage.py collectstatic --noinput

echo "==> Uygulama baslatiliyor: $*"
exec "$@"
