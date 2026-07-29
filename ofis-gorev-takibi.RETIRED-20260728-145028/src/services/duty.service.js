'use strict';

/**
 * Zamanlanmış mesajları yürüten servis (rotasyon + Discord + geçmiş).
 *
 * Cron, her zamanlanmış mesaj için `runScheduledMessage()` çağırır. Mesajın
 * çeşidine göre iki farklı yol izlenir:
 *
 *   kind='duty'     (örn. 08:05 sabah bildirimi)
 *     → Discord'da ETKİLEŞİMLİ onay akışını başlatır: "X bugün ofiste mi?"
 *       Geçmişe kayıt ve sıra hareketi, biri "Evet" dediğinde
 *       `dutyConfirmation.service` tarafından yapılır.
 *
 *   kind='reminder' (örn. 10:30 / 15:00 / 17:20)
 *     1. Şablondan mesajı üret ve GÜNÜN GÖREVLİSİNE ÖZEL MESAJ (DM) olarak gönder.
 *     → Sıraya ve geçmişe DOKUNULMAZ. Bu ayrım kasıtlıdır: aksi halde günde
 *       dört kişinin sırası yanardı.
 *
 * HATIRLATMALAR KANALA DEĞİL, GÖREVLİYE GİDER
 * -------------------------------------------
 * Kanal yalnızca sabahki onay sorusu için kullanılır. Görevli kesinleştikten
 * sonraki tüm mesajlar (günaydın + gün içi hatırlatmalar) yalnızca o kişinin
 * özel mesaj kutusuna düşer; kanal gereksiz bildirimle dolmaz.
 * Gönderim ayrıntıları: services/dutyNotifier.service.js
 *
 * SIRA YALNIZCA GÖREVİ YAPANLA İLERLER
 * ------------------------------------
 * Ofiste olmadığı için atlanan kişi sırasını kaybetmez; ertesi gün yine ondan
 * sorulur. Sıra ancak kişi görevi fiilen yaptığında ilerler. Bkz.
 * `rotation.service.completeDuty()`.
 *
 * İDEMPOTENS (yalnızca kind='duty' için)
 * --------------------------------------
 * Bir gün + görev türü için tek onay akışı vardır. Cron çift tetiklense, sunucu
 * yeniden başlasa veya admin "Şimdi Gönder" dese bile yeni akış açılmaz; mevcut
 * mesaj tazelenir, kesinleşmişse dokunulmaz.
 */

const { renderTemplate } = require('../discord/messages');
const dutyTypeService = require('./dutyType.service');
const scheduledMessageService = require('./scheduledMessage.service');
const dutyNotifier = require('./dutyNotifier.service');
const settingsService = require('./settings.service');
const { todayISO } = require('../utils/date');
const log = require('../utils/logger').create('duty');

/**
 * Hatırlatma mesajını GÜNÜN GÖREVLİSİNE özel mesaj olarak gönderir
 * (sıraya ve geçmişe dokunmaz).
 *
 * Şablondaki {name}/{first} gibi değişkenler görevlinin bilgileriyle doldurulur;
 * metin doğrudan ona hitap eder.
 *
 * GÖREVLİ HENÜZ BELLİ DEĞİLSE HİÇBİR ŞEY GÖNDERİLMEZ
 * --------------------------------------------------
 * Mesajın gideceği tek adres günün görevlisidir. Sabahki onay akışı henüz
 * sonuçlanmadıysa (kimse "Evet" demediyse) gönderilecek adres yoktur; bu bir
 * hata değildir, log'a yazılır ve cron normal çalışmaya devam eder.
 *
 * @param {object} message scheduled_messages satırı
 * @returns {Promise<{ ok: boolean, message: string, skipped?: boolean }>}
 */
