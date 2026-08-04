'use strict';

/**
 * Görünüm (EJS) yardımcıları.
 * `middleware/locals.js` üzerinden tüm şablonlara aktarılır.
 */

/**
 * İsimden baş harfleri üretir (avatar dairesi için).
 * "Beril Kahramanca" -> "BK"
 */
function initials(fullName) {
  const parts = String(fullName ?? '').trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return '?';
  if (parts.length === 1) return parts[0].slice(0, 2).toLocaleUpperCase('tr-TR');
  return (parts[0][0] + parts[parts.length - 1][0]).toLocaleUpperCase('tr-TR');
}

/**
 * İsimden sabit bir renk seçer; aynı kişi her sayfada aynı rengi alır.
 * Rastgele değil deterministik olması, arayüzün "titremesini" önler.
 */
const AVATAR_COLORS = [
  'bg-indigo-500', 'bg-emerald-500', 'bg-amber-500', 'bg-rose-500',
  'bg-sky-500', 'bg-violet-500', 'bg-teal-500', 'bg-orange-500',
];

function avatarColor(fullName) {
  const text = String(fullName ?? '');
  let hash = 0;
  for (let i = 0; i < text.length; i += 1) {
    hash = (hash * 31 + text.charCodeAt(i)) >>> 0;
  }
  return AVATAR_COLORS[hash % AVATAR_COLORS.length];
}

module.exports = { initials, avatarColor };
