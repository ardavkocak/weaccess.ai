'use strict';

/**
 * Ayar servisi — `settings` tablosundaki anahtar/değer çiftlerini yönetir.
 *
 * Discord token gibi hassas değerler veritabanında saklanır; arayüze gönderilirken
 * `getMaskedSettings()` ile maskelenir, böylece panelde tam token görünmez.
 */

const db = require('../database/connection');

// Panelden yönetilebilen ayarların tanımı. Yeni ayar eklemek için buraya bir
// satır eklemek yeterlidir; doğrulama ve kaydetme otomatik olarak uygulanır.
//
// NOT: Mesaj saatleri burada DEĞİL, `scheduled_messages.send_time` sütununda
// tutulur (her mesajın kendi saati var). Bkz. scheduledMessage.service.js
const SETTING_KEYS = {
  discord_bot_token: { label: 'Discord Bot Token', sensitive: true },
  discord_guild_id: { label: 'Discord Sunucu (Guild) ID', sensitive: false },
  discord_duty_channel_id: { label: 'Görev Kanalı ID', sensitive: false },
  discord_meal_channel_id: { label: 'Yemek Kanalı ID', sensitive: false },
  company_name: { label: 'Şirket Adı', sensitive: false },
};

/**
 * Kanal ayarları — tek kaynak.
 *
 * İki sistem aynı botu, farklı kanalları kullanır. Kanalı çözen her yer (bot,
 * teşhis, panel) bu tanımdan okur; kanal eklemek/yeniden adlandırmak için tek
 * bir yer değişir.
 */
const CHANNEL_KEYS = {
  duty: { settingKey: 'discord_duty_channel_id', label: 'Görev kanalı' },
  meal: { settingKey: 'discord_meal_channel_id', label: 'Yemek kanalı' },
};

/** Bir kanalın ayarlardaki ID'sini döner ('duty' | 'meal'). */
function getChannelId(channelKey) {
  const channel = CHANNEL_KEYS[channelKey];
  if (!channel) throw new Error(`Bilinmeyen kanal anahtarı: ${channelKey}`);
  return get(channel.settingKey);
}

/**
 * Arayüze HİÇBİR BİÇİMDE gönderilmeyecek anahtarlar.
 *
 * Bunlar `SETTING_KEYS`'te değildir (panelin genel formundan yazılamazlar) ama
 * `settings` tablosunda dururlar. `getMaskedSettings()` tüm tabloyu okuduğu için,
 * buraya yazılmasalar bile çıktıya sızabilirlerdi — bu liste onları tamamen
 * dışarıda bırakır. Parola hash'i maskelenmez, hiç gönderilmez.
 */
const SECRET_KEYS = new Set(['admin_password_hash']);

/** Discord "snowflake" kimlikleri 17-20 haneli sayılardır. */
const SNOWFLAKE_PATTERN = /^\d{17,20}$/;

/** Tek bir ayarı okur. */
function get(key, fallback = '') {
  const row = db.prepare('SELECT value FROM settings WHERE key = ?').get(key);
  return row ? row.value : fallback;
}

/** Tüm ayarları düz bir nesne olarak döner: { key: value }. */
function getAll() {
  const rows = db.prepare('SELECT key, value FROM settings').all();
  return Object.fromEntries(rows.map((r) => [r.key, r.value]));
}

/**
 * Arayüzde gösterilmek üzere ayarları döner; hassas alanlar maskelenir.
 * Token dolu ise son 4 karakteri gösterilir, boş ise boş string döner.
 */
function getMaskedSettings() {
  const all = getAll();
  const masked = { ...all };

  // Gizli anahtarlar maskelenmez, tamamen çıkarılır (bkz. SECRET_KEYS).
  for (const key of SECRET_KEYS) delete masked[key];

  for (const [key, meta] of Object.entries(SETTING_KEYS)) {
    if (meta.sensitive && all[key]) {
      masked[key] = `••••••••••••${all[key].slice(-4)}`;
    }
  }
  return masked;
}