async function runReminder(message) {
  // Hatırlatma bir göreve bağlıysa o türün, değilse varsayılan türün görevlisi.
  const dutyType = message.duty_type_id
    ? dutyTypeService.getById(message.duty_type_id)
    : dutyTypeService.getDefault();

  if (!dutyType) {
    log.info(`Hatırlatma atlandı (${message.name}): tanımlı görev türü yok.`);
    return { ok: true, skipped: true, message: 'Tanımlı görev türü yok; hatırlatma gönderilmedi.' };
  }

  const employee = dutyNotifier.getTodayAssignee(dutyType.id);
  if (!employee) {
    log.info(`Hatırlatma atlandı (${message.name}): bugünkü görevli henüz kesinleşmedi.`);
    return {
      ok: true,
      skipped: true,
      message: 'Bugünkü görevli henüz kesinleşmedi; hatırlatma gönderilmedi.',
    };
  }

  const content = renderTemplate(message.message_template, {
    employee,
    dutyType,
    company: settingsService.get('company_name'),
    date: todayISO(),
  });

  return dutyNotifier.sendToEmployee(employee, content, { label: message.name });
}

/**
 * Görev bildirimi: ETKİLEŞİMLİ onay akışını başlatır.
 *
 * Artık doğrudan "Bugünkü görevli X" mesajı GÖNDERMEZ. Bunun yerine Discord'da
 * butonlu bir soru gönderir ("X bugün ofiste mi?") ve cevaba göre sırayı
 * yürütür. Geçmişe kayıt ve rotasyon ilerletme, biri "Evet" dediğinde
 * `dutyConfirmation.service` tarafından yapılır.
 *
 * Akış durumu tamamen veritabanındadır; bu fonksiyon yalnızca akışı başlatır
 * veya (zaten varsa) mevcut mesajı tazeler. `source` ve idempotens ayrıntıları
 * için bkz. dutyConfirmation.service.js.
 *
 * @param {object} message  scheduled_messages satırı (kind='duty')
 * @param {object} options
 * @param {'cron'|'manual'} [options.source]
 * @returns {Promise<{ ok: boolean, message: string, skipped?: boolean }>}
 */
async function runDutyMessage(message, { source = 'cron' } = {}) {
  const dutyType = dutyTypeService.getById(message.duty_type_id);
  if (!dutyType) return { ok: false, message: 'Görev türü bulunamadı.' };

  // Lazy require: döngüsel bağımlılığı önler (confirmation → bot → confirmation).
  const confirmation = require('./dutyConfirmation.service');
  return confirmation.startFlow({ dutyTypeId: message.duty_type_id, source });
}

/**
 * Zamanlanmış bir mesajı çeşidine göre yürütür. Cron'un tek giriş noktası.
 *
 * @param {object} message scheduled_messages satırı
 * @param {object} [options]
 */
async function runScheduledMessage(message, options = {}) {
  if (message.kind === 'duty') {
    return runDutyMessage(message, options);
  }
  return runReminder(message);
}

/**
 * Bugünkü görev onay akışını elle başlatır/tazeler (panel butonu).
 * Görev mesajı artık etkileşimlidir; sıra ilerletme onay üzerinden olur.
 */
async function resendToday(dutyTypeId) {
  const message = scheduledMessageService.getDutyMessageFor(dutyTypeId);
  if (!message) {
    return { ok: false, message: 'Bu görev türü için tanımlı bir sabah bildirimi yok.' };
  }
  return runDutyMessage(message, { source: 'manual' });
}

/**
 * Tek bir zamanlanmış mesajı elle gönderir (Ayarlar → "Gönder" butonu).
 *   - Hatırlatma  → sabit metni gönderir.
 *   - Görev mesajı → etkileşimli onay akışını başlatır/tazeler.
 */
async function sendMessageNow(messageId) {
  const message = scheduledMessageService.getById(messageId);
  if (!message) return { ok: false, message: 'Mesaj bulunamadı.' };

  if (message.kind === 'reminder') {
    return runReminder(message);
  }
  return runDutyMessage(message, { source: 'manual' });
}

module.exports = { runScheduledMessage, runDutyMessage, runReminder, resendToday, sendMessageNow };
