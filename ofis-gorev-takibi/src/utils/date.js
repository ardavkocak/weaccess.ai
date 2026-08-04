'use strict';

/**
 * Tarih yardımcıları.
 *
 * Tüm tarihler ofisin saat diliminde (config.timezone, varsayılan Europe/Istanbul)
 * hesaplanır. `new Date().toISOString()` UTC döndürdüğü için doğrudan kullanılmaz:
 * saat 03:00'te (TR) UTC henüz bir önceki gündedir ve "bugünün görevlisi" yanlış
 * güne yazılırdı. Bu yüzden gün hesabı Intl üzerinden saat dilimine sabitlenir.
 */

const { config } = require('../config');

/**
 * Ofis saat diliminde bugünün tarihini "YYYY-MM-DD" olarak döner.
 * @param {Date} [date] Test için tarih enjekte edilebilir.
 */
function todayISO(date = new Date()) {
  // en-CA yerel biçimi zaten YYYY-MM-DD üretir.
  return new Intl.DateTimeFormat('en-CA', {
    timeZone: config.timezone,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).format(date);
}

/**
 * Verilen ISO tarihe gün ekler ve yine "YYYY-MM-DD" döner.
 *
 * Hesap UTC öğlen üzerinden yapılır: yaz saati geçişlerinde gün kaymasın diye
 * (gece yarısına yakın bir saatte +1 gün eklemek DST'de aynı güne düşebilir).
 *
 * @param {string} isoDate 'YYYY-MM-DD'
 * @param {number} days Eklenecek gün sayısı (negatif olabilir).
 */
function addDays(isoDate, days) {
  const base = new Date(`${isoDate}T12:00:00Z`);
  base.setUTCDate(base.getUTCDate() + days);
  return base.toISOString().slice(0, 10);
}

/**
 * Ofis saat diliminde şu anki saati "HH:MM" olarak döner.
 */
function nowHHMM(date = new Date()) {
  return new Intl.DateTimeFormat('tr-TR', {
    timeZone: config.timezone,
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  }).format(date);
}

/**
 * "YYYY-MM-DD" değerini okunabilir Türkçe tarihe çevirir.
 * Örn: "2026-07-17" -> "17 Temmuz 2026 Cuma"
 */
function formatLongTR(isoDate) {
  // Saat bileşeni ekleyip UTC olarak yorumlatıyoruz ki gün kayması olmasın.
  const date = new Date(`${isoDate}T12:00:00Z`);
  return new Intl.DateTimeFormat('tr-TR', {
    timeZone: config.timezone,
    day: 'numeric',
    month: 'long',
    year: 'numeric',
    weekday: 'long',
  }).format(date);
}

/**
 * "YYYY-MM-DD" -> "17.07.2026"
 */
function formatShortTR(isoDate) {
  const date = new Date(`${isoDate}T12:00:00Z`);
  return new Intl.DateTimeFormat('tr-TR', {
    timeZone: config.timezone,
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  }).format(date);
}

/** Verilen ISO tarihi bugün mü? */
function isToday(isoDate) {
  return isoDate === todayISO();
}

module.exports = { todayISO, addDays, nowHHMM, formatLongTR, formatShortTR, isToday };
