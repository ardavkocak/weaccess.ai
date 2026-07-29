'use strict';

/**
 * Yemek bildirim servisi (mealNotifier) — menüyü Discord'a gönderir, oyları işler.
 *
 * Görev tarafındaki `dutyNotifier.service.js`in yemek karşılığıdır: her sistemin
 * kendi bildirim servisi vardır, ikisi birbirini çağırmaz.
 *
 * AKIŞ
 * ----
 *   15:00 (cron)  → announceTomorrow({ source: 'cron' })
 *                   • Yarının menüsü VARSA YEMEK kanalına butonlu mesaj gider.
 *                   • YOKSA hiçbir mesaj gönderilmez; log'a bilgi yazılır ve
 *                     uygulama normal çalışmaya devam eder.
 *   Buton tıklaması → onButton()
 *                   • Oy senkron olarak kaydedilir/değiştirilir.
 *                   • Mesaj güncel SAYILARLA yeniden yazılır (isim listesi yok).
 *                   • Oy verene yalnızca kendisinin gördüğü bir onay gönderilir.
 *
 * KANAL AYRIMI
 * ------------
 * Bu servis yalnızca 'meal' kanalına yazar; görev mesajları 'duty' kanalına
 * gider. Kanal `bot.sendInteractive()` çağrısında açıkça belirtilir.
 *
 * BAĞIMSIZLIK
 * -----------
 * Servis GÖREV TAKİBİNDEN tamamen bağımsızdır: rotasyona, görev geçmişine ya da
 * onay akışına hiçbir noktada dokunmaz. Buradaki bir hata görev sistemini
 * etkilemez (cron işleri ayrıdır, buton yönlendirmesi customId önekiyle ayrılır).
 */

const bot = require('../discord/bot');
const dbRetry = require('../database/dbRetry');
const mealMenuService = require('./mealMenu.service');
const mealVoteService = require('./mealVote.service');
const { renderAnnouncement, renderCounts, COUNTS_HEADING } = require('../discord/mealMessages');
const { buildVoteButtons } = require('../discord/mealComponents');
const { formatLongTR } = require('../utils/date');
const log = require('../utils/logger').create('meal');

/**
 * Yarının menüsünü kanala duyurur.
 *
 * @param {object} [options]
 * @param {'cron'|'manual'} [options.source] Kaynak; yalnızca log ve idempotens için.
 * @param {boolean} [options.force] true ise "zaten duyuruldu" kontrolü atlanır
 *   (panelin "Şimdi Gönder" test butonu bunu kullanır).
 * @returns {Promise<{ ok: boolean, skipped?: boolean, message: string }>}
 *   Hata FIRLATMAZ; cron her koşulda çalışmaya devam eder.
 */
async function announceTomorrow({ source = 'cron', force = false } = {}) {
  // Duyurulan menü SONRAKİ İŞ GÜNÜNÜNKİDİR: Cuma günü Pazartesi menüsü gönderilir
  // (hafta sonu atlanır). Hafta içi bu "yarın" ile aynıdır.
  const menuDate = mealMenuService.nextMenuDateISO();
  const menu = mealMenuService.getByDate(menuDate);

  // Menü yoksa Discord'a HİÇBİR mesaj gitmez — istenen davranış budur.
  if (!menu) {
    log.info(`Sonraki iş günü (${menuDate}) için yemek menüsü bulunamadı.`);
    return {
      ok: true,
      skipped: true,
      message: `${formatLongTR(menuDate)} için menü bulunamadı; mesaj gönderilmedi.`,
    };
  }

  // Cron gün içinde iki kez tetiklenirse (yeniden başlatma, saat değişikliği)
  // aynı menü ikinci kez duyurulmasın. Elle gönderimde bu kontrol atlanır.
  if (!force && menu.announced_at) {
    log.info(`Menü zaten duyurulmuş (${menuDate}); tekrar gönderilmedi.`);
    return { ok: true, skipped: true, message: 'Bu menü bugün zaten duyuruldu.' };
  }

  const content = renderAnnouncement({ menu, counts: mealVoteService.getCounts(menuDate) });
  // Yemek duyurusu her zaman YEMEK kanalına gider (görev kanalına değil).
  const sent = await bot.sendInteractive('meal', content, buildVoteButtons(menuDate));

  if (!sent.ok) {
    log.error(`Yemek menüsü gönderilemedi (${menuDate}): ${sent.message}`);
    return { ok: false, message: `Yemek menüsü gönderilemedi: ${sent.message}` };
  }

  mealMenuService.markAnnounced(menuDate);
  log.info(`Yemek menüsü duyuruldu (${menuDate}, ${menu.items.length} yemek, kaynak: ${source}).`);

  return { ok: true, message: `${formatLongTR(menuDate)} menüsü Discord kanalına gönderildi.` };
}

