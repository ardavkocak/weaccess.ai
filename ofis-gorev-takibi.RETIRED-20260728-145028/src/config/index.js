'use strict';

/**
 * Uygulama yapılandırması.
 *
 * Buradaki değerler yalnızca .env dosyasından okunur ve süreç boyunca sabittir
 * (port, admin kimlik bilgileri, veritabanı yolu gibi altyapı ayarları).
 *
 * Çalışma zamanında panelden değiştirilebilen ayarlar (Discord token, kanal ID,
 * gönderim saati, şirket adı) burada DEĞİL, veritabanındaki `settings` tablosunda
 * tutulur ve `services/settings.service.js` üzerinden okunur. .env'deki karşılıkları
 * yalnızca ilk kurulumda tohum (seed) değeri olarak kullanılır.
 */

const path = require('path');
require('dotenv').config();

const rootDir = path.resolve(__dirname, '..', '..');

/** .env'den boolean okur ("true"/"1" -> true). */
function readBool(value, fallback = false) {
  if (value === undefined || value === '') return fallback;
  return value === 'true' || value === '1';
}

const config = {
  rootDir,
  env: process.env.NODE_ENV || 'development',
  port: Number(process.env.PORT) || 3000,

  // Sunucunun ve cron ifadelerinin çalışacağı saat dilimi.
  timezone: process.env.TZ || 'Europe/Istanbul',

  // SQLite dosyasının konumu. Varsayılan: <proje kökü>/data/ofis.sqlite
  databaseFile: process.env.DATABASE_FILE
    ? path.resolve(rootDir, process.env.DATABASE_FILE)
    : path.join(rootDir, 'data', 'ofis.sqlite'),

  session: {
    secret: process.env.SESSION_SECRET || 'degistirilmesi-gereken-gizli-anahtar',
    // Uygulama HTTPS arkasında çalışıyorsa .env'de SESSION_SECURE=true yapın.
    secure: readBool(process.env.SESSION_SECURE, false),
  },

  admin: {
    username: process.env.ADMIN_USERNAME || 'admin',
    password: process.env.ADMIN_PASSWORD || 'admin123',
  },

  // Yalnızca ilk kurulumda veritabanına yazılacak başlangıç değerleri.
  //
  // NOT: Saat değerleri (notify_time ve *_time) `settings` tablosuna DEĞİL,
  // `scheduled_messages.send_time` sütununa tohumlanır — her mesajın saati
  // kendi satırında durur. Buradaki değerler yalnızca ilk kurulumdaki
  // varsayılanlardır; sonrasında panelden yönetilir.
  seedSettings: {
    discord_bot_token: process.env.DISCORD_BOT_TOKEN || '',
    discord_guild_id: process.env.DISCORD_GUILD_ID || '',

    // İKİ AYRI KANAL: görev mesajları ve yemek duyuruları farklı kanallara gider.
    // Eski tek kanallı kurulumlar için `DISCORD_CHANNEL_ID` geriye dönük olarak
    // her ikisine de tohum değeri olur; panelden ayrıştırılabilir.
    discord_duty_channel_id:
      process.env.DISCORD_DUTY_CHANNEL_ID || process.env.DISCORD_CHANNEL_ID || '',
    discord_meal_channel_id:
      process.env.DISCORD_MEAL_CHANNEL_ID || process.env.DISCORD_CHANNEL_ID || '',

    company_name: process.env.COMPANY_NAME || 'Şirketiniz',

    // Aşağıdakiler `settings` tablosuna yazılmaz; seedScheduledMessages()
    // tarafından okunur. (Bkz. database/schema.js)
    notify_time: process.env.NOTIFY_TIME || '08:05',
    tea_check_1_time: process.env.TEA_CHECK_1_TIME || '10:30',
    tea_check_2_time: process.env.TEA_CHECK_2_TIME || '15:00',
    end_of_day_time: process.env.END_OF_DAY_TIME || '17:20',

    // Yemek menüsü modülü: yarının menüsünün duyurulacağı saat. `settings`
    // tablosuna `meal_notify_time` olarak tohumlanır ve Yemek Menüsü sayfasından
    // yönetilir (bkz. database/schema.js → seedMealSettings).
    meal_notify_time: process.env.MEAL_NOTIFY_TIME || '15:00',
  },
};

/**
 * `settings` tablosuna yazılacak anahtarlar.
 * Saat alanları hariç tutulur; onlar scheduled_messages'ta yaşar.
 */
const SETTINGS_SEED_KEYS = [
  'discord_bot_token',
  'discord_guild_id',
  'discord_duty_channel_id',
  'discord_meal_channel_id',
  'company_name',
];

/**
 * Kurulum hatalarını sunucu açılmadan önce yakalar.
 * Eksik/zayıf ayarları uyarı olarak bildirir, kritik olanlarda süreci durdurur.
 */
function validateConfig() {
  const warnings = [];

  if (!process.env.SESSION_SECRET) {
    warnings.push('SESSION_SECRET tanımlı değil, varsayılan değer kullanılıyor. Üretimde mutlaka ayarlayın.');
  }
  if (!process.env.ADMIN_PASSWORD) {
    warnings.push('ADMIN_PASSWORD tanımlı değil, varsayılan "admin123" kullanılıyor. Üretimde mutlaka değiştirin.');
  }
  if (config.admin.password.length < 6) {
    warnings.push('ADMIN_PASSWORD 6 karakterden kısa. Daha güçlü bir parola önerilir.');
  }

  return warnings;
}

module.exports = { config, validateConfig, SETTINGS_SEED_KEYS };
