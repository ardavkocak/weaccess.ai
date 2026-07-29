'use strict';

/**
 * Zamanlanmış mesaj servisi — "ne zaman ne gönderilecek?"
 *
 * İKİ ÇEŞİT MESAJ
 * ---------------
 *   kind = 'duty'     → Görevliyi bildirir. Geçmişe kaydeder ve SIRAYI İLERLETİR.
 *                        Bir `duty_type_id` taşımak zorundadır.
 *   kind = 'reminder' → Sabit hatırlatma metni gönderir. Sıraya ve geçmişe
 *                        DOKUNMAZ. Günde kaç tane olursa olsun rotasyonu bozmaz.
 *
 * Varsayılan takvim:
 *   08:05  duty      Sabah görev bildirimi   → sırayı ilerletir
 *   10:30  reminder  Birinci çay kontrol
 *   15:00  reminder  İkinci çay kontrol
 *   17:20  reminder  Gün sonu hatırlatması
 *
 * YENİ MESAJ EKLEME
 * -----------------
 * Kod değişikliği gerekmez; tabloya satır eklemek yeterlidir. Cron açılışta ve
 * her ayar kaydında etkin satırların tümü için ayrı bir iş kurar.
 */

const db = require('../database/connection');

/** Tüm mesajlar, gönderim sırasına göre. */
function getAll() {
  return db.prepare(`
    SELECT sm.*, dt.name AS duty_name, dt.emoji AS duty_emoji
    FROM scheduled_messages sm
    LEFT JOIN duty_types dt ON dt.id = sm.duty_type_id
    ORDER BY sm.sort_order ASC, sm.send_time ASC
  `).all();
}

/** Yalnızca etkin mesajlar (cron bunları zamanlar). */
function getEnabled() {
  return db.prepare(`
    SELECT sm.*, dt.name AS duty_name, dt.emoji AS duty_emoji
    FROM scheduled_messages sm
    LEFT JOIN duty_types dt ON dt.id = sm.duty_type_id
    WHERE sm.is_enabled = 1
    ORDER BY sm.sort_order ASC, sm.send_time ASC
  `).all();
}

function getById(id) {
  return db.prepare('SELECT * FROM scheduled_messages WHERE id = ?').get(id);
}

function getByKey(key) {
  return db.prepare('SELECT * FROM scheduled_messages WHERE key = ?').get(key);
}

/** Bir görev türüne bağlı sabah bildirimi (şablon önizlemesi için). */
function getDutyMessageFor(dutyTypeId) {
  return db.prepare(
    "SELECT * FROM scheduled_messages WHERE kind = 'duty' AND duty_type_id = ? ORDER BY sort_order LIMIT 1"
  ).get(dutyTypeId);
}

/** "SS:DD" biçimini doğrular (00:00 - 23:59). */
function isValidTime(value) {
  return /^([01]\d|2[0-3]):([0-5]\d)$/.test(String(value ?? '').trim());
}

/** Tek bir mesajın saatini günceller. */
function setTime(id, time) {
  db.prepare('UPDATE scheduled_messages SET send_time = ? WHERE id = ?').run(time, id);
}

/** Etkin/pasif değiştirir. */
function setEnabled(id, enabled) {
  db.prepare('UPDATE scheduled_messages SET is_enabled = ? WHERE id = ?').run(enabled ? 1 : 0, id);
}

/** Şablon metni için üst sınır (Discord mesaj sınırı 2000 karakter). */
const MAX_TEMPLATE_LENGTH = 1900;

/**
 * Bir mesaj şablonunu doğrular.
 *
 * `duty` mesajının şablonu Discord'daki onay SORUSUDUR; kimin sorulduğu belli
 * olsun diye {name} veya {first} içermek zorundadır. Hatırlatmalarda böyle bir
 * zorunluluk yoktur (çoğu sabit metindir).
 *
 * @returns {string[]} Hata mesajları (boşsa geçerli).
 */
function validateTemplate(template, message) {
  const errors = [];
  const text = String(template ?? '').trim();

  if (!text) {
    errors.push(`"${message.name}" için mesaj metni boş bırakılamaz.`);
    return errors;
  }
  if (text.length > MAX_TEMPLATE_LENGTH) {
    errors.push(`"${message.name}" mesajı çok uzun (${text.length} karakter). En fazla ${MAX_TEMPLATE_LENGTH} olabilir.`);
  }
  if (message.kind === 'duty' && !/\{(name|first|mention)\}/.test(text)) {
    errors.push(`"${message.name}" bir onay sorusudur; kimin sorulduğu belli olsun diye {name}, {first} veya {mention} içermelidir.`);
  }

  return errors;
}

