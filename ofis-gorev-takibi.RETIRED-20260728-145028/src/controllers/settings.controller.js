'use strict';

/** Ayarlar — Discord bağlantısı, mesaj saatleri, şirket adı. */

const settingsService = require('../services/settings.service');
const adminAccount = require('../services/adminAccount.service');
const scheduledMessageService = require('../services/scheduledMessage.service');
const dutyService = require('../services/duty.service');
const scheduler = require('../cron/scheduler');
const bot = require('../discord/bot');
const { asyncHandler } = require('../middleware/errorHandler');
const { safeRedirect } = require('../utils/redirect');
const log = require('../utils/logger').create('settings');

/** Ayarlar sayfasını render eden ortak yardımcı. */
function renderSettings(req, res, { errors = [], values = null, status = 200 } = {}) {
  const masked = settingsService.getMaskedSettings();

  return res.status(status).render('pages/settings', {
    pageTitle: 'Ayarlar',
    activeNav: 'settings',
    // Token asla düz metin olarak arayüze gönderilmez; yalnızca maskeli hali
    // ve "tanımlı mı" bilgisi gider.
    settings: {
      company_name: values?.company_name ?? masked.company_name ?? '',
      discord_guild_id: values?.discord_guild_id ?? masked.discord_guild_id ?? '',
      // Görev ve yemek sistemleri ayrı kanallara yazar.
      discord_duty_channel_id: values?.discord_duty_channel_id ?? masked.discord_duty_channel_id ?? '',
      discord_meal_channel_id: values?.discord_meal_channel_id ?? masked.discord_meal_channel_id ?? '',
      discord_bot_token_masked: masked.discord_bot_token ?? '',
    },
    // Zamanlanmış mesajlar (saat + metin + etkinlik durumu formda düzenlenir).
    scheduledMessages: scheduledMessageService.getAll(),
    // Hata sonrası: admin'in yazdığı saat/metin kaybolmasın diye ham form verisi.
    // Boş nesne = "veritabanındaki değerleri göster".
    formValues: values ?? {},
    tokenIsSet: settingsService.isSet('discord_bot_token'),
    // Yönetici hesabı: parola ASLA (hash'i bile) görünüme gönderilmez.
    adminUsername: values?.admin_username ?? adminAccount.getUsername(),
    adminIsCustomized: adminAccount.isCustomized(),
    minPasswordLength: adminAccount.MIN_PASSWORD_LENGTH,
    schedulerStatus: scheduler.getStatus(),
    botStatus: bot.getStatus(),
    formErrors: errors,
  });
}

/** GET /ayarlar */
function showSettings(req, res) {
  return renderSettings(req, res);
}

/**
 * POST /ayarlar
 *
 * Tek form iki ayrı yeri günceller:
 *   - `settings` tablosu       → şirket adı, Discord kimlikleri
 *   - `scheduled_messages`     → her mesajın saati ve etkinliği
 *
 * İkisi de doğrulanır; herhangi birinde hata varsa HİÇBİRİ kaydedilmez ve
 * kullanıcı girdiği değerlerle birlikte forma geri döner.
 */
