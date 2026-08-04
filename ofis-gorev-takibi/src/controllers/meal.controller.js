'use strict';

/** Yemek Menüsü sayfası — Excel yükleme, menü görüntüleme/silme, test gönderimi. */

const mealMenuService = require('../services/mealMenu.service');
const mealVoteService = require('../services/mealVote.service');
const mealImportService = require('../services/mealImport.service');
const settingsService = require('../services/settings.service');
const scheduledMessageService = require('../services/scheduledMessage.service');
const mealScheduler = require('../cron/mealScheduler');
const bot = require('../discord/bot');
const { asyncHandler } = require('../middleware/errorHandler');
const { MAX_FILE_SIZE } = require('../middleware/upload');
const { formatLongTR } = require('../utils/date');
const log = require('../utils/logger').create('meal');

/** Sayfayı render eden ortak yardımcı (hata sonrası da aynı görünüm kullanılır). */
function renderPage(req, res, { errors = [], importReport = null, status = 200 } = {}) {
  const tomorrowDate = mealMenuService.nextMenuDateISO();
  const tomorrow = mealMenuService.getByDate(tomorrowDate);

  return res.status(status).render('pages/meal', {
    pageTitle: 'Yemek Menüsü',
    activeNav: 'meal',
    summary: mealMenuService.getSummary(),
    // Liste: bugünden itibaren; geçmiş menüler paneli doldurmasın.
    menus: mealMenuService.list({ upcomingOnly: true }),
    tomorrow,
    tomorrowDate,
    tomorrowLong: formatLongTR(tomorrowDate),
    // Katılım dökümü: kartlar ve üç liste (yiyecek / yemeyecek / cevapsız).
    // Aynı veri `/yemek-menusu/katilim.json` ile canlı tazelenir.
    participation: mealVoteService.getParticipation(tomorrowDate),
    schedulerStatus: mealScheduler.getStatus(),
    notifyTime: mealScheduler.getTime(),
    tokenIsSet: settingsService.isSet('discord_bot_token'),
    channelIsSet: settingsService.isSet('discord_meal_channel_id'),
    botStatus: bot.getStatus(),
    maxFileSizeMb: MAX_FILE_SIZE / 1024 / 1024,
    // Son yükleme raporu (kaç satır okundu, hangi sütunlar eşleşti).
    importReport,
    formErrors: errors,
  });
}

/** GET /yemek-menusu */
function showMeals(req, res) {
  return renderPage(req, res);
}

/**
 * POST /yemek-menusu/yukle — Excel dosyasını okur ve veritabanına aktarır.
 *
 * Excel YALNIZCA burada okunur. Sonrasında sistemin hiçbir yeri dosyaya
 * dokunmaz; duyurular ve panel hep `meal_menus` tablosundan beslenir.
 */
const uploadMenu = asyncHandler(async (req, res) => {
  // multer'ın ürettiği kullanıcı dostu hata (boyut/tür) varsa önce onu göster.
  if (req.uploadError) {
    return renderPage(req, res, { errors: [req.uploadError], status: 400 });
  }
  if (!req.file) {
    return renderPage(req, res, { errors: ['Lütfen bir .xlsx dosyası seçin.'], status: 400 });
  }

  const parsed = await mealImportService.parseBuffer(req.file.buffer);

  if (!parsed.ok) {
    log.warn(`Excel okunamadı (${req.file.originalname}): ${parsed.message}`);
    return renderPage(req, res, {
      errors: [parsed.message, ...parsed.warnings],
      status: 400,
    });
  }

  // "Tümünü değiştir" işaretliyse eski menüler silinir; değilse aynı tarihler
  // güncellenip yeni tarihler eklenir (ay ortası düzeltmeleri için).
  const replaceAll = req.body?.replace_all === 'on';

  const result = mealMenuService.saveRows(parsed.rows, {
    sourceFile: req.file.originalname,
    replaceAll,
  });

  log.info(
    `Yemek menüsü yüklendi (${req.file.originalname}): ` +
    `${result.inserted} yeni, ${result.updated} güncellendi, ${result.removed} silindi.`
  );

  req.flash('success',
    `"${req.file.originalname}" işlendi: ${result.inserted} yeni kayıt, ` +
    `${result.updated} güncelleme${result.removed ? `, ${result.removed} eski kayıt silindi` : ''}.`
  );

  // Rapor: hangi satır başlıktı, hangi sütunlar neye eşlendi, kaç satır atlandı.
  // Sütun eşleştirme ekranı eklenirse bu rapor onun veri kaynağıdır.
  return renderPage(req, res, {
    importReport: {
      fileName: req.file.originalname,
      sheetName: parsed.sheetName,
      rowCount: parsed.rows.length,
      skipped: parsed.skipped,
      // Biçime özgü ayrıntılar (blok / düz tablo) hazır etiket-değer listesi
      // olarak gelir; görünüm biçim bilmek zorunda kalmaz.
      details: parsed.details ?? [],
      warnings: parsed.warnings,
    },
  });
});

