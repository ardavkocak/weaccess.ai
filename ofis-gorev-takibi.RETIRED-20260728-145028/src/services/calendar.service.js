'use strict';

/**
 * Çalışma günü takvimi.
 *
 * "Bugün otomatik görevler çalışmalı mı?" sorusunun TEK karar noktasıdır. Tüm
 * zamanlanmış görevler (cron) bu servisi kullanır; böylece kural tek yerde durur
 * ve tutarlı kalır.
 *
 * KURAL
 * -----
 * Otomatik görevler yalnızca ÇALIŞMA GÜNLERİNDE çalışır: Pazartesi–Cuma.
 * Cumartesi ve Pazar günleri hiçbir otomatik Discord mesajı gönderilmez, sıra
 * ilerlemez. (Panelin manuel "Gönder"/"Onayı Başlat" butonları bu kontrolden
 * geçmez; onlar her gün çalışır.)
 *
 * GENİŞLETİLEBİLİRLİK — resmi tatiller
 * ------------------------------------
 * İleride resmi tatil desteği eklemek için yalnızca `isHoliday()` fonksiyonunu
 * doldurmak yeterlidir (örn. bir `holidays` tablosundan veya sabit bir listeden
 * kontrol). `isWorkingDay()` ve tüm çağıranlar otomatik olarak tatilleri de
 * dışlar; başka hiçbir yeri değiştirmek gerekmez.
 *
 * Gün hesabı ofis saat dilimine (config.timezone) göre yapılır: sunucu farklı
 * bir bölgede olsa bile "bugün hangi gün" ofis takvimine göre belirlenir.
 */

const { config } = require('../config');
const { todayISO, addDays } = require('../utils/date');

// 0 = Pazar, 6 = Cumartesi (JavaScript getUTCDay/getDay ile aynı numaralandırma).
const WEEKEND_DAYS = new Set([0, 6]);

/**
 * Verilen tarihin ofis saat dilimindeki haftanın günü (0=Pazar ... 6=Cumartesi).
 *
 * Önce ofis saat dilimindeki takvim tarihi (YYYY-MM-DD) bulunur, sonra o tarihin
 * haftanın günü okunur. Böylece saat dilimi/DST kaymaları günü etkilemez.
 */
function weekday(date = new Date()) {
  const iso = todayISO(date); // ofis saat diliminde YYYY-MM-DD
  return new Date(`${iso}T00:00:00Z`).getUTCDay();
}

/** Bugün (veya verilen tarih) hafta sonu mu? */
function isWeekend(date = new Date()) {
  return WEEKEND_DAYS.has(weekday(date));
}

/**
 * Bugün resmi tatil mi?
 *
 * Şimdilik her zaman false döner. Resmi tatil desteği eklemek isteyen buraya
 * bir kontrol yazar (örn. `holidays` tablosundan tarih araması). Yapının geri
 * kalanı değişmeden tatilleri de dışlar.
 */
function isHoliday(/* date = new Date() */) {
  return false;
}

/** Otomatik görevler bugün çalışmalı mı? (hafta içi VE tatil değil) */
function isWorkingDay(date = new Date()) {
  return !isWeekend(date) && !isHoliday(date);
}

/** Verilen ISO tarih (YYYY-MM-DD) çalışma günü mü? */
function isWorkingDayISO(isoDate) {
  return isWorkingDay(new Date(`${isoDate}T12:00:00Z`));
}

/**
 * Verilen tarihten SONRAKİ ilk çalışma gününü döner (YYYY-MM-DD).
 *
 * Görevli bir gün önceden belirlendiği için gereklidir: Cuma 17:00'de "yarın"
 * Cumartesi'dir ama görev Pazartesi'ye aittir. Hafta sonu ve tatiller atlanır.
 *
 * @param {string} [fromISO] Başlangıç tarihi; varsayılan bugün.
 * @returns {string} Sonraki çalışma günü.
 */
function nextWorkingDay(fromISO = todayISO()) {
  // 14 gün: art arda bu kadar tatil olması beklenmez; sonsuz döngüye karşı sınır.
  for (let offset = 1; offset <= 14; offset += 1) {
    const candidate = addDays(fromISO, offset);
    if (isWorkingDayISO(candidate)) return candidate;
  }
  // Olağandışı: hepsi tatilse ertesi güne düş (sistem tıkanmasın).
  return addDays(fromISO, 1);
}

/**
 * Çalışılmama nedeni — panel mesajları ve loglar için.
 * @returns {'weekend'|'holiday'|null} Çalışma günüyse null.
 */
function getNonWorkingReason(date = new Date()) {
  if (isWeekend(date)) return 'weekend';
  if (isHoliday(date)) return 'holiday';
  return null;
}

/** Nedenin Türkçe kısa açıklaması (panelde göstermek için). */
function describeNonWorkingReason(date = new Date()) {
  const reason = getNonWorkingReason(date);
  if (!reason) return null;

  const dayName = new Intl.DateTimeFormat('tr-TR', {
    timeZone: config.timezone,
    weekday: 'long',
  }).format(date);

  if (reason === 'holiday') return `Bugün (${dayName}) resmi tatil.`;
  return `Bugün hafta sonu (${dayName}).`;
}

module.exports = {
  weekday,
  isWeekend,
  isHoliday,
  isWorkingDay,
  isWorkingDayISO,
  nextWorkingDay,
  getNonWorkingReason,
  describeNonWorkingReason,
};
