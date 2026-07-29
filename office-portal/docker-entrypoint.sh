#!/usr/bin/env bash
#
# Konteyner acilis adimlari: veritabanini bekle -> migrate -> collectstatic.
# zimmet-sistemi/docker-entrypoint.sh ile ayni deseni izler.
set -euo pipefail

DB_HOST="${DB_HOST:-db}"
DB_PORT="${DB_PORT:-5432}"
DB_USER="${DB_USER:-office_portal_user}"

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
python manage.py migrate --noinput --database=default

echo "==> Statik dosyalar toplaniyor..."
python manage.py collectstatic --noinput

echo "==> Uygulama baslatiliyor: $*"
exec "$@"
