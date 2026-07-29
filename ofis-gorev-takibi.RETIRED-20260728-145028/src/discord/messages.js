'use strict';

/**
 * Discord mesaj şablonlarının işlenmesi.
 *
 * Şablonlar `scheduled_messages.message_template` sütununda tutulur ve süslü
 * parantezli değişkenler içerir. Böylece yeni mesaj veya görev türü eklerken
 * kod yazmak gerekmez.
 *
 * KULLANILABİLİR DEĞİŞKENLER
 * --------------------------
 *   {name}     -> Çalışanın adı soyadı           (örn. "Beril Kahramanca")
 *   {first}    -> Yalnızca ilk ad                (örn. "Beril")
 *   {mention}  -> Discord etiketi; ID yoksa isim (örn. "<@123...>" veya "Beril Kahramanca")
 *   {emoji}    -> Görev türünün emojisi          (örn. "☕")
 *   {duty}     -> Görev türünün adı              (örn. "Çay")
 *   {company}  -> Ayarlardaki şirket adı
 *   {date}     -> Uzun Türkçe tarih              (örn. "17 Temmuz 2026 Cuma")
 *   {gun}      -> Görev günü, düz hâl            ("Yarın" veya "Pazartesi")
 *   {gunUn}    -> Görev günü, -in hâli           ("Yarının" veya "Pazartesinin")
 *
 * Örnek şablon:
 *   "☀️ Günaydın. Bugünkü çay görevlisi: {emoji} {name}. Herkese iyi çalışmalar."
 */

const { formatLongTR, todayISO, addDays } = require('../utils/date');

/** Hafta günü indeksi (0=Pazar) → düz ve -in hâlli Türkçe ad. */
const WEEKDAY_LABELS = [
  { plain: 'Pazar', genitive: 'Pazarın' },
  { plain: 'Pazartesi', genitive: 'Pazartesinin' },
  { plain: 'Salı', genitive: 'Salının' },
  { plain: 'Çarşamba', genitive: 'Çarşambanın' },
  { plain: 'Perşembe', genitive: 'Perşembenin' },
  { plain: 'Cuma', genitive: 'Cumanın' },
  { plain: 'Cumartesi', genitive: 'Cumartesinin' },
];

/**
 * Bir görev tarihi için gün etiketini üretir.
 *
 * Görev tarihi tam olarak YARIN ise "Yarın" denir (en tanıdık ifade). Değilse —
 * örneğin Cuma 17:00'de sorulan gün Pazartesi'dir, aradaki hafta sonu atlanır —
 * gün adı kullanılır: "Pazartesinin görevlisi belirleniyor".
 *
 * @param {string} targetISO Görev günü (YYYY-MM-DD).
 * @param {string} [todayIso] Karşılaştırma günü; varsayılan bugün.
 * @returns {{ plain: string, genitive: string }}
 */
function dayLabel(targetISO, todayIso = todayISO()) {
  if (targetISO && targetISO === addDays(todayIso, 1)) {
    return { plain: 'Yarın', genitive: 'Yarının' };
  }
  const weekdayIndex = new Date(`${targetISO}T12:00:00Z`).getUTCDay();
  return WEEKDAY_LABELS[weekdayIndex] ?? { plain: 'Yarın', genitive: 'Yarının' };
}

/**
 * Discord kullanıcı etiketi üretir. ID tanımlı değilse düz isme düşer,
 * böylece Discord hesabı olmayan çalışan için de mesaj anlamlı kalır.
 */
function buildMention(employee) {
  return employee.discord_user_id ? `<@${employee.discord_user_id}>` : employee.full_name;
}

/** "Beril Kahramanca" -> "Beril" (samimi hitap için {first} değişkeni). */
function firstName(fullName) {
  return String(fullName ?? '').trim().split(/\s+/)[0] || String(fullName ?? '');
}

/**
 * Şablondaki değişkenleri gerçek değerlerle değiştirir.
 *
 * @param {string} template Ham şablon metni.
 * @param {object} context
 * @param {object} context.employee   Görevli çalışan.
 * @param {object} context.dutyType   Görev türü kaydı.
 * @param {string} [context.company]  Şirket adı.
 * @param {string} [context.date]     ISO tarih; varsayılan bugün.
 * @returns {string} Gönderilmeye hazır mesaj.
 */
function renderTemplate(template, { employee, dutyType, company = '', date = todayISO() }) {
  const day = dayLabel(date);
  const values = {
    name: employee.full_name,
    first: firstName(employee.full_name),
    mention: buildMention(employee),
    emoji: dutyType.emoji || '',
    duty: dutyType.name,
    company,
    date: formatLongTR(date),
    // Gün etiketi: yarınsa "Yarın", değilse gün adı ("Pazartesi"). Cuma 17:00'de
    // sorulan gün Pazartesi olduğu için otomatik "Pazartesi" olur.
    gun: day.plain,
    gunUn: day.genitive, // "Yarının" / "Pazartesinin" (görevlisi belirleniyor)
  };

  // {key} kalıplarını tek geçişte değiştir. Tanınmayan değişken olduğu gibi kalır,
  // böylece şablon hatası sessizce boş metne dönüşmez, gözle fark edilir.
  return template.replace(/\{(\w+)\}/g, (match, key) =>
    Object.prototype.hasOwnProperty.call(values, key) ? values[key] : match
  );
}

module.exports = { renderTemplate, buildMention, firstName, dayLabel };
