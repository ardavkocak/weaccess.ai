'use strict';

/**
 * Yemek menüsü duyurusunun zamanlayıcısı.
 *
 * NEDEN AYRI BİR ZAMANLAYICI?
 * ---------------------------
 * Görev mesajları `scheduled_messages` tablosundan beslenir ve `kind` sütunu
 * yalnızca 'duty'/'reminder' değerlerini kabul eder. Yemek duyurusunu oraya
 * sıkıştırmak, çalışan bir tablonun CHECK kısıtını değiştirmeyi gerektirirdi.
 * Modül bağımsız kalsın diye kendi tek işlik zamanlayıcısıyla gelir: dosya
 * silinse görev zamanlayıcısı hiç etkilenmez.
 *
 * SAAT HER ZAMAN VERİTABANINDAN OKUNUR — KOD İÇİNDE SABİT SAAT/CRON İFADESİ YOK
 * -------------------------------------------------------------------------
 * Eskiden bu dosya, ayarlardaki saate göre TEK BİR cron işi kaydediyordu
 * (örn. "0 15 * * *"); saat değiştiğinde bu işin `reschedule()` ile yeniden
 * kurulması gerekiyordu. Bu, yalnızca AYNI Node sürecinin kendi panelinden
 * değiştirildiğinde işe yarıyordu — Office Portal (Django) `settings`
 * tablosuna doğrudan yazdığında Node'un bunu bilmesinin hiçbir yolu yoktu.
 *
 * Şimdiki tasarım bunun yerine HER DAKİKA çalışan tek bir kontrol kullanır:
 * her tetiklemede `settings.meal_notify_time` DOĞRUDAN veritabanından okunur
 * ve o anki saatle karşılaştırılır. Eşleşirse duyuru gönderilir. Böylece:
 *   - Saat İSTER Node panelinden İSTER Office Portal'dan değiştirilsin, bir
 *     sonraki dakika kontrolünde OTOMATİK olarak devreye girer — süreç
 *     yeniden başlatılmaya ya da ayrıca "reschedule" çağrılmaya gerek YOKTUR.
 *   - `announceTomorrow()`'un kendi `announced_at` kontrolü zaten aynı günde
 *     iki kez göndermeyi engeller; bu yüzden "her dakika kontrol" tasarımı
 *     yanlışlıkla mükerrer mesaj riski taşımaz.
 *
 * ÇALIŞMA GÜNÜ KONTROLÜ YOKTUR — bilerek. Duyurunun tek koşulu "yarının menüsü
 * veritabanında var mı" sorusudur. Hafta sonu için menü yüklenmediyse zaten
 * mesaj gitmez; yüklendiyse de göndermemek için bir sebep yoktur.
 */

const cron = require('node-cron');
const { config } = require('../config');
const settingsService = require('../services/settings.service');
const mealNotifier = require('../services/mealNotifier.service');
const mealMenuService = require('../services/mealMenu.service');
const scheduledMessageService = require('../services/scheduledMessage.service');
const { todayISO, addDays } = require('../utils/date');
const log = require('../utils/logger').create('meal-cron');

const DEFAULT_TIME = '10:00';
const ENABLED_KEY = 'meal_notify_enabled';

/** @type {import('node-cron').ScheduledTask|null} */
let task = null;
let lastRun = null;
/** Bu süreçte "az önce gönderdik" tekrarını önlemek için (aynı dakika içinde çift tetiklenme). */
let lastFiredAtMinute = null;

/** Otomatik gönderim açık mı? Varsayılan: açık. */
function isEnabled() {
  return settingsService.get(ENABLED_KEY, '1') !== '0';
}

/** Ayarlardaki duyuru saati; geçersizse varsayılana düşer. HER ÇAĞRIDA veritabanından okunur. */
function getTime() {
  const value = settingsService.get('meal_notify_time', DEFAULT_TIME);
  return scheduledMessageService.isValidTime(value) ? value : DEFAULT_TIME;
}

/** Ofis saat diliminde şu anki "HH:MM". */
function nowHHMM() {
  return new Intl.DateTimeFormat('tr-TR', {
    timeZone: config.timezone, hour: '2-digit', minute: '2-digit', hour12: false,
  }).format(new Date());
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

/**
 * Her dakika çalışan kontrol: şu anki saat, ayarlardaki hedef saate eşit mi?
 * Eşitse ve bu dakika için henüz tetiklenmediyse duyuruyu gönderir.
 */
async function tick() {
  if (!isEnabled()) return;

  const nowKey = `${todayISO()}T${nowHHMM()}`; // aynı dakika içinde ikinci kez çalışmasın
  if (nowKey === lastFiredAtMinute) return;

  if (nowHHMM() !== getTime()) return;

  lastFiredAtMinute = nowKey;
  log.info(`Yemek duyurusu saati geldi (${getTime()}), gönderiliyor...`);
  await runJob();
}

/** Durdurur (kapanışta çağrılır). */
function stop() {
  if (task) {
    task.stop();
    task = null;
  }
}

/** Her dakika çalışan kontrolü kurar. Saat DEĞİŞSE BİLE yeniden çağrılmasına gerek yoktur. */
function reschedule() {
  stop();
  task = cron.schedule('* * * * *', tick, { scheduled: true, timezone: config.timezone });
  const message = isEnabled()
    ? `Yemek duyurusu kontrolü çalışıyor; hedef saat: ${getTime()} (${config.timezone}), her dakika kontrol ediliyor.`
    : 'Yemek duyurusu otomatik gönderimi KAPALI.';
  log.info(message);
  return { ok: true, message, time: getTime() };
}

/** Açılışta çağrılır. */
function initialize() {
  return reschedule();
}

/** Son gerçek gönderim tarihi (meal_menus.announced_at üzerinden). */
function getLastAnnouncedDate() {
  return mealMenuService.getLastAnnouncedDate();
}

/** Bir sonraki gönderimin ne zaman olacağı (bugün hedef saat geçmemişse bugün, geçtiyse yarın). */
function getNextFireAt() {
  const time = getTime();
  const isPast = nowHHMM() >= time;
  const date = isPast ? addDays(todayISO(), 1) : todayISO();
  return { date, time };
}

/** Panelde gösterilecek durum. */
function getStatus() {
  return {
    enabled: isEnabled(),
    active: Boolean(task),
    time: getTime(),
    timezone: config.timezone,
    lastRun,
    lastAnnouncedDate: getLastAnnouncedDate(),
    nextFireAt: getNextFireAt(),
  };
}

/** Elle tetikleme ("Yarının Menüsünü Şimdi Gönder") — zamanlamadan TAMAMEN bağımsız, anında çalışır. */
async function triggerNow() {
  const result = await mealNotifier.announceTomorrow({ source: 'manual', force: true });
  lastRun = { at: new Date(), ok: result.ok, skipped: Boolean(result.skipped), message: result.message };
  return result;
}

module.exports = {
  initialize, reschedule, stop, getStatus, getTime, isEnabled, triggerNow, tick, DEFAULT_TIME, ENABLED_KEY,
};