/** Bir ayarın dolu olup olmadığını söyler (token'ı ifşa etmeden kontrol için). */
function isSet(key) {
  return Boolean(get(key));
}

/** Tek bir ayarı yazar. */
function set(key, value) {
  db.prepare(`
    INSERT INTO settings (key, value, updated_at)
    VALUES (?, ?, datetime('now'))
    ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at
  `).run(key, String(value ?? ''));
}

/**
 * "HH:MM" formatını doğrular (00:00 - 23:59).
 * @returns {boolean}
 */
function isValidTime(value) {
  return /^([01]\d|2[0-3]):([0-5]\d)$/.test(String(value || '').trim());
}

/**
 * Ayarları DOĞRULAR ama kaydetmez.
 *
 * Doğrulama ve kayıt bilerek ayrılmıştır: Ayarlar formu hem bu tabloyu hem
 * `scheduled_messages`'ı güncelliyor. Doğrularken kaydetseydik, saatlerden biri
 * geçersiz olduğunda şirket adı çoktan yazılmış olurdu — yani form hata verirken
 * verinin bir kısmı değişmiş olurdu (kısmi kayıt). Çağıran önce her iki bölümü
 * doğrular, ikisi de temizse kaydeder.
 *
 * Mesaj saatleri buraya DAHİL DEĞİLDİR; onlar scheduledMessage servisine aittir.
 *
 * @param {object} input Formdan gelen ham değerler.
 * @returns {{ errors: string[], data?: object }} Hata yoksa `data` kaydedilmeye hazırdır.
 */
function validateSettings(input) {
  const errors = [];
  const toSave = {};

  // --- Şirket adı ---
  const companyName = String(input.company_name ?? '').trim();
  if (!companyName) {
    errors.push('Şirket adı boş bırakılamaz.');
  } else if (companyName.length > 100) {
    errors.push('Şirket adı en fazla 100 karakter olabilir.');
  } else {
    toSave.company_name = companyName;
  }

  // --- Discord sunucu (guild) ID ---
  const guildId = String(input.discord_guild_id ?? '').trim();
  if (guildId && !SNOWFLAKE_PATTERN.test(guildId)) {
    errors.push('Discord Sunucu (Guild) ID yalnızca rakamlardan oluşmalı ve 17-20 haneli olmalıdır.');
  } else {
    toSave.discord_guild_id = guildId;
  }

  // --- Kanal ID'leri (görev ve yemek ayrı kanallar) ---
  // İkisi de aynı doğrulamadan geçer; kural tek yerde durur.
  for (const { settingKey, label } of Object.values(CHANNEL_KEYS)) {
    const channelId = String(input[settingKey] ?? '').trim();
    if (channelId && !SNOWFLAKE_PATTERN.test(channelId)) {
      errors.push(`${label} ID yalnızca rakamlardan oluşmalı ve 17-20 haneli olmalıdır.`);
    } else {
      toSave[settingKey] = channelId;
    }
  }

  // --- Discord bot token ---
  // Kullanıcı alanı boş bıraktıysa mevcut token'a dokunmayız. Bu sayede maskeli
  // değeri geri göndermek zorunda kalmadan diğer ayarlar kaydedilebilir.
  const token = String(input.discord_bot_token ?? '').trim();
  if (token) {
    toSave.discord_bot_token = token;
  }

  if (errors.length > 0) return { errors };
  return { errors: [], data: toSave };
}

/**
 * `validateSettings()` çıktısını tek işlemde kaydeder.
 * @param {object} data validateSettings'in döndürdüğü `data`.
 */
function saveSettings(data) {
  const saveAll = db.transaction((entries) => {
    for (const [key, value] of entries) set(key, value);
  });
  saveAll(Object.entries(data));
}

/** Token'ı tamamen temizler (bot bağlantısını kesmek için). */
function clearToken() {
  set('discord_bot_token', '');
}

module.exports = {
  SETTING_KEYS,
  CHANNEL_KEYS,
  getChannelId,
  get,
  getAll,
  getMaskedSettings,
  isSet,
  set,
  isValidTime,
  validateSettings,
  saveSettings,
  clearToken,
};
