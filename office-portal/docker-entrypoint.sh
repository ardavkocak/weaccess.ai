#!/usr/bin/env bash
#
# Konteyner acilis adimlari: (root olarak) docker.sock grubuna appuser'i ekle
# -> veritabanini bekle -> migrate -> collectstatic -> appuser'a devret.
# zimmet-sistemi/docker-entrypoint.sh ile ayni deseni izler; ek olarak
# discord-bot modulunun docker.sock erisimi icin appuser'in socket grubuna
# eklenmesi gerekir (bkz. Dockerfile "USER appuser YOK" notu).
set -euo pipefail

# /var/run/docker.sock bind-mount edilmisse (docker-compose.yml), host'taki
# grup ID'sini appuser'a taniyacak bir grup olustur. Socket mount edilmemisse
# (ornegin discord-bot ozelligi kullanilmiyorsa) bu adim sessizce atlanir.
if [ -S /var/run/docker.sock ]; then
    SOCK_GID="$(stat -c '%g' /var/run/docker.sock)"
    if ! getent group "${SOCK_GID}" >/dev/null 2>&1; then
        groupadd -g "${SOCK_GID}" dockerhost
    fi
    SOCK_GROUP="$(getent group "${SOCK_GID}" | cut -d: -f1)"
    usermod -aG "${SOCK_GROUP}" appuser
fi

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
gosu appuser python manage.py migrate --noinput --database=default

echo "==> Statik dosyalar toplaniyor..."
gosu appuser python manage.py collectstatic --noinput

echo "==> Uygulama baslatiliyor (appuser): $*"
exec gosu appuser "$@"
