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

# collectstatic acilista calisir, imaj insasinda DEGIL: staticfiles host'tan
# bind-mount edilir ve mount, imajdaki dizinin uzerine baglanir. Build
# sirasinda toplanan dosyalar calisma aninda mount tarafindan golgelenirdi.
echo "==> Statik dosyalar toplaniyor..."
if ! python manage.py collectstatic --noinput; then
    # WhiteNoise'un sikistirma adimi (CompressedStaticFilesStorage), staticfiles
    # Windows host'undan bind-mount edildiginde dosyalarin mtime'ini
    # degistiremedigi icin "Operation not permitted" ile basarisiz olabilir
    # (Docker Desktop'in Windows bind-mount'larindaki bir kisitlama). Bu durumda
    # sikistirmasiz toplama ile devam edilir; WhiteNoise gzip'i yine de calisma
    # aninda yapar, yalnizca onceden sikistirilmis .gz/.br dosyalari uretilmez.
    echo "UYARI: collectstatic sikistirmayla basarisiz oldu, --no-post-process ile tekrar deneniyor..." >&2
    python manage.py collectstatic --noinput --no-post-process
fi

echo "==> Uygulama baslatiliyor: $*"
exec "$@"