/**
 * GET /yemek-menusu/katilim.json — katılım verisinin canlı hâli.
 *
 * Panel bu uç noktayı belirli aralıklarla çağırıp kartları ve listeleri
 * tazeler; Discord'da butona basıldığı anda sayfa yenilenmeden güncellenir.
 * Sayfanın kendisiyle AYNI servisten beslenir, böylece iki farklı doğruluk
 * kaynağı oluşmaz.
 */
function participationJson(req, res) {
  const date = String(req.query.tarih ?? mealMenuService.nextMenuDateISO());
  return res.json({ date, ...mealVoteService.getParticipation(date) });
}

/** POST /yemek-menusu/sil — tüm menüleri siler. */
function removeAll(req, res) {
  const removed = mealMenuService.removeAll();

  // Oylar bilerek korunur (bkz. mealMenu.service.removeAll). Admin isterse
  // ayrıca "oyları sıfırla" ile temizler.
  log.warn(`Tüm yemek menüsü silindi (${removed} kayıt).`);
  req.flash(removed > 0 ? 'success' : 'info',
    removed > 0 ? `${removed} günlük menü kaydı silindi.` : 'Silinecek menü kaydı yoktu.');

  return res.redirect('/yemek-menusu');
}

/** POST /yemek-menusu/:date/sil — tek bir günün menüsünü siler. */
function removeOne(req, res) {
  const date = String(req.params.date);
  const removed = mealMenuService.removeByDate(date);

  req.flash(removed ? 'success' : 'error',
    removed ? `${formatLongTR(date)} menüsü silindi.` : 'Silinecek kayıt bulunamadı.');

  return res.redirect('/yemek-menusu');
}

/** POST /yemek-menusu/oylari-sifirla — yarının oylarını temizler. */
function resetVotes(req, res) {
  const date = String(req.body.date ?? mealMenuService.nextMenuDateISO());
  const removed = mealVoteService.removeByDate(date);

  log.info(`Yemek oyları sıfırlandı (${date}): ${removed} oy silindi.`);
  req.flash('success', `${formatLongTR(date)} için ${removed} oy silindi.`);

  return res.redirect('/yemek-menusu');
}

/**
 * POST /yemek-menusu/gonder — "Yarının Menüsünü Şimdi Gönder" (test).
 * Cron saatini beklemez ve "zaten duyuruldu" kontrolünü atlar.
 */
const sendNow = asyncHandler(async (req, res) => {
  const result = await mealScheduler.triggerNow();

  // Menü bulunamaması bir hata değildir; bilgi olarak gösterilir.
  const type = result.ok ? (result.skipped ? 'info' : 'success') : 'error';
  req.flash(type, result.message);

  return res.redirect('/yemek-menusu');
});

/** POST /yemek-menusu/saat — duyuru saatini günceller ve cron'u yeniden kurar. */
function updateTime(req, res) {
  const time = String(req.body.meal_notify_time ?? '').trim();

  if (!scheduledMessageService.isValidTime(time)) {
    return renderPage(req, res, {
      errors: [`Geçersiz saat: ${time || '(boş)'}. SS:DD biçiminde olmalıdır.`],
      status: 400,
    });
  }

  settingsService.set('meal_notify_time', time);
  const result = mealScheduler.reschedule();

  log.info(`Yemek duyuru saati güncellendi: ${time}`);
  req.flash(result.ok ? 'success' : 'error',
    result.ok ? `Duyuru saati ${time} olarak güncellendi.` : result.message);

  return res.redirect('/yemek-menusu');
}

module.exports = {
  showMeals,
  participationJson,
  uploadMenu,
  removeAll,
  removeOne,
  resetVotes,
  sendNow,
  updateTime,
};
