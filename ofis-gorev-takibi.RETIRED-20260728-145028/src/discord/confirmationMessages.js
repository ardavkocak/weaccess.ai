'use strict';

/**
 * Etkileşimli görev onayı mesaj metinleri.
 *
 * Kullanıcının istediği metinler birebir burada üretilir. Metinler sabittir
 * (şablon değişkeni sistemine bağlı değildir) çünkü akışa özgü ve dinamik cümle
 * yapıları içerir.
 */

/** "Beril Kahramanca" -> "Beril" (soruda ilk ad kullanılıyor). */
function firstName(fullName) {
  return String(fullName ?? '').trim().split(/\s+/)[0] || String(fullName ?? '');
}

/**
 * İlk adım sorusu için yerleşik varsayılan (şablon boşsa kullanılır).
 *
 * Soru BİR GÜN ÖNCEDEN, akşam 17:00'de ve KANALA gider — kişinin DM'ine değil.
 * Sebep: kişi özel mesajlarına bakmıyor olabilir ve cevap gelmezse ertesi günün
 * görevlisi hiç belirlenemez. Kanalda soru herkese görünür, ekipten biri de
 * cevaplayabilir.
 *
 * {mention} kişiyi etiketler; ilgili kişi bildirim alır ama mesaj kanalda durur.
 */
const DEFAULT_QUESTION_TEMPLATE =
  '📅 Yarın ofiste olacak mısın?\n\n👤 {mention}\n\nYarın ofiste misin?';

/**
 * İlk adım sorusunu ayarlardaki şablondan üretir.
 *
 * Şablon boşsa veya render için gereken bağlam yoksa varsayılana düşer; böylece
 * eksik yapılandırma soruyu tamamen boş bırakmaz.
 */
function renderFirstQuestion({ candidateName, context, template }) {
  const text = String(template ?? '').trim() || DEFAULT_QUESTION_TEMPLATE;

  if (!context?.employee || !context?.dutyType) {
    // Bağlam yoksa en azından adı yerine koy (test ve geri düşüş yolu).
    return text
      .replace(/\{name\}/g, candidateName)
      .replace(/\{first\}/g, firstName(candidateName));
  }

  // Lazy require: messages.js ↔ confirmationMessages.js döngüsünü önler.
  return require('./messages').renderTemplate(text, context);
}

/**
 * Onay sorusu — 17:00'de, ERTESİ İŞ GÜNÜ için, KANALA gider.
 *
 * METİN AYARLARDAN GELİR
 * ----------------------
 * Soru, görev bildiriminin `message_template` alanından (Ayarlar → Otomatik
 * Mesaj Saatleri) render edilir; admin panelden değiştirebilir. Şablon boşsa
 * DEFAULT_QUESTION_TEMPLATE kullanılır.
 *
 * TEK MESAJ, ZİNCİR HALİNDE
 * -------------------------
 * Akış boyunca TEK bir kanal mesajı düzenlenir. "Hayır" denince aynı mesaj
 * sıradaki kişinin sorusuna dönüşür; kanal yeni mesajlarla dolmaz. Kimin
 * atlandığı yazılır, çünkü ekip zaten aynı mesajı takip ediyor.
 *
 * Panelden sıfırlandıysa (isRetry) başa bir düzeltme notu eklenir.
 *
 * @param {object} p
 * @param {string} p.candidateName Şu an sorulan kişinin tam adı.
 * @param {string} [p.previousName] Bir önceki "Hayır" denen kişi (step > 0).
 * @param {boolean} p.isFirst İlk adım mı?
 * @param {boolean} [p.isRetry] Onay sıfırlandıktan sonra yeniden mi soruluyor?
 * @param {object} [p.context] Şablon değişkenlerinin kaynağı (employee, dutyType,
 *   company, date).
 * @param {string} [p.template] Ayarlardaki soru şablonu; boşsa varsayılan.
 */
function renderQuestion({ candidateName, isRetry = false, context = null, template = '' }) {
  const question = renderFirstQuestion({ candidateName, context, template });

  if (isRetry) {
    return `🔄 Görev onayı panelden sıfırlandı, yeniden soruluyor.\n\n${question}`;
  }

  // Akış tek bir kanal mesajında yürür; her adayda bu mesaj güncellenir.
  return question;
}

