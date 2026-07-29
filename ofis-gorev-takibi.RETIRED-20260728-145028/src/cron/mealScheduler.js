'use strict';

/**
 * Yemek menüsü duyurusunun zamanlayıcısı (varsayılan 15:00).
 *
 * NEDEN AYRI BİR ZAMANLAYICI?
 * ---------------------------
 * Görev mesajları `scheduled_messages` tablosundan beslenir ve `kind` sütunu
 * yalnızca 'duty'/'reminder' değerlerini kabul eder. Yemek duyurusunu oraya
 * sıkıştırmak, çalışan bir tablonun CHECK kısıtını değiştirmeyi gerektirirdi.
 * Modül bağımsız kalsın diye kendi tek işlik zamanlayıcısıyla gelir: dosya
 * silinse görev zamanlayıcısı hiç etkilenmez.
 *
 * Saat `settings.meal_notify_time` içinde tutulur ve Yemek Menüsü sayfasından
 * değiştirilir; kaydedildiğinde `reschedule()` çağrılır, sunucu yeniden
 * başlatmak gerekmez.
 *
 * ÇALIŞMA GÜNÜ KONTROLÜ YOKTUR — bilerek. Duyurunun tek koşulu "yarının menüsü
 * veritabanında var mı" sorusudur. Hafta sonu için menü yüklenmediyse zaten
 * mesaj gitmez; yüklendiyse de göndermemek için bir sebep yoktur.
 */

const cron = require('node-cron');
const { config } = require('../config');
const settingsService = require('../services/settings.service');
const mealNotifier = require('../services/mealNotifier.service');
const scheduledMessageService = require('../services/scheduledMessage.service');
const log = require('../utils/logger').create('meal-cron');

const DEFAULT_TIME = '15:00';

/** @type {import('node-cron').ScheduledTask|null} */
let task = null;
let activeTime = null;
let lastRun = null;

/** Ayarlardaki duyuru saati; geçersizse varsayılana düşer. */
function getTime() {
  const value = settingsService.get('meal_notify_time', DEFAULT_TIME);
  return scheduledMessageService.isValidTime(value) ? value : DEFAULT_TIME;
}

/** "15:00" -> "0 15 * * *" */
function toCronExpression(time) {
  const [hour, minute] = time.split(':').map(Number);
  return `${minute} ${hour} * * *`;
}

/**
 * Zamanlanmış çalıştırma. Hata fırlatmaz: yemek modülündeki bir sorun süreci
 * düşürmemeli, diğer cron işlerini etkilememelidir.
 */
async function runJob() {
  const startedAt = new Date();

  try {
    const result = await mealNotifier.announceTomorrow({ source: 'cron' });
    lastRun = { at: startedAt, ok: result.ok, skipped: Boolean(result.skipped), message: result.message };

    if (!result.ok) log.error(`Duyuru başarısız: ${result.message}`);
  } catch (error) {
    log.error('Yemek duyurusu çalıştırılırken beklenmeyen hata', error);
    lastRun = { at: startedAt, ok: false, skipped: false, message: error.message };
  }
}

/** Kurulu işi durdurur. */
function stop() {
  if (task) {
    task.stop();
    task = null;
    activeTime = null;
  }
}

/**
 * İşi (yeniden) kurar. Saat değiştiğinde controller tarafından çağrılır.
 * @returns {{ ok: boolean, message: string, time: string }}
 */
function reschedule() {
  stop();

  const time = getTime();
  const expression = toCronExpression(time);

  if (!cron.validate(expression)) {
    const message = `Yemek duyurusu için geçersiz saat: ${time}`;
    log.error(message);
    return { ok: false, message, time };
  }

  task = cron.schedule(expression, runJob, { scheduled: true, timezone: config.timezone });
  activeTime = time;

  const message = `Yemek duyurusu zamanlandı → ${time} (${config.timezone})`;
  log.info(message);
  return { ok: true, message, time };
}

/** Açılışta çağrılır. */
function initialize() {
  return reschedule();
}

/** Panelde gösterilecek durum. */
function getStatus() {
  return {
    active: Boolean(task),
    time: activeTime ?? getTime(),
    timezone: config.timezone,
    lastRun,
  };
}

/** Elle tetikleme ("Yarının Menüsünü Şimdi Gönder"). */
async function triggerNow() {
  const result = await mealNotifier.announceTomorrow({ source: 'manual', force: true });
  lastRun = { at: new Date(), ok: result.ok, skipped: Boolean(result.skipped), message: result.message };
  return result;
}

module.exports = { initialize, reschedule, stop, getStatus, getTime, triggerNow, toCronExpression, DEFAULT_TIME };
