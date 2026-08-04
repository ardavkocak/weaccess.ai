'use strict';

/**
 * Zamanlanmış görev yöneticisi (node-cron).
 *
 * `scheduled_messages` tablosundaki ETKİN her satır için ayrı bir cron işi kurar.
 * Varsayılan takvim:
 *
 *   08:05  Sabah Görev Bildirimi   (duty)     → mesaj + geçmiş + sıra ilerlet
 *   10:30  Birinci Çay Kontrol     (reminder) → yalnızca mesaj
 *   15:00  İkinci Çay Kontrol      (reminder) → yalnızca mesaj
 *   17:20  Gün Sonu Hatırlatması   (reminder) → yalnızca mesaj
 *
 * Saatler panelden değiştirilebildiği için işler yeniden kurulabilir olmalıdır:
 * `reschedule()` tüm işleri durdurup tabloyu yeniden okur ve baştan kurar.
 * Böylece saat değişikliği sunucu yeniden başlatılmadan geçerli olur.
 *
 * Saat dilimi `config.timezone` (varsayılan Europe/Istanbul) üzerinden sabitlenir;
 * sunucu farklı bir bölgede çalışsa bile mesajlar ofis saatiyle gider.
 */

const cron = require('node-cron');
const { config } = require('../config');
const scheduledMessageService = require('../services/scheduledMessage.service');
const dutyService = require('../services/duty.service');
const calendar = require('../services/calendar.service');
const log = require('../utils/logger').create('cron');

/**
 * Kurulu işler: messageId → { task, message, expression }
 * @type {Map<number, object>}
 */
const jobs = new Map();

/** Son çalışma bilgisi (panelde gösterilir). */
let lastRun = null;

/**
 * "SS:DD" -> cron ifadesi ("dakika saat * * *").
 * Örn. "08:05" -> "5 8 * * *"
 */
function timeToCronExpression(time) {
  const [hour, minute] = time.split(':').map(Number);
  return `${minute} ${hour} * * *`;
}

/**
 * Tek bir zamanlanmış mesajı çalıştırır.
 * Hata fırlatmaz: bir mesajın hatası diğerlerini ve süreci etkilememeli.
 */
async function runJob(messageId) {
  // Hafta sonu / tatil kontrolü — tek karar noktası (calendar servisi).
  // Bu yalnızca OTOMATİK (cron) çalışmayı engeller; panelin manuel "Gönder" ve
  // "Onayı Başlat" butonları bu fonksiyondan geçmediği için hafta sonu da çalışır.
  if (!calendar.isWorkingDay()) {
    const reason = calendar.describeNonWorkingReason();
    log.info(`${reason} Otomatik görevler bugün çalışmıyor; mesaj ${messageId} atlandı.`);
    lastRun = {
      at: new Date(),
      name: 'Otomatik görevler',
      ok: true,
      skippedNonWorkingDay: true,
      message: `${reason} Otomatik görevler çalışmadı (manuel gönderim açık).`,
    };
    return;
  }

  // Satırı çalışma anında tazeleriz: admin şablonu/durumu değiştirmiş olabilir.
  const message = scheduledMessageService.getById(messageId);

  if (!message) {
    log.warn(`Mesaj ${messageId} bulunamadı, iş atlanıyor.`);
    return;
  }
  if (message.is_enabled !== 1) {
    log.debug(`"${message.name}" pasif, atlanıyor.`);
    return;
  }

  const startedAt = new Date();
  log.info(`Çalıştırılıyor: "${message.name}" (${message.send_time}, ${message.kind})`);

  try {
    const result = await dutyService.runScheduledMessage(message, { source: 'cron' });

    if (result.ok) log.info(`✓ ${message.name}: ${result.message}`);
    else log.error(`✗ ${message.name}: ${result.message}`);

    lastRun = { at: startedAt, name: message.name, ok: result.ok, message: result.message };
  } catch (error) {
    // Yakalanmayan hata süreci düşürmesin.
    log.error(`"${message.name}" çalıştırılırken beklenmeyen hata`, error);
    lastRun = { at: startedAt, name: message.name, ok: false, message: error.message };
  }
}

/** Tüm kurulu işleri durdurur. */
function stop() {
  for (const [, job] of jobs) job.task.stop();
  jobs.clear();
}

/**
 * Tabloyu okuyup tüm işleri (yeniden) kurar.
 * Ayarlar kaydedildiğinde controller tarafından çağrılır.
 *
 * @returns {{ ok: boolean, message: string, scheduled: number, errors: string[] }}
 */
function reschedule() {
  stop();

  const messages = scheduledMessageService.getEnabled();
  const errors = [];

  for (const message of messages) {
    if (!scheduledMessageService.isValidTime(message.send_time)) {
      const error = `"${message.name}" için geçersiz saat: ${message.send_time}`;
      log.error(error);
      errors.push(error);
      continue;
    }

    const expression = timeToCronExpression(message.send_time);

    if (!cron.validate(expression)) {
      const error = `"${message.name}" için geçersiz cron ifadesi: ${expression}`;
      log.error(error);
      errors.push(error);
      continue;
    }

    const task = cron.schedule(expression, () => runJob(message.id), {
      scheduled: true,
      timezone: config.timezone,
    });

    jobs.set(message.id, { task, message, expression });
    log.info(`Zamanlandı: "${message.name}" → ${message.send_time} (${expression})`);
  }

  const summary = `${jobs.size} mesaj zamanlandı (${config.timezone}).`;
  log.info(summary);

  return {
    ok: errors.length === 0,
    message: errors.length === 0 ? summary : `${summary} ${errors.length} hata var.`,
    scheduled: jobs.size,
    errors,
  };
}

/** Açılışta çağrılır. */
function initialize() {
  return reschedule();
}

/** Panelde göstermek için zamanlayıcı durumu. */
function getStatus() {
  const all = scheduledMessageService.getAll();

  return {
    active: jobs.size > 0,
    scheduledCount: jobs.size,
    totalCount: all.length,
    timezone: config.timezone,
    lastRun,
    // Bugün otomatik görevler çalışıyor mu? (hafta içi/tatil durumu)
    workingDayToday: calendar.isWorkingDay(),
    nonWorkingReason: calendar.describeNonWorkingReason(),
    // Her mesajın kurulu olup olmadığı, saatiyle birlikte.
    messages: all.map((message) => ({
      id: message.id,
      key: message.key,
      name: message.name,
      time: message.send_time,
      kind: message.kind,
      enabled: message.is_enabled === 1,
      running: jobs.has(message.id),
      expression: jobs.get(message.id)?.expression ?? null,
    })),
  };
}

/** Sabah görev bildiriminin saati (dashboard'da "bildirim bekliyor" rozetinde). */
function getDutyTime(dutyTypeId) {
  const message = scheduledMessageService.getDutyMessageFor(dutyTypeId);
  return message?.send_time ?? '08:05';
}

/** Elle tetikleme (test amaçlı). */
async function triggerNow(messageId) {
  await runJob(messageId);
  return lastRun;
}

module.exports = {
  initialize,
  reschedule,
  stop,
  getStatus,
  getDutyTime,
  triggerNow,
  timeToCronExpression,
};