/**
 * Menü kaydı silinmişse mesajın tamamı yeniden üretilemez; bu durumda mevcut
 * metnin yalnızca KATILIM BLOĞU tazelenir. Böylece eski bir duyurunun butonları
 * menü silinse bile çalışmaya ve sayaçları güncellemeye devam eder.
 */
function refreshCountsBlock(existingContent, counts) {
  const text = String(existingContent ?? '');
  const index = text.indexOf(COUNTS_HEADING);

  // Blok yoksa (çok eski bir mesaj) sona eklenir.
  if (index === -1) return `${text}\n\n${renderCounts(counts)}`;

  return `${text.slice(0, index)}${renderCounts(counts)}`;
}

/**
 * `interaction.followUp()`'ı güvenli biçimde çağırır (ephemeral bildirimler için).
 */
async function safeFollowUp(interaction, payload) {
  try {
    await interaction.followUp(payload);
  } catch (error) {
    log.error('interaction.followUp başarısız', error);
  }
}

/**
 * Katılım butonu tıklamasının İŞ MANTIĞI kısmı.
 *
 * ÖNEMLİ MİMARİ KURAL: Bu fonksiyon yalnızca `discord/interactionRouter.js`
 * tarafından, Discord'a İLK yanıt (`interaction.deferUpdate()`) ZATEN
 * gönderildikten SONRA çağrılır — bkz. dutyConfirmation.service.handleDeferredButton
 * başındaki aynı notla. `castVote`'un SQLite transaction'ı `dbRetry.withRetry`
 * ile sarmalanır; bu sayede DB gecikmesi Discord'un 3sn yanıt penceresini
 * hiçbir zaman tehdit etmez.
 *
 * @param {import('discord.js').ButtonInteraction} interaction Zaten deferUpdate() yapılmış.
 * @param {{menuDate: string, choice: 'yes'|'no'}} parsed
 * @param {ReturnType<typeof import('../discord/interactionLog').start>} [ilog]
 */
async function handleDeferredButton(interaction, parsed, ilog = null) {
  const userId = interaction.user?.id;
  if (!userId) return;

  const userName = interaction.member?.displayName ?? interaction.user?.username ?? null;

  let result;
  try {
    result = await dbRetry.withRetry(() => mealVoteService.castVote({
      menuDate: parsed.menuDate, userId, userName, choice: parsed.choice,
    }), { label: 'castVote' });
    ilog?.step('db-bitti');
  } catch (error) {
    log.error('Oy kaydedilemedi (castVote, tüm denemeler tükendi)', error);
    await safeFollowUp(interaction, {
      content: 'Bir hata oluştu, lütfen birkaç saniye sonra tekrar deneyin.',
      ephemeral: true,
    });
    ilog?.step('hata-yaniti-gonderildi');
    return;
  }

  // Anket kapanmış (gün geçmiş): oy kaydedilmedi, kullanıcıya açıkça söylenir.
  if (result.closed) {
    await safeFollowUp(interaction, { content: 'Bu anket kapandı, artık oy kullanılamaz.', ephemeral: true });
    ilog?.step('kapali-yaniti-gonderildi');
    return;
  }

  // Aynı tercihe tekrar basıldı: veritabanında değişen bir şey yok. Router
  // zaten deferUpdate() ile etkileşimi sessizce kapattı; burada ekstra bir
  // Discord çağrısına gerek yok.
  if (!result.changed) {
    ilog?.step('degisiklik-yok');
    return;
  }

  const counts = mealVoteService.getCounts(parsed.menuDate);
  const menu = mealMenuService.getByDate(parsed.menuDate);
  const content = menu
    ? renderAnnouncement({ menu, counts })
    : refreshCountsBlock(interaction.message?.content, counts);

  try {
    await interaction.editReply({ content, components: buildVoteButtons(parsed.menuDate) });
    ilog?.step('discord-guncellendi');
  } catch (error) {
    log.error('Yemek mesajı güncellenemedi (editReply) — muhtemelen mesaj silinmiş', error);
    // Yemek duyurusunun message_id'si veritabanında saklanmadığı için (şema
    // değişikliği gerektirmeden) otomatik yeniden oluşturma yapılamaz; oy
    // yine de kaydedilmiş olduğundan (üstteki castVote) veri kaybı yoktur —
    // yalnızca kanaldaki sayaç görünümü bir sonraki oya kadar eski kalır.
    await safeFollowUp(interaction, {
      content: 'Oyunuz kaydedildi, ancak mesaj güncellenemedi (mesaj silinmiş olabilir).',
      ephemeral: true,
    });
    ilog?.step('kurtarma-yaniti-gonderildi');
  }

  log.debug(
    `Yemek oyu (${parsed.menuDate}): ${userName ?? userId} → ${parsed.choice}` +
    `${result.previous ? ` (önceki: ${result.previous})` : ''}`
  );
}

module.exports = { announceTomorrow, handleDeferredButton, refreshCountsBlock };
