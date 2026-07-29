'use strict';

/**
 * Görevliye ÖZEL MESAJ (DM) olarak giden metinler.
 *
 * NEREYE NE GİDER?
 * ----------------
 *   Kanal → 17:00'deki butonlu onay sorusu ("X yarın ofiste mi?") ve o akışın
 *           sonuç metni. Bkz. confirmationMessages.js
 *
 *           Soru bilerek KANALA gider: kişi özel mesajlarına bakmıyor olabilir
 *           ve akış cevapsız kalırsa ertesi günün görevlisi hiç belirlenmez.
 *           Kanalda ekipten herhangi biri de cevaplayabilir.
 *
 *   DM    → görevli KESİNLEŞTİKTEN sonra yalnızca o kişiye:
 *             • "Yarın görevlisi sensin, erken gelmeyi unutma"  (bu dosya)
 *             • Ertesi gün 10:30 / 15:00 hatırlatmaları
 *               (metinleri panelden yönetilir: scheduled_messages.message_template)
 *
 * Buradaki metin de şablon değişkenlerini destekler ({first}, {name}, {emoji}...);
 * bkz. messages.js. Böylece hatırlatmalarla aynı değişken sözlüğü geçerlidir.
 */

const { renderTemplate } = require('./messages');

/**
 * Görev kesinleştiğinde görevliye gönderilen atama mesajı.
 *
 * BİR GÜN ÖNCEDEN gönderilir: 17:00'deki onay akışı "Evet" cevabını alır almaz
 * kişinin DM'i bu metinle güncellenir. Böylece görevli ertesi güne hazırlıklı
 * başlar; sabah ayrıca bir bildirim yapılmaz.
 */
const DUTY_ASSIGNED_TEMPLATE =
  '📌 Merhaba {name},\n\n' +
  'Yarın ofis görevlisi sensin.\n\n' +
  'Gün içerisinde lütfen aşağıdaki ihtiyaçları kontrol etmeyi unutma:\n\n' +
  '• ☕ Kahve\n' +
  '• 🍵 Çay\n' +
  '• 🧻 Peçete\n\n' +
  'Eksik varsa tamamlamanı rica ederiz.\n\n' +
  'İyi çalışmalar. 😊';

/**
 * "Görev sende" DM metnini üretir.
 *
 * @param {object} context renderTemplate bağlamı (employee, dutyType, company, date).
 * @returns {string}
 */
function renderDutyAssigned(context) {
  return renderTemplate(DUTY_ASSIGNED_TEMPLATE, context);
}

module.exports = { renderDutyAssigned, DUTY_ASSIGNED_TEMPLATE };
