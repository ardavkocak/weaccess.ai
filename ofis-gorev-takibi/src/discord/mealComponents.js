'use strict';

/**
 * Yemek katılım butonları.
 *
 * customId FORMATI:  mv:<menuDate>:<y|n>
 *   mv        : yemek oylaması öneki (görev onayının "dc" önekinden ayrıdır)
 *   menuDate  : 'YYYY-MM-DD' — oyun hangi güne ait olduğu
 *   y | n     : yiyeceğim / yemeyeceğim
 *
 * NEDEN TARİH, ID DEĞİL?
 * ----------------------
 * Görev onayında customId satır id'si taşır ve veritabanı değişirse (farklı
 * kurulum, sıfırlama) buton bir daha eşleşmez. Burada anahtar olarak TARİH
 * kullanılır: tarih evrenseldir, veritabanından bağımsızdır. Menü yeniden
 * yüklense veya sunucu yeniden başlasa bile eski mesajın butonları doğru güne
 * oy yazmaya devam eder.
 */

const { ButtonBuilder, ButtonStyle, ActionRowBuilder } = require('discord.js');

const CUSTOM_ID_PREFIX = 'mv';

/**
 * Katılım butonlarını üretir.
 *
 * @param {string} menuDate 'YYYY-MM-DD'
 * @param {object} [opts]
 * @param {boolean} [opts.disabled] Oylama kapandığında pasifleştirmek için.
 * @returns {ActionRowBuilder[]}
 */
function buildVoteButtons(menuDate, { disabled = false } = {}) {
  const yes = new ButtonBuilder()
    .setCustomId(`${CUSTOM_ID_PREFIX}:${menuDate}:y`)
    .setLabel('Yiyeceğim')
    .setEmoji('🟢')
    .setStyle(ButtonStyle.Success)
    .setDisabled(disabled);

  const no = new ButtonBuilder()
    .setCustomId(`${CUSTOM_ID_PREFIX}:${menuDate}:n`)
    .setLabel('Yemeyeceğim')
    .setEmoji('🔴')
    .setStyle(ButtonStyle.Danger)
    .setDisabled(disabled);

  return [new ActionRowBuilder().addComponents(yes, no)];
}

/**
 * customId'yi çözümler.
 * @returns {{ menuDate: string, choice: 'yes'|'no' }|null}
 */
function parseCustomId(customId) {
  const parts = String(customId ?? '').split(':');
  if (parts.length !== 3 || parts[0] !== CUSTOM_ID_PREFIX) return null;

  const menuDate = parts[1];
  const code = parts[2];

  if (!/^\d{4}-\d{2}-\d{2}$/.test(menuDate)) return null;
  if (code !== 'y' && code !== 'n') return null;

  return { menuDate, choice: code === 'y' ? 'yes' : 'no' };
}

/** Bu modüle ait bir buton mu? (bot.js yönlendirmesi için) */
function isOwnCustomId(customId) {
  return String(customId ?? '').startsWith(`${CUSTOM_ID_PREFIX}:`);
}

module.exports = { buildVoteButtons, parseCustomId, isOwnCustomId, CUSTOM_ID_PREFIX };