const updateSettings = asyncHandler(async (req, res) => {
  const previousToken = settingsService.get('discord_bot_token');

  // 1) ÖNCE her iki bölümü de doğrula, hiçbir şey yazma.
  //    Doğrularken yazsaydık, saatlerden biri geçersizken şirket adı çoktan
  //    kaydedilmiş olurdu; kullanıcı hata görürken veri kısmen değişirdi.
  const settingsResult = settingsService.validateSettings(req.body);
  const scheduleResult = scheduledMessageService.validateSchedule(req.body);
  const errors = [...settingsResult.errors, ...scheduleResult.errors];

  if (errors.length > 0) {
    return renderSettings(req, res, { errors, values: req.body, status: 400 });
  }

  // 2) İkisi de temiz: şimdi kaydet.
  settingsService.saveSettings(settingsResult.data);
  const schedule = scheduledMessageService.saveSchedule(scheduleResult.updates);

  const messages = ['Ayarlar kaydedildi.'];

  // Yalnızca saat/etkinlik değiştiyse cron işlerini yeniden kur (sunucu yeniden
  // başlatmadan). Metin değişikliği zamanlamayı etkilemez; yeni metin bir sonraki
  // gönderimde veritabanından okunur.
  if (schedule.timingChanged) {
    const result = scheduler.reschedule();
    messages.push(result.ok
      ? `Mesaj takvimi güncellendi (${result.scheduled} mesaj zamanlandı).`
      : `Zamanlayıcı uyarısı: ${result.errors.join(' ')}`);
  } else if (schedule.saved) {
    messages.push('Mesaj metinleri güncellendi.');
  }

  // Token değiştiyse bot bağlantısını yenile.
  const newToken = settingsService.get('discord_bot_token');
  if (newToken !== previousToken) {
    const result = await bot.reconnect();
    messages.push(result.ok ? 'Discord bağlantısı yenilendi.' : `Discord: ${result.message}`);
  }

  log.info('Ayarlar güncellendi.');
  req.flash('success', messages.join(' '));
  return res.redirect('/ayarlar');
});

/** POST /ayarlar/test — Discord bağlantısını sınar. */
const testDiscord = asyncHandler(async (req, res) => {
  const result = await bot.testConnection();
  req.flash(result.ok ? 'success' : 'error', result.message);
  return res.redirect('/ayarlar');
});

/**
 * POST /ayarlar/mesaj/:id/gonder — tek bir zamanlanmış mesajı elle gönderir.
 * Saati beklemeden Discord çıktısını görmek için.
 */
const sendMessageNow = asyncHandler(async (req, res) => {
  const result = await dutyService.sendMessageNow(Number(req.params.id));
  req.flash(result.ok ? 'success' : 'error', result.message);
  return res.redirect(safeRedirect(req.body.redirectTo, '/ayarlar'));
});

/**
 * POST /ayarlar/yonetici — yönetici kullanıcı adı / parolasını değiştirir.
 *
 * Mevcut parola her zaman sorulur (bkz. adminAccount.service.validateChange).
 * Parola alanı boş bırakılırsa yalnızca kullanıcı adı değişir.
 */
function updateAdminAccount(req, res) {
  const { errors, data } = adminAccount.validateChange(req.body);

  if (errors.length > 0) {
    // Parola alanları bilerek forma geri yazılmaz; yalnızca kullanıcı adı korunur.
    return renderSettings(req, res, {
      errors,
      values: { admin_username: String(req.body.admin_username ?? '').trim() },
      status: 400,
    });
  }

  const result = adminAccount.saveChange(data);

  const changed = [];
  if (result.usernameChanged) changed.push('kullanıcı adı');
  if (result.passwordChanged) changed.push('parola');

  log.info(`Yönetici hesabı güncellendi (${changed.join(' + ') || 'değişiklik yok'}).`);
  req.flash('success', changed.length > 0
    ? `Yönetici ${changed.join(' ve ')} güncellendi. Bir sonraki girişte yeni bilgileri kullanın.`
    : 'Yönetici bilgilerinde değişiklik yapılmadı.');

  return res.redirect('/ayarlar');
}

/** POST /ayarlar/token-sil — kayıtlı token'ı temizler. */
const clearToken = asyncHandler(async (req, res) => {
  settingsService.clearToken();
  await bot.disconnect();
  log.warn('Discord bot token silindi.');
  req.flash('success', 'Discord bot token silindi ve bağlantı kapatıldı.');
  return res.redirect('/ayarlar');
});

module.exports = {
  showSettings,
  updateSettings,
  updateAdminAccount,
  testDiscord,
  sendMessageNow,
  clearToken,
};
