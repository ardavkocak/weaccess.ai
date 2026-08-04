'use strict';

/**
 * Görevliye özel mesaj (DM) gönderiminin TEK noktası.
 *
 * NEDEN AYRI BİR SERVİS?
 * ---------------------
 * Günün görevlisine üç farklı yerden mesaj gidiyor:
 *   1. Onay akışında "Evet" alınınca      → "Günaydın, görev sende"
 *   2. Cron hatırlatmaları (10:30/15:00/17:20)
 *   3. Panelden "Sırayı Geç" ile görev devredilince
 * Üçünde de aynı üç soru var: kişi kim, Discord ID'si var mı, gönderilemezse ne
 * olacak? Cevap tek yerde dursun diye bu servis var; çağıranlar yalnızca "kime"
 * ve "ne" bilgisini verir.
 *
 * HATA POLİTİKASI
 * ---------------
 * Bu servisteki hiçbir fonksiyon HATA FIRLATMAZ. DM kapalıysa, kullanıcı botu
 * engellediyse, Discord ID girilmemişse veya Discord'a ulaşılamıyorsa yalnızca
 * log'a bilgilendirici bir satır yazılır:
 *
 *   DM gönderilemedi: Beril Kahramanca - Cannot send messages to this user.
 *
 * Cron akışı bundan etkilenmez, bir sonraki iş normal çalışır.
 */

const bot = require('../discord/bot');
const employeeService = require('./employee.service');
const historyService = require('./history.service');
const dutyTypeService = require('./dutyType.service');
const settingsService = require('./settings.service');
const { renderDutyAssigned } = require('../discord/directMessages');
const { todayISO } = require('../utils/date');
const log = require('../utils/logger').create('dm');

/**
 * O günün KESİNLEŞMİŞ görevlisini döner.
 *
 * Kaynak `duty_history`'dir: bu satır ancak görev kesinleştiğinde yazılır (onay
 * akışında "Evet" ya da panelden manuel devir). Dolayısıyla "görevli henüz belli
 * değil" durumu doğal olarak `null` ile ifade edilir — sıranın sahibine
 * (rotasyondaki aday) mesaj GİTMEZ; o kişi henüz görevli değildir, yalnızca
 * kendisine soru sorulan kişidir.
 *
 * Çalışan sonradan silinmişse geçmişteki isim snapshot'ına düşülür; Discord ID
 * olmadığı için mesaj gönderilemez ama isim log'da görünür.
 *
 * @param {number} dutyTypeId
 * @param {string} [date] ISO tarih; varsayılan bugün.
 * @returns {object|null} Çalışan kaydı (veya isim snapshot'ı), yoksa null.
 */
function getTodayAssignee(dutyTypeId, date = todayISO()) {
  const record = historyService.getByDate(dutyTypeId, date);
  if (!record) return null;

  return (
    employeeService.getById(record.employee_id) ?? {
      id: record.employee_id,
      full_name: record.employee_name,
      discord_user_id: null,
    }
  );
}

/**
 * Bir çalışana DM gönderir. Hata fırlatmaz.
 *
 * @param {object} employee Çalışan kaydı (full_name + discord_user_id).
 * @param {string} content  Gönderilecek metin.
 * @param {object} [options]
 * @param {string} [options.label] Log ve panel mesajlarında geçen mesaj adı.
 * @returns {Promise<{ ok: boolean, message: string, skipped?: boolean }>}
 */
async function sendToEmployee(employee, content, { label = 'Mesaj' } = {}) {
  const name = employee?.full_name ?? '—';

  // Discord ID girilmemiş: bu bir hata değil, eksik yapılandırmadır. Panelde
  // (Çalışanlar sayfası) doldurulabilir; o zamana kadar sessizce atlanır.
  if (!employee?.discord_user_id) {
    log.info(`DM gönderilemedi: ${name} - Discord ID tanımlı değil.`);
    return {
      ok: false,
      skipped: true,
      message: `${name} için Discord ID tanımlı olmadığından "${label}" gönderilemedi.`,
    };
  }

  const result = await bot.sendDirectMessage(employee.discord_user_id, content);

  if (result.ok) {
    log.info(`DM gönderildi: ${name} - ${label}`);
    return { ok: true, message: `"${label}" ${name} kişisine özel mesaj olarak gönderildi.` };
  }

  // Ham Discord metni log'a yazılır (örn. "Cannot send messages to this user."),
  // panele Türkçe açıklama döner.
  log.warn(`DM gönderilemedi: ${name} - ${result.reason ?? result.message}`);
  return { ok: false, message: `"${label}" ${name} kişisine gönderilemedi: ${result.message}` };
}

/**
 * "Günaydın, bugünkü ofis görevi sende" DM'ini gönderir.
 *
 * Görev kesinleştiği anda çağrılır (Discord'da "Evet" ya da panelden devir).
 *
 * @param {number} dutyTypeId
 * @param {object} employee Görevi üstlenen çalışan.
 * @returns {Promise<{ ok: boolean, message: string, skipped?: boolean }>}
 */
async function sendDutyAssigned(dutyTypeId, employee) {
  if (!employee) return { ok: false, skipped: true, message: 'Görevli belirlenmedi.' };

  try {
    const content = renderDutyAssigned({
      employee,
      dutyType: dutyTypeService.getById(dutyTypeId) ?? { name: '', emoji: '' },
      company: settingsService.get('company_name', ''),
      date: todayISO(),
    });

    return await sendToEmployee(employee, content, { label: 'Günaydın mesajı' });
  } catch (error) {
    // Son güvenlik ağı: metin üretimi/ayar okuma beklenmedik şekilde patlasa bile
    // görevin kesinleşmesi ya da cron akışı bundan etkilenmemeli.
    log.warn(`DM gönderilemedi: ${employee.full_name} - ${error.message}`);
    return { ok: false, message: `Günaydın mesajı gönderilemedi: ${error.message}` };
  }
}

module.exports = { getTodayAssignee, sendToEmployee, sendDutyAssigned };
