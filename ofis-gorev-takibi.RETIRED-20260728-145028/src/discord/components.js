'use strict';

/**
 * Discord etkileşim bileşenleri (butonlar).
 *
 * Etkileşimli sabah görev onayında kullanılan "✅ Evet / ❌ Hayır" butonlarını
 * üretir. discord.js v14'ün ButtonBuilder + ActionRowBuilder yapıları kullanılır.
 *
 * customId FORMATI:  dc:<flowId>:<step>:<y|n>
 *   dc      : bu uygulamanın buton öneki (interactionCreate bununla filtreler)
 *   flowId  : duty_confirmations.id — akışı veritabanından bulmak için
 *   step    : akıştaki adım — bayat (eski) buton tıklamalarını reddetmek için
 *   y | n   : cevap (evet / hayır)
 *
 * step alanı kritik: aynı mesaj her "Hayır"da düzenlenip yeni step'li butonlarla
 * güncellenir. Böylece eski butonların customId'si artık geçerli step'i
 * göstermez; bir kullanıcı önbelleğe alınmış eski bir butona bassa bile servis
 * "bu soru zaten yanıtlandı" diyerek reddeder.
 */

const { ButtonBuilder, ButtonStyle, ActionRowBuilder } = require('discord.js');

const CUSTOM_ID_PREFIX = 'dc';

/**
 * Onay butonlarını üretir.
 *
 * @param {number} flowId  duty_confirmations.id
 * @param {number} step    geçerli adım
 * @param {object} [opts]
 * @param {boolean} [opts.disabled] Butonları pasif göster (akış bittiğinde).
 * @returns {ActionRowBuilder[]}
 */
function buildConfirmButtons(flowId, step, { disabled = false } = {}) {
  const yes = new ButtonBuilder()
    .setCustomId(`${CUSTOM_ID_PREFIX}:${flowId}:${step}:y`)
    .setLabel('Evet')
    .setEmoji('✅')
    .setStyle(ButtonStyle.Success)
    .setDisabled(disabled);

  const no = new ButtonBuilder()
    .setCustomId(`${CUSTOM_ID_PREFIX}:${flowId}:${step}:n`)
    .setLabel('Hayır')
    .setEmoji('❌')
    .setStyle(ButtonStyle.Danger)
    .setDisabled(disabled);

  return [new ActionRowBuilder().addComponents(yes, no)];
}

/**
 * customId'yi çözümler.
 * @param {string} customId
 * @returns {{ flowId: number, step: number, answer: 'yes'|'no' }|null}
 */
function parseCustomId(customId) {
  const parts = String(customId ?? '').split(':');
  if (parts.length !== 4 || parts[0] !== CUSTOM_ID_PREFIX) return null;

  const flowId = Number(parts[1]);
  const step = Number(parts[2]);
  const answerCode = parts[3];

  if (!Number.isInteger(flowId) || !Number.isInteger(step)) return null;
  if (answerCode !== 'y' && answerCode !== 'n') return null;

  return { flowId, step, answer: answerCode === 'y' ? 'yes' : 'no' };
}

/** Bu uygulamaya ait bir buton customId'si mi? */
function isOwnCustomId(customId) {
  return String(customId ?? '').startsWith(`${CUSTOM_ID_PREFIX}:`);
}

module.exports = { buildConfirmButtons, parseCustomId, isOwnCustomId, CUSTOM_ID_PREFIX };
