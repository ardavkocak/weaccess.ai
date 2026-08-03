"""
discord-bot container'ını Docker socket üzerinden (docker.sock bind-mount)
kontrol eden katman.

DİKKAT: office-portal container'ına /var/run/docker.sock bağlandığı için bu
modül, host'taki TÜM Docker container'larını (yalnızca discord-bot değil)
kontrol edebilecek yetkiye sahiptir. Bu bilinçli bir tasarım kararıdır
(bkz. proje notları) — yalnızca Yönetici rolündeki kullanıcılar bu modüle
erişebilir (bkz. views.py DashboardView.test_func).

Container'ı YENİDEN OLUŞTURMAK (rebuild_and_recreate) için host'un gördüğü
mutlak yola ihtiyaç var (DISCORD_BOT_HOST_PATH ortam değişkeni,
docker-compose.override.yml'de tanımlı) — bu container'ın kendi /discord-bot-src
görüntüsü değil, host daemon'ın volume bind için anlayacağı gerçek yol.
"""
from __future__ import annotations

import os

import docker
from docker.errors import DockerException, NotFound

CONTAINER_NAME = "c_satis-pipeline-bot_app"
IMAGE_TAG = "satis-pipeline-bot:latest"

# office-portal container'ı içindeki bind-mount noktası (docker-compose.yml:
# ../discord-bot:/discord-bot-src). .env/credentials.json buraya yazılır ve
# build context olarak buradan okunur.
SRC_PATH = "/discord-bot-src"

ENV_TEMPLATE = """DISCORD_TOKEN={discord_token}
SPREADSHEET_ID={spreadsheet_id}
WORKSHEET_NAME={worksheet_name}
GOOGLE_SERVICE_ACCOUNT_FILE=credentials.json
DB_PATH=data/bot.db
DEFAULT_POLL_MINUTES={poll_minutes}
DEFAULT_STALE_DAYS={stale_days}
TEST_GUILD_ID=
"""


def _client():
    return docker.from_env()


def get_status() -> tuple[str, str | None]:
    """('running'|'exited'|...|'not_found'|'error', detay) döner."""
    try:
        container = _client().containers.get(CONTAINER_NAME)
        return container.status, None
    except NotFound:
        return "not_found", None
    except DockerException as exc:
        return "error", str(exc)


def start() -> None:
    """Var olan container'ı (yeniden oluşturmadan) başlatır."""
    _client().containers.get(CONTAINER_NAME).start()


def stop() -> None:
    _client().containers.get(CONTAINER_NAME).stop(timeout=10)


def write_env_files(ayar) -> None:
    """Ayarları discord-bot/.env ve credentials.json dosyalarına yazar."""
    os.makedirs(SRC_PATH, exist_ok=True)
    env_content = ENV_TEMPLATE.format(
        discord_token=ayar.discord_token,
        spreadsheet_id=ayar.spreadsheet_id,
        worksheet_name=ayar.worksheet_name or "Sales Pipeline",
        poll_minutes=ayar.poll_minutes,
        stale_days=ayar.stale_days,
    )
    with open(os.path.join(SRC_PATH, ".env"), "w", encoding="utf-8") as f:
        f.write(env_content)

    if ayar.service_account_json:
        with open(os.path.join(SRC_PATH, "credentials.json"), "w", encoding="utf-8") as f:
            f.write(ayar.service_account_json)


def rebuild_and_recreate() -> None:
    """
    /discord-bot-src'deki Dockerfile'dan imajı yeniden derler, varsa eski
    container'ı kaldırıp güncel .env/credentials.json ile yeniden oluşturup
    başlatır. Ayarlar kaydedildiğinde çağrılır (yeni token/ID'nin etkili
    olması için container'ın env'inin yenilenmesi şart — basit start()
    yetmez, çünkü env değerleri container oluşturma anında sabitlenir).
    """
    host_path = os.environ.get("DISCORD_BOT_HOST_PATH", "").strip()
    if not host_path:
        raise RuntimeError(
            "DISCORD_BOT_HOST_PATH tanımlı değil (docker-compose.override.yml). "
            "Bot container'ı yeniden oluşturulamıyor."
        )

    client = _client()

    # Build context, .env/credentials.json henüz yazılmamışken de host'tan
    # okunabilsin diye images.build() öncesi write_env_files() çağrılmış olmalı
    # (views.py bu sırayı zaten uyguluyor).
    image, _log_stream = client.images.build(path=SRC_PATH, tag=IMAGE_TAG, rm=True)

    try:
        client.containers.get(CONTAINER_NAME).remove(force=True)
    except NotFound:
        pass

    from dotenv import dotenv_values

    env_vars = dict(dotenv_values(os.path.join(SRC_PATH, ".env")))
    env_vars["DB_PATH"] = "data/bot.db"

    sep = "\\" if "\\" in host_path else "/"
    host_path = host_path.rstrip("\\/")
    data_bind = f"{host_path}{sep}data"
    creds_bind = f"{host_path}{sep}credentials.json"

    client.containers.run(
        image.tags[0] if image.tags else IMAGE_TAG,
        name=CONTAINER_NAME,
        detach=True,
        environment=env_vars,
        restart_policy={"Name": "unless-stopped"},
        volumes={
            data_bind: {"bind": "/app/data", "mode": "rw"},
            creds_bind: {"bind": "/app/credentials.json", "mode": "ro"},
        },
    )