/**
 * Ayarlar formundan gelen saatleri, metinleri ve etkinlik durumlarını DOĞRULAR
 * ama kaydetmez.
 *
 * Doğrulama ve kayıt bilerek ayrılmıştır: form aynı anda `settings` tablosunu da
 * güncelliyor. İkisinden biri geçersizken diğerini yazsaydık, hata ekranı
 * gösterirken verinin bir kısmı değişmiş olurdu (kısmi kayıt).
 *
 * Form alanları `time_<id>`, `template_<id>` ve `enabled_<id>` biçiminde gelir;
 * böylece kaç mesaj tanımlı olursa olsun aynı kod çalışır (yeni mesaj eklenince
 * form kendiliğinden büyür).
 *
 * @param {object} input req.body
 * @returns {{ errors: string[], updates?: object[] }}
 */
function validateSchedule(input) {
  const errors = [];
  const updates = [];

  for (const message of getAll()) {
    const rawTime = input[`time_${message.id}`];
    if (rawTime === undefined) continue; // Form bu satırı göndermemiş.

    const time = String(rawTime).trim();
    if (!isValidTime(time)) {
      errors.push(`"${message.name}" için geçersiz saat: ${time || '(boş)'}. SS:DD biçiminde olmalı.`);
      continue;
    }

    // Şablon alanı formda yoksa mevcut metin korunur (geriye dönük uyumluluk).
    const rawTemplate = input[`template_${message.id}`];
    let template = message.message_template;
    if (rawTemplate !== undefined) {
      // Tarayıcılar textarea satır sonlarını \r\n gönderir; Discord'da fazladan
      // boşluk görünmesin diye normalize ediyoruz.
      template = String(rawTemplate).replace(/\r\n/g, '\n').trim();
      const templateErrors = validateTemplate(template, message);
      if (templateErrors.length > 0) {
        errors.push(...templateErrors);
        continue;
      }
    }

    // Checkbox işaretli değilse alan hiç gelmez → pasif.
    const enabled = input[`enabled_${message.id}`] ? 1 : 0;

    // Cron yalnızca saat/etkinlik değişiminde yeniden kurulmalı; metin değişikliği
    // zamanlamayı etkilemez (bir sonraki gönderimde yeni metin okunur).
    const timingChanged = time !== message.send_time || enabled !== message.is_enabled;
    const templateChanged = template !== message.message_template;

    if (timingChanged || templateChanged) {
      updates.push({ id: message.id, time, enabled, template, timingChanged });
    }
  }

  if (errors.length > 0) return { errors };
  return { errors: [], updates };
}

/**
 * `validateSchedule()` çıktısını tek işlemde kaydeder.
 *
 * @param {object[]} updates
 * @returns {{ saved: boolean, timingChanged: boolean }}
 *   saved         — herhangi bir değişiklik yazıldı mı?
 *   timingChanged — saat/etkinlik değişti mi? (yalnızca bu durumda cron yenilenir)
 */
function saveSchedule(updates) {
  if (updates.length === 0) return { saved: false, timingChanged: false };

  const saveAll = db.transaction((rows) => {
    for (const row of rows) {
      db.prepare(
        'UPDATE scheduled_messages SET send_time = ?, is_enabled = ?, message_template = ? WHERE id = ?'
      ).run(row.time, row.enabled, row.template, row.id);
    }
  });
  saveAll(updates);

  return { saved: true, timingChanged: updates.some((row) => row.timingChanged) };
}

/**
 * Yeni zamanlanmış mesaj ekler (genişletme noktası).
 *
 * @example
 *   create({
 *     key: 'kitchen_check',
 *     name: 'Mutfak Düzeni',
 *     send_time: '16:00',
 *     message_template: '🍽️ Mutfağı toplamayı unutmayalım.',
 *     kind: 'reminder',
 *   });
 */
function create({ key, name, send_time, message_template, kind = 'reminder', duty_type_id = null, sort_order = 99 }) {
  if (!isValidTime(send_time)) {
    throw new Error(`Geçersiz saat: ${send_time}. SS:DD biçiminde olmalı.`);
  }
  if (kind === 'duty' && !duty_type_id) {
    throw new Error("kind='duty' olan mesaj bir duty_type_id taşımalıdır.");
  }

  const result = db.prepare(`
    INSERT INTO scheduled_messages (key, name, send_time, message_template, kind, duty_type_id, sort_order)
    VALUES (@key, @name, @send_time, @message_template, @kind, @duty_type_id, @sort_order)
  `).run({ key, name, send_time, message_template, kind, duty_type_id, sort_order });

  return getById(result.lastInsertRowid);
}

module.exports = {
  getAll,
  getEnabled,
  getById,
  getByKey,
  getDutyMessageFor,
  isValidTime,
  setTime,
  setEnabled,
  validateTemplate,
  validateSchedule,
  saveSchedule,
  create,
};
