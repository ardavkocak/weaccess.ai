'use strict';

/**
 * Discord `interactionCreate` olayının TEK giriş noktası.
 *
 * MİMARİ KURAL (ihlal edilemez): Bu dosyadaki `handleInteraction`, Discord'a
 * İLK yanıtı (`interaction.deferUpdate()`) HER ZAMAN ilk satırlarda, hiçbir
 * SQL/Discord API/iş mantığı çağrısından ÖNCE gönderir. Bunun nedeni: Discord
 * bir interaction'ı yalnızca 3 saniye içinde onaylanırsa geçerli sayar; bu süre
 * aşılırsa etkileşim sunucu tarafında "expired" olur ve o andan sonraki HİÇBİR
 * yanıt (update/reply/editReply) işe yaramaz — kullanıcı "Uygulama zamanında
 * yanıt vermedi" görür. `deferUpdate()` başka hiçbir I/O gerektirmediği için
 * (SQL yok, HTTP yok) neredeyse her zaman birkaç ms içinde tamamlanır; bu da
 * DB gecikmesini (kilit çakışması dahil) ve iş mantığını Discord'un 3sn'lik
 * penceresinden TAMAMEN çıkarır — sonraki her şey `editReply`/`followUp` ile
 * yapılır ve bunların süre sınırı ~15 dakikadır.
 *
 * Ayrıca burada:
 *   - Tekillik (idempotency) koruması: aynı interaction.id iki kez işlenmez.
 *   - Modül yönlendirmesi: customId önekine göre (dc: / mv:) ilgili servise
 *     gider; her modülün İŞ MANTIĞI kendi dosyasında kalır (bkz.
 *     dutyConfirmation.service.handleDeferredButton, mealNotifier.service.handleDeferredButton).
 *   - Son güvenlik ağı: servis katmanı beklenmedik bir istisna fırlatırsa bile
 *     kullanıcı yanıtsız bırakılmaz.
 *   - Her interaction için baştan sona zaman damgalı debug günlüğü.
 */

const idempotencyGuard = require('./idempotencyGuard');
const interactionLog = require('./interactionLog');
const { isOwnCustomId: isDutyCustomId, parseCustomId: parseDutyCustomId } = require('./components');
const { isOwnCustomId: isMealCustomId, parseCustomId: parseMealCustomId } = require('./mealComponents');
const log = require('../utils/logger').create('interaction-router');

/**
 * @param {import('discord.js').Interaction} interaction
 */
async function handleInteraction(interaction) {
  if (!interaction.isButton?.()) return;

  const customId = interaction.customId;
  const isDuty = isDutyCustomId(customId);
  const isMeal = !isDuty && isMealCustomId(customId);
  if (!isDuty && !isMeal) return; // Bize ait bir buton değil.

  // Aynı interaction'ın iki kez işlenmesini engelle (Gateway'in nadiren aynı
  // olayı tekrar teslim etmesi ya da olası bir çağıran hatası ihtimaline karşı).
  if (idempotencyGuard.alreadySeen(interaction.id)) {
    log.warn(`Interaction ${interaction.id} zaten işlendi/işleniyor, atlandı (customId=${customId}).`);
    return;
  }

  const moduleName = isDuty ? 'duty' : 'meal';
  const ilog = interactionLog.start(interaction, { module: moduleName });

  // 1) HER ŞEYDEN ÖNCE: hemen deferUpdate(). Önüne hiçbir şey geçmez.
  try {
    await interaction.deferUpdate();
    ilog.step('deferUpdate');
  } catch (error) {
    // Bu noktada başarısızlık pratikte yalnızca ağ/Discord kaynaklı olabilir
    // (kod burada henüz hiçbir I/O yapmadı); yapacak başka bir şey yok.
    ilog.finish({ ok: false, error });
    return;
  }

  // 2) Etkileşim güvenceye alındıktan SONRA iş mantığı çalışır.
  try {
    if (isDuty) {
      const parsed = parseDutyCustomId(customId);
      if (!parsed) { ilog.finish({ ok: true }); return; }
      // Lazy require: döngüsel bağımlılığı önler (service → bot.js → ...).
      const dutyConfirmationService = require('../services/dutyConfirmation.service');
      await dutyConfirmationService.handleDeferredButton(interaction, parsed, ilog);
    } else {
      const parsed = parseMealCustomId(customId);
      if (!parsed) { ilog.finish({ ok: true }); return; }
      const mealNotifierService = require('../services/mealNotifier.service');
      await mealNotifierService.handleDeferredButton(interaction, parsed, ilog);
    }
    ilog.finish({ ok: true });
  } catch (error) {
    // SON GÜVENLİK AĞI. Servis fonksiyonları kendi hatalarını zaten yakalayıp
    // editReply/followUp ile kullanıcıya haber veriyor; ama beklenmedik bir
    // istisna (örn. bir programlama hatası) buraya sızarsa bile kullanıcı
    // yanıtsız bırakılmamalı — deferUpdate() ZATEN yapıldığı için editReply
    // burada güvenle denenebilir.
    log.error(`Beklenmeyen hata (${moduleName}, customId=${customId})`, error);
    try {
      await interaction.editReply({ content: 'Beklenmeyen bir hata oluştu. Lütfen tekrar deneyin.', components: [] });
    } catch (fallbackError) {
      log.error('Son güvenlik ağı editReply de başarısız', fallbackError);
    }
    ilog.finish({ ok: false, error });
  }
}

module.exports = { handleInteraction };
