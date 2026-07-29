'use strict';

/**
 * Görev türü servisi.
 *
 * Sistem tek bir "çay görevi"ne gömülü değildir. Her tür (çay, kahve, çöp, mutfak
 * düzeni...) burada bir kayıttır ve kendi BAĞIMSIZ sırasını + geçmişini taşır.
 *
 * Görev türü "sıra kimde?" sorusunun sahibidir; "ne zaman ne yazılacak?" sorusu
 * `scheduled_messages` tablosuna aittir. `create()` ikisini birlikte kurar.
 *
 * YENİ GÖREV TÜRÜ EKLEME
 * ----------------------
 * Kod değişikliği gerekmez:
 *
 *   dutyTypeService.create({
 *     key: 'coffee',
 *     name: 'Kahve',
 *     emoji: '☕',
 *     sendTime: '09:00',
 *     messageTemplate: '☀️ Bugünkü kahve görevlisi:\n{emoji} {name}',
 *   });
 *
 * Bu çağrı: görev türünü, rotasyon satırını ve 09:00'da çalışıp sırayı ilerleten
 * bir sabah bildirimini birlikte oluşturur. Sunucu yeniden başlatıldığında (veya
 * Ayarlar kaydedildiğinde) cron yeni mesajı da zamanlar.
 */

const db = require('../database/connection');
const { ensureRotationRows } = require('../database/schema');

/** Etkin/pasif tüm görev türleri. */
function getAll() {
  return db.prepare('SELECT * FROM duty_types ORDER BY id ASC').all();
}

/** Yalnızca etkin görev türleri (cron bunları işler). */
function getEnabled() {
  return db.prepare('SELECT * FROM duty_types WHERE is_enabled = 1 ORDER BY id ASC').all();
}

function getById(id) {
  return db.prepare('SELECT * FROM duty_types WHERE id = ?').get(id);
}

function getByKey(key) {
  return db.prepare('SELECT * FROM duty_types WHERE key = ?').get(key);
}

/**
 * Varsayılan görev türü: sistemin ana odağı olan çay görevi.
 * Çay kaydı bir şekilde silinmişse ilk sıradaki türe düşer.
 */
function getDefault() {
  return getByKey('tea') ?? getAll()[0] ?? null;
}

/**
 * Yeni görev türü ekler: tür + rotasyon satırı + sabah bildirimi.
 *
 * Üçü tek işlemde (transaction) kurulur; yarım kalmış bir görev türü
 * (rotasyonu olmayan ya da mesajı olmayan) oluşmaz.
 *
 * @param {object} params
 * @param {string} params.key             Benzersiz anahtar, örn. 'coffee'
 * @param {string} params.name            Görünen ad, örn. 'Kahve'
 * @param {string} [params.emoji]         Örn. '☕'
 * @param {string} [params.sendTime]      Sabah bildirimi saati (SS:DD)
 * @param {string} [params.messageTemplate] Mesaj şablonu; verilmezse üretilir.
 * @returns {object} Oluşturulan görev türü
 */
function create({ key, name, emoji = '', sendTime = '08:05', messageTemplate = null }) {
  // Döngüsel bağımlılığı önlemek için içeride çağrılır:
  // scheduledMessage.service → (yok) ; burada tek yönlü kalması için lazy require.
  const scheduledMessageService = require('./scheduledMessage.service');

  const run = db.transaction(() => {
    const result = db.prepare(`
      INSERT INTO duty_types (key, name, emoji)
      VALUES (@key, @name, @emoji)
    `).run({ key, name, emoji });

    const dutyTypeId = result.lastInsertRowid;

    ensureRotationRows(); // Yeni tür için boş rotasyon satırı oluştur.

    // Sıra ilerletmeyi tetikleyen sabah bildirimi.
    scheduledMessageService.create({
      key: `morning_${key}`,
      name: `${name} Görev Bildirimi`,
      send_time: sendTime,
      message_template: messageTemplate ??
        `☀️ Günaydın herkese.\n\nBugünkü ${name.toLocaleLowerCase('tr-TR')} görevlisi:\n{emoji} {name}\n\nHerkese iyi çalışmalar. 😊`,
      kind: 'duty',
      duty_type_id: dutyTypeId,
      sort_order: 10,
    });

    return getById(dutyTypeId);
  });

  return run();
}

module.exports = { getAll, getEnabled, getById, getByKey, getDefault, create };
