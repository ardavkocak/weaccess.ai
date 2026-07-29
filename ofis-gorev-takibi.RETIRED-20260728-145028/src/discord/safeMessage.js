'use strict';

/**
 * Mesaj düzenleme/yeniden-oluşturma için TEK merkezi yardımcı.
 *
 * NEDEN GEREKLİ?
 * --------------
 * Saklanan bir `channel_id`/`message_id` çifti her zaman GEÇERLİ olmayabilir:
 * mesaj elle silinmiş olabilir, kanal değişmiş olabilir, ya da (nadiren) bir
 * interaction'ın arkasındaki mesaj tam o anda silinmiş olabilir. Bu durumda
 * Discord "Unknown Message" (404) döner. Kullanıcıya asla 404 sızdırılmamalı:
 * ESKİ message_id KULLANILMAYA DEVAM EDİLMEMELİ, otomatik olarak YENİ bir
 * mesaj oluşturulmalı ve veritabanı güncellenmelidir.
 *
 * Bu mantık daha önce yalnızca `dutyConfirmation.service.startFlow()` içinde,
 * tek bir yerde vardı; buton-tıklama yolunda (interaction.editReply 404
 * verirse) hiç yoktu. Artık HER İKİ yol da bu tek fonksiyonu kullanır — kod
 * tekrarı kalkar, davranış tek yerden garanti edilir.
 */

const bot = require('./bot');
const log = require('../utils/logger').create('safe-msg');

/**
 * Var olan bir mesajı düzenlemeyi dener; başarısız olursa (silinmiş, kanal
 * değişmiş vb.) aynı kanala YENİ bir mesaj gönderir.
 *
 * @param {object} p
 * @param {'duty'|'meal'} p.channelKey  Yeniden oluşturma durumunda hangi kanala gidileceği.
 * @param {string|null} p.channelId     Saklı kanal ID'si (varsa).
 * @param {string|null} p.messageId     Saklı mesaj ID'si (varsa).
 * @param {string} p.content
 * @param {import('discord.js').ActionRowBuilder[]} p.components
 * @returns {Promise<{ ok: boolean, message: string, recreated: boolean, channelId?: string, messageId?: string }>}
 */
async function editOrRecreate({ channelKey, channelId, messageId, content, components }) {
  if (channelId && messageId) {
    const edited = await bot.editInteractive(channelId, messageId, content, components);
    if (edited.ok) {
      return { ok: true, message: edited.message, recreated: false, channelId, messageId };
    }
    log.warn(`Mesaj düzenlenemedi (${channelId}/${messageId}): ${edited.message} — yeni mesaj gönderiliyor.`);
  } else {
    log.warn(`Saklı channel_id/message_id yok (${channelKey}) — yeni mesaj gönderiliyor.`);
  }

  const sent = await bot.sendInteractive(channelKey, content, components);
  if (!sent.ok) {
    return { ok: false, message: sent.message, recreated: false };
  }

  return {
    ok: true,
    message: 'Eski mesaj bulunamadığı için yeni mesaj gönderildi.',
    recreated: true,
    channelId: sent.channelId,
    messageId: sent.messageId,
  };
}

module.exports = { editOrRecreate };
