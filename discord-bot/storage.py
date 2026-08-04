"""
SQLite üzerinden kalıcı depolama.

Tablolar:
- watches: kullanıcıların abone olduğu bildirim kuralları (guild'in ana sheet'i için,
  ya da source_id doluysa belirli bir kişisel sheet_sources kaydı için)
- guild_settings: sunucu bazlı varsayılan kanal / kontrol sıklığı / eskime eşiği / ana sheet
- sheet_sources: kullanıcıların kendi eklediği ek Google Sheet kaynakları (kişi başına
  birden fazla, etiketle ayırt edilir). Varsayılan olarak olaylar sahibine DM olarak gider;
  watches tablosunda source_id ile eşleşen bir kayıt varsa onun yerine kullanılır.
- row_state: bir önceki taramada tablonun satır satır görüntüsü (değişiklik tespiti için).
  Guild'in ana sheet'i için row_key olduğu gibi saklanır (geriye dönük uyumluluk);
  kişisel sheet_sources kayıtları "src:<id>:" öneki ile izole edilir, aynı satır anahtarının
  farklı kaynaklarda çakışmaması için.
"""
import sqlite3
import json
from contextlib import contextmanager
from datetime import datetime, timezone

import config

EVENT_TYPES = ["yeni_kayit", "durum_degisti", "kaybedildi", "guncelleme_yok", "hepsi"]


def _connect():
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def get_conn():
    conn = _connect()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS watches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                firma TEXT,                 -- NULL ise tüm firmalar
                event_type TEXT NOT NULL,   -- EVENT_TYPES içinden biri
                deliver_channel_id TEXT,    -- NULL ise kullanıcıya DM atılır
                source_id INTEGER,          -- NULL ise guild'in ana sheet'i, doluysa sheet_sources.id
                created_at TEXT NOT NULL
            )
        """)
        existing_watch_cols = {row["name"] for row in conn.execute("PRAGMA table_info(watches)")}
        if "source_id" not in existing_watch_cols:
            conn.execute("ALTER TABLE watches ADD COLUMN source_id INTEGER")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS guild_settings (
                guild_id TEXT PRIMARY KEY,
                default_channel_id TEXT,
                poll_minutes INTEGER NOT NULL DEFAULT %d,
                stale_days INTEGER NOT NULL DEFAULT %d,
                spreadsheet_id TEXT,
                worksheet_name TEXT
            )
        """ % (config.DEFAULT_POLL_MINUTES, config.DEFAULT_STALE_DAYS))

        # Basit migrasyon: eski bir veritabanında bu sütunlar yoksa ekle.
        existing_cols = {row["name"] for row in conn.execute("PRAGMA table_info(guild_settings)")}
        if "spreadsheet_id" not in existing_cols:
            conn.execute("ALTER TABLE guild_settings ADD COLUMN spreadsheet_id TEXT")
        if "worksheet_name" not in existing_cols:
            conn.execute("ALTER TABLE guild_settings ADD COLUMN worksheet_name TEXT")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS row_state (
                row_key TEXT PRIMARY KEY,
                data_json TEXT NOT NULL,
                last_notified_stale_at TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS event_channels (
                guild_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                channel_id TEXT NOT NULL,
                PRIMARY KEY (guild_id, event_type)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sheet_sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id TEXT NOT NULL,
                owner_user_id TEXT NOT NULL,
                label TEXT NOT NULL,
                spreadsheet_id TEXT NOT NULL,
                worksheet_name TEXT NOT NULL,
                poll_minutes INTEGER,   -- NULL ise guild_settings.poll_minutes kullanılır
                stale_days INTEGER,     -- NULL ise guild_settings.stale_days kullanılır
                created_at TEXT NOT NULL,
                UNIQUE (owner_user_id, label)
            )
        """)


# ---------- watches ----------

def add_watch(guild_id: str, user_id: str, firma: str | None, event_type: str,
              deliver_channel_id: str | None, source_id: int | None = None):
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO watches (guild_id, user_id, firma, event_type, deliver_channel_id, source_id, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (guild_id, user_id, firma, event_type, deliver_channel_id, source_id,
             datetime.now(timezone.utc).isoformat()),
        )
        return cur.lastrowid


def remove_watch(watch_id: int, user_id: str) -> bool:
    with get_conn() as conn:
        cur = conn.execute(
            "DELETE FROM watches WHERE id = ? AND user_id = ?", (watch_id, user_id)
        )
        return cur.rowcount > 0


def delete_watches_for_user(guild_id: str, user_id: str) -> int:
    """Kullanıcının o guild'deki tüm aboneliklerini siler (ana sheet + kişisel kaynak)."""
    with get_conn() as conn:
        cur = conn.execute(
            "DELETE FROM watches WHERE guild_id = ? AND user_id = ?", (guild_id, user_id)
        )
        return cur.rowcount


def list_watches_for_user(guild_id: str, user_id: str):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM watches WHERE guild_id = ? AND user_id = ? ORDER BY id",
            (guild_id, user_id),
        ).fetchall()
        return [dict(r) for r in rows]


