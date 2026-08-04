import os
from dotenv import load_dotenv

load_dotenv()

# Discord
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
# Doluysa slash komutları SADECE bu sunucuya anında senkronize edilir (test için).
# Boşsa global senkronizasyon yapılır (tüm sunucularda görünür ama saatler sürebilir).
TEST_GUILD_ID = os.getenv("TEST_GUILD_ID")

# Google Sheets
GOOGLE_SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "credentials.json")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
WORKSHEET_NAME = os.getenv("WORKSHEET_NAME", "Sales Pipeline")

# Depolama
DB_PATH = os.getenv("DB_PATH", "data/bot.db")

# Varsayılan davranışlar (guild bazlı /ayar komutlarıyla değiştirilebilir)
DEFAULT_POLL_MINUTES = int(os.getenv("DEFAULT_POLL_MINUTES", "30"))
DEFAULT_STALE_DAYS = int(os.getenv("DEFAULT_STALE_DAYS", "7"))

# "Eskime eşiği" için hazır süre seçenekleri (gün cinsine çevrilir).
# Hem Discord /ayar komutunda hem de web arayüzünde kullanılır.
STALE_DAYS_PRESETS = {
    "1_gun": 1,
    "1_hafta": 7,
    "1_ay": 30,
    "3_ay": 90,
    "6_ay": 180,
    "1_yil": 365,
}

# Tablodaki sütun başlıkları (görseldeki tabloyla birebir eşleşmeli)
COL_FIRMA = "Firma"
COL_KAMERA = "Kamera Sayısı"
COL_ARAC = "Araç Sayısı"
COL_TEKLIF_TARIHI = "Teklif Tarihi"
COL_SATIS_ASAMASI = "Satış Aşaması"
COL_FIRSAT_DURUMU = "Fırsat Durumu"
COL_OLASILIK = "Olasılık %"
COL_SON_GUNCELLEME = "Son Güncelleme"
COL_NOT = "Not"

REQUIRED_COLUMNS = [
    COL_FIRMA, COL_KAMERA, COL_ARAC, COL_TEKLIF_TARIHI,
    COL_SATIS_ASAMASI, COL_FIRSAT_DURUMU, COL_OLASILIK,
    COL_SON_GUNCELLEME, COL_NOT,
]