/**
 * KANALDAKİ kesinleşme mesajı (butonlar kaldırılır).
 *
 *   "☕ Yarının görevlisi belli oldu.
 *
 *    👤 @Beril Kahramanca
 *
 *    İyi çalışmalar! 😊"
 *
 * Ayrıntılı "görev sende, erken gel" metni buraya DEĞİL, kesinleşen kişinin
 * özel mesajına gider (bkz. directMessages.js). Kanalda yalnızca kısa bir özet
 * durur; herkes yarının görevlisini görür.
 *
 * Çalışanın Discord ID'si tanımlıysa isim yerine ETİKET yazılır (👤 @Beril).
 *
 * @param {object} p
 * @param {string} p.name Kesinleşen görevlinin tam adı.
 * @param {object} [p.employee] Çalışan kaydı; etiketleme için (discord_user_id).
 * @param {string} [p.holderName] Sırası korunan kişi; sıra ilerlediyse null.
 */
function renderConfirmed({ name, employee = null, holderName = null, dutyDate = null }) {
  // Etiket, ID varsa "<@123...>" olur; yoksa ismin kendisi.
  const who = employee ? require('./messages').buildMention(employee) : name;

  // Gün etiketi: "Yarının" / "Pazartesinin". Cuma 17:00'de sorulan gün Pazartesi.
  const gunUn = dutyDate ? require('./messages').dayLabel(dutyDate).genitive : 'Yarının';

  // Görevi sıranın sahibi değil de onun yerine biri üstlendiyse, sıranın kimde
  // kaldığı da yazılır — kimse hakkını kaybettiğini sanmasın.
  const keptNote = holderName
    ? `\n\n🔁 Sıra ${holderName} kişisinde kaldı; hakkı korundu.`
    : '';

  return `✅ ${gunUn} görevlisi belli oldu.\n\n👤 ${who}${keptNote}`;
}

/**
 * Herkese "Hayır" denip kimse kalmadığında (tam tur döndü).
 *
 * Kimse görevi üstlenmediği için sıra da ilerlemez; sonraki iş günü yine
 * sıranın sahibinden sorulur.
 */
function renderExhausted(dutyDate = null) {
  const gunUn = dutyDate ? require('./messages').dayLabel(dutyDate).genitive : 'Yarının';
  return (
    `⚠️ ${gunUn} görevi için uygun kişi bulunamadı; herkese soruldu.\n\n` +
    '🔁 Sıra ilerlemedi. Lütfen panelden manuel belirleyin.'
  );
}

/**
 * Cevap beklemeyen bir butona basıldığında mesajın yerine yazılan kısa özet.
 *
 * İki durumda kullanılır (bkz. dutyConfirmation.service.decideAnswer):
 *   - Görev zaten sonuçlanmış (biri daha önce "Evet" demiş).
 *   - Butonun akış kaydı bu veritabanında yok (mesaj eski bir kurulumdan kalmış).
 *
 * Her iki durumda da kullanıcıya teknik bir hata göstermenin faydası yoktur;
 * tek merak ettiği "bugün görev kimde?" sorusudur. Bu yüzden mesaj tek satıra
 * indirilir ve butonlar kaldırılır — mesaj bir daha tıklanabilir kalmaz.
 */
function renderResolved(name) {
  return `☕ Görevli: ${name}.`;
}

/**
 * Ne akış kaydı ne de günün görev kaydı bulunabildiğinde yazılır.
 * Butonlar yine kaldırılır; ölü bir mesajın tıklanabilir kalmasının anlamı yok.
 */
function renderOutdated() {
  return '⚠️ Bu mesaj artık geçerli değil. Güncel görev bilgisi yönetim panelindedir.';
}

/**
 * Panelden "Sırayı Geç" ile karar verildiğinde, bekleyen sorunun yerine yazılır.
 * Butonlar kaldırılır; artık cevap beklenmiyor.
 */
function renderManualOverride(name) {
  return `☕ Görev panelden belirlendi.\n\nGörevli: ${name}.\n\nİyi çalışmalar.`;
}

module.exports = {
  renderQuestion,
  renderConfirmed,
  renderExhausted,
  renderResolved,
  renderOutdated,
  renderManualOverride,
  firstName,
};