def list_watches_for_guild(guild_id: str):
    """Guild'in ANA sheet'i için abonelikler (kişisel sheet_sources'a bağlı olanlar hariç)."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM watches WHERE guild_id = ? AND source_id IS NULL", (guild_id,)
        ).fetchall()
        return [dict(r) for r in rows]


def list_watches_for_source(source_id: int):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM watches WHERE source_id = ?", (source_id,)
        ).fetchall()
        return [dict(r) for r in rows]


# ---------- guild settings ----------

def get_guild_settings(guild_id: str) -> dict:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM guild_settings WHERE guild_id = ?", (guild_id,)
        ).fetchone()
        if row:
            return dict(row)
        conn.execute(
            "INSERT INTO guild_settings (guild_id, poll_minutes, stale_days) VALUES (?, ?, ?)",
            (guild_id, config.DEFAULT_POLL_MINUTES, config.DEFAULT_STALE_DAYS),
        )
        return {
            "guild_id": guild_id,
            "default_channel_id": None,
            "poll_minutes": config.DEFAULT_POLL_MINUTES,
            "stale_days": config.DEFAULT_STALE_DAYS,
        }


def set_default_channel(guild_id: str, channel_id: str):
    get_guild_settings(guild_id)  # satırın var olduğundan emin ol
    with get_conn() as conn:
        conn.execute(
            "UPDATE guild_settings SET default_channel_id = ? WHERE guild_id = ?",
            (channel_id, guild_id),
        )


def set_poll_minutes(guild_id: str, minutes: int):
    get_guild_settings(guild_id)
    with get_conn() as conn:
        conn.execute(
            "UPDATE guild_settings SET poll_minutes = ? WHERE guild_id = ?",
            (minutes, guild_id),
        )


def set_stale_days(guild_id: str, days: int):
    get_guild_settings(guild_id)
    with get_conn() as conn:
        conn.execute(
            "UPDATE guild_settings SET stale_days = ? WHERE guild_id = ?",
            (days, guild_id),
        )


def set_sheet_source(guild_id: str, spreadsheet_id: str, worksheet_name: str):
    get_guild_settings(guild_id)
    with get_conn() as conn:
        conn.execute(
            "UPDATE guild_settings SET spreadsheet_id = ?, worksheet_name = ? WHERE guild_id = ?",
            (spreadsheet_id, worksheet_name, guild_id),
        )


def all_guild_ids_with_settings():
    with get_conn() as conn:
        rows = conn.execute("SELECT guild_id FROM guild_settings").fetchall()
        return [r["guild_id"] for r in rows]


# ---------- event_channels (olay türü -> sunucu geneli varsayılan kanal) ----------

def set_event_channel(guild_id: str, event_type: str, channel_id: str):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO event_channels (guild_id, event_type, channel_id) VALUES (?, ?, ?) "
            "ON CONFLICT(guild_id, event_type) DO UPDATE SET channel_id = excluded.channel_id",
            (guild_id, event_type, channel_id),
        )


def get_event_channels(guild_id: str) -> dict:
    """event_type -> channel_id eşlemesi döner."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT event_type, channel_id FROM event_channels WHERE guild_id = ?", (guild_id,)
        ).fetchall()
        return {r["event_type"]: r["channel_id"] for r in rows}


# ---------- row_state (değişiklik tespiti için önbellek) ----------
#
# Guild'in ana sheet'i için row_key'ler öneksiz saklanır (geriye dönük uyumluluk).
# Kişisel sheet_sources kayıtları "src:<source_id>:" öneki ile izole edilir ki aynı
# satır anahtarı farklı kaynaklarda çakışmasın. Bu yüzden aşağıdaki "ana sheet"
# fonksiyonları "src:" ile başlayan satırları hariç tutar.

_SOURCE_PREFIX = "src:"


def get_all_row_states() -> dict:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT row_key, data_json FROM row_state WHERE row_key NOT LIKE 'src:%'"
        ).fetchall()
        return {r["row_key"]: json.loads(r["data_json"]) for r in rows}


def upsert_row_state(row_key: str, data: dict):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO row_state (row_key, data_json) VALUES (?, ?) "
            "ON CONFLICT(row_key) DO UPDATE SET data_json = excluded.data_json",
            (row_key, json.dumps(data, ensure_ascii=False)),
        )


def delete_row_states_not_in(valid_keys: list[str]):
    if not valid_keys:
        return
    with get_conn() as conn:
        placeholders = ",".join("?" for _ in valid_keys)
        conn.execute(
            f"DELETE FROM row_state WHERE row_key NOT LIKE 'src:%' AND row_key NOT IN ({placeholders})",
            valid_keys,
        )


def mark_stale_notified(row_key: str):
    with get_conn() as conn:
        conn.execute(
            "UPDATE row_state SET last_notified_stale_at = ? WHERE row_key = ?",
            (datetime.now(timezone.utc).isoformat(), row_key),
        )


def get_stale_notified_at(row_key: str) -> str | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT last_notified_stale_at FROM row_state WHERE row_key = ?", (row_key,)
        ).fetchone()
        return row["last_notified_stale_at"] if row else None


