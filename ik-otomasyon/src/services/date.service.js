'use strict';

/** Yerel tarih için saat dilimi kayması yaşamayan yardımcılar. */
function toISODate(date) {
  return [date.getFullYear(), String(date.getMonth() + 1).padStart(2, '0'), String(date.getDate()).padStart(2, '0')].join('-');
}

function fromISODate(iso) {
  const [year, month, day] = iso.split('-').map(Number);
  return new Date(year, month - 1, day, 12);
}

function addDays(date, amount) {
  const result = new Date(date);
  result.setDate(result.getDate() + amount);
  return result;
}

/** Belirtilen ayın son cuma günü. month: 0-11 */
function lastFriday(year, month) {
  const lastDay = new Date(year, month + 1, 0, 12);
  const daysSinceFriday = (lastDay.getDay() - 5 + 7) % 7;
  return addDays(lastDay, -daysSinceFriday);
}

/** Hafta sonuna düşen gönderim tarihini önceki cumaya çeker. */
function moveWeekendReminderToFriday(date) {
  if (date.getDay() === 6) return addDays(date, -1);
  if (date.getDay() === 0) return addDays(date, -2);
  return date;
}

function birthdayReminderDate(year, month) {
  return moveWeekendReminderToFriday(addDays(lastFriday(year, month), -2));
}

function anniversaryDate(hireDate, year) {
  const result = new Date(year, hireDate.getMonth(), hireDate.getDate(), 12);
  // 29 Şubat işe girişinde, artık olmayan yıllarda 28 Şubat kabul edilir.
  if (hireDate.getMonth() === 1 && hireDate.getDate() === 29 && result.getMonth() !== 1) {
    return new Date(year, 1, 28, 12);
  }
  return result;
}

function anniversaryReminderDate(anniversary) {
  return moveWeekendReminderToFriday(addDays(anniversary, -2));
}

module.exports = {
  toISODate, fromISODate, addDays, lastFriday, birthdayReminderDate,
  anniversaryDate, anniversaryReminderDate,
};
