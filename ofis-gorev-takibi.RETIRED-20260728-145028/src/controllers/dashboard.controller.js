'use strict';

/** Dashboard — sistemin durumunu tek bakışta gösterir. */

const employeeService = require('../services/employee.service');
const dutyTypeService = require('../services/dutyType.service');
const rotationService = require('../services/rotation.service');
const historyService = require('../services/history.service');
const dutyService = require('../services/duty.service');
const confirmationService = require('../services/dutyConfirmation.service');
const dutyNotifier = require('../services/dutyNotifier.service');
const scheduler = require('../cron/scheduler');
const bot = require('../discord/bot');
const { renderManualOverride } = require('../discord/confirmationMessages');
const { asyncHandler } = require('../middleware/errorHandler');
const { todayISO, formatLongTR } = require('../utils/date');
const { safeRedirect } = require('../utils/redirect');

/** GET / */
function showDashboard(req, res) {
  const dutyType = dutyTypeService.getDefault();

  // Hiç görev türü yoksa (kullanıcı elle sildiyse) boş durum göster.
  if (!dutyType) {
    return res.render('pages/dashboard', {
      pageTitle: 'Dashboard',
      activeNav: 'dashboard',
      dutyType: null,
      overview: null,
      counts: employeeService.getCounts(),
      recentHistory: [],
      schedulerStatus: scheduler.getStatus(),
      dutyTime: '08:05',
      botStatus: bot.getStatus(),
      confirmation: null,
      todayLong: formatLongTR(todayISO()),
    });
  }

  const overview = rotationService.getOverview(dutyType.id);

  res.render('pages/dashboard', {
    pageTitle: 'Dashboard',
    activeNav: 'dashboard',
    dutyType,
    overview,
    counts: employeeService.getCounts(),
    recentHistory: historyService.getRecent(5),
    schedulerStatus: scheduler.getStatus(),
    // Sabah bildiriminin saati: "Bildirim bekliyor (08:05)" rozetinde kullanılır.
    dutyTime: scheduler.getDutyTime(dutyType.id),
    botStatus: bot.getStatus(),
    // Bugünkü etkileşimli onay durumu (bekliyor / kesinleşti / kimse yok).
    confirmation: confirmationService.getTodayStatus(dutyType.id),
    todayLong: formatLongTR(todayISO()),
  });
}

/**
 * POST /gorev/:dutyTypeId/sirayi-gec
 * BUGÜNKÜ görevi bir sonraki aktif çalışana aktarır.
 *
 * Devredilen kişi görevi yapmamış sayılır; sıra hakkını kaybetmez (Discord'daki
 * "Hayır" cevabıyla aynı mantık). Ayrıntı: rotation.service.skipToNext().
 */
const skipTurn = asyncHandler(async (req, res) => {
  const dutyTypeId = Number(req.params.dutyTypeId);
  const dutyType = dutyTypeService.getById(dutyTypeId);

  if (!dutyType) {
    req.flash('error', 'Görev türü bulunamadı.');
    return res.redirect('/');
  }

  const result = rotationService.skipToNext(dutyTypeId);
  req.flash(result.ok ? 'success' : 'error', result.message);

  // Bekleyen bir Discord sorusu kapatıldıysa mesajı da sonuçlandır ki kanaldaki
  // butonlar paneldeki kararla çelişmesin. Hata olursa akış zaten DB'de kapalı.
  if (result.closedFlow) {
    await bot.editInteractive(
      result.closedFlow.channelId,
      result.closedFlow.messageId,
      renderManualOverride(result.closedFlow.name),
      []
    );
  }

  // Görev el değiştirdi: yeni görevli gün içi hatırlatmaları alacak, o yüzden
  // "görev sende" mesajını da alsın. DM gönderilemezse yalnızca log'a yazılır;
  // paneldeki sonuç mesajı bundan etkilenmez.
  if (result.ok) {
    await dutyNotifier.sendDutyAssigned(dutyTypeId, dutyNotifier.getTodayAssignee(dutyTypeId));
  }

  // Kullanıcıyı geldiği sayfaya döndür (dashboard veya görev sırası).
  return res.redirect(safeRedirect(req.body.redirectTo, '/'));
});

/**
 * POST /gorev/:dutyTypeId/simdi-gonder
 * Bugünkü bildirimi elle gönderir. Sırayı ikinci kez ilerletmez.
 */
const sendNow = asyncHandler(async (req, res) => {
  const dutyTypeId = Number(req.params.dutyTypeId);
  const dutyType = dutyTypeService.getById(dutyTypeId);

  if (!dutyType) {
    req.flash('error', 'Görev türü bulunamadı.');
    return res.redirect('/');
  }

  const result = await dutyService.resendToday(dutyTypeId);
  req.flash(result.ok ? 'success' : 'error', result.message);

  return res.redirect(safeRedirect(req.body.redirectTo, '/'));
});

/**
 * POST /gorev/:dutyTypeId/onayi-sifirla
 *
 * Yanlışlıkla "Evet"e basıldığında bugünkü onayı geri alır: günün geçmiş kaydı
 * silinir, yakılmışsa sıra hakkı iade edilir ve Discord'daki soru baştan sorulur.
 * Denetim kayıtları korunur. Ayrıntı: dutyConfirmation.service.resetToday().
 */
const resetConfirmation = asyncHandler(async (req, res) => {
  const dutyTypeId = Number(req.params.dutyTypeId);
  const dutyType = dutyTypeService.getById(dutyTypeId);

  if (!dutyType) {
    req.flash('error', 'Görev türü bulunamadı.');
    return res.redirect('/');
  }

  const result = await confirmationService.resetAndAskAgain(dutyTypeId);
  req.flash(result.ok ? 'success' : 'error', result.message);

  return res.redirect(safeRedirect(req.body.redirectTo, '/'));
});

module.exports = { showDashboard, skipTurn, sendNow, resetConfirmation };