# ---------- sheet_sources (kullanıcıların kendi ekledikleri kişisel Google Sheet'leri) ----------

def add_sheet_source(guild_id: str, owner_user_id: str, label: str, spreadsheet_id: str,
                      worksheet_name: str, poll_minutes: int | None = None,
                      stale_days: int | None = None) -> int:
    """
    Aynı kullanıcı aynı etiketle tekrar eklerse (güncelleme amacıyla) var olan
    kaydın üzerine yazar; id değişmez, ilgili poll döngüsü çağıran taraf
    (Notifications cog) tarafından yeniden başlatılmalıdır.
    """
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO sheet_sources
                (guild_id, owner_user_id, label, spreadsheet_id, worksheet_name,
                 poll_minutes, stale_days, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(owner_user_id, label) DO UPDATE SET
                guild_id = excluded.guild_id,
                spreadsheet_id = excluded.spreadsheet_id,
                worksheet_name = excluded.worksheet_name,
                -- dakika/eskime_gun belirtilmezse (NULL), önceki özel değeri korur.
                poll_minutes = COALESCE(excluded.poll_minutes, sheet_sources.poll_minutes),
                stale_days = COALESCE(excluded.stale_days, sheet_sources.stale_days)
            """,
            (guild_id, owner_user_id, label, spreadsheet_id, worksheet_name,
             poll_minutes, stale_days, datetime.now(timezone.utc).isoformat()),
        )
        # ON CONFLICT DO UPDATE durumunda cur.lastrowid güvenilir değildir (SQLite bunu
        # yalnızca gerçek INSERT'lerde günceller), bu yüzden id'yi ayrıca sorguluyoruz.
        row = conn.execute(
            "SELECT id FROM sheet_sources WHERE owner_user_id = ? AND label = ?",
            (owner_user_id, label),
        ).fetchone()
        return row["id"]


def get_sheet_source(source_id: int) -> dict | None:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM sheet_sources WHERE id = ?", (source_id,)).fetchone()
        return dict(row) if row else None


def get_sheet_source_by_label(guild_id: str, owner_user_id: str, label: str) -> dict | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM sheet_sources WHERE guild_id = ? AND owner_user_id = ? AND label = ?",
            (guild_id, owner_user_id, label),
        ).fetchone()
        return dict(row) if row else None


def list_sheet_sources_for_user(guild_id: str, owner_user_id: str) -> list:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM sheet_sources WHERE guild_id = ? AND owner_user_id = ? ORDER BY label",
            (guild_id, owner_user_id),
        ).fetchall()
        return [dict(r) for r in rows]


def all_sheet_sources() -> list:
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM sheet_sources").fetchall()
        return [dict(r) for r in rows]


def delete_sheet_source(source_id: int, owner_user_id: str) -> bool:
    """Sadece sahibi silebilir. Silinirse ilgili watches ve row_state kayıtları da temizlenir."""
    with get_conn() as conn:
        cur = conn.execute(
            "DELETE FROM sheet_sources WHERE id = ? AND owner_user_id = ?",
            (source_id, owner_user_id),
        )
        deleted = cur.rowcount > 0
        if deleted:
            conn.execute("DELETE FROM watches WHERE source_id = ?", (source_id,))
            conn.execute(
                "DELETE FROM row_state WHERE row_key LIKE ?", (f"{_SOURCE_PREFIX}{source_id}:%",)
            )
        return deleted


# ---------- source row_state (kişisel sheet_sources için izole değişiklik önbelleği) ----------

def _source_key(source_id: int, row_key: str) -> str:
    return f"{_SOURCE_PREFIX}{source_id}:{row_key}"


def get_source_row_states(source_id: int) -> dict:
    prefix = f"{_SOURCE_PREFIX}{source_id}:"
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT row_key, data_json FROM row_state WHERE row_key LIKE ?", (f"{prefix}%",)
        ).fetchall()
        return {r["row_key"][len(prefix):]: json.loads(r["data_json"]) for r in rows}


def upsert_source_row_state(source_id: int, row_key: str, data: dict):
    upsert_row_state(_source_key(source_id, row_key), data)


def delete_source_row_states_not_in(source_id: int, valid_keys: list[str]):
    prefix = f"{_SOURCE_PREFIX}{source_id}:"
    with get_conn() as conn:
        existing = conn.execute(
            "SELECT row_key FROM row_state WHERE row_key LIKE ?", (f"{prefix}%",)
        ).fetchall()
        valid_composite = {_source_key(source_id, k) for k in valid_keys}
        to_delete = [r["row_key"] for r in existing if r["row_key"] not in valid_composite]
        if to_delete:
            placeholders = ",".join("?" for _ in to_delete)
            conn.execute(f"DELETE FROM row_state WHERE row_key IN ({placeholders})", to_delete)


def mark_source_stale_notified(source_id: int, row_key: str):
    mark_stale_notified(_source_key(source_id, row_key))


def get_source_stale_notified_at(source_id: int, row_key: str) -> str | None:
    return get_stale_notified_at(_source_key(source_id, row_key))
