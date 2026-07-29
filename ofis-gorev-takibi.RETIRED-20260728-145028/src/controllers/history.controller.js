'use strict';

/** Görev Geçmişi sayfası — hangi gün görev kimdeydi. */

const historyService = require('../services/history.service');
const dutyTypeService = require('../services/dutyType.service');

const PAGE_SIZE = 20;

/** GET /gorev-gecmisi */
function showHistory(req, res) {
  const dutyTypes = dutyTypeService.getAll();

  // Filtreler
  const dutyTypeId = Number(req.query.tur) || null;
  const from = /^\d{4}-\d{2}-\d{2}$/.test(req.query.baslangic ?? '') ? req.query.baslangic : null;
  const to = /^\d{4}-\d{2}-\d{2}$/.test(req.query.bitis ?? '') ? req.query.bitis : null;
  const page = Math.max(1, Number(req.query.sayfa) || 1);

  const result = historyService.list({ dutyTypeId, from, to, page, pageSize: PAGE_SIZE });

  res.render('pages/history', {
    pageTitle: 'Görev Geçmişi',
    activeNav: 'history',
    dutyTypes,
    history: result,
    stats: historyService.getStatsByEmployee(dutyTypeId),
    filters: { dutyTypeId, from, to },
    // Sayfalama linklerinde filtreleri korumak için hazır sorgu dizesi.
    queryString: buildQueryString({ tur: dutyTypeId, baslangic: from, bitis: to }),
  });
}

/** Boş olmayan filtreleri "&k=v" biçiminde birleştirir. */
function buildQueryString(params) {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value) search.set(key, value);
  }
  const str = search.toString();
  return str ? `&${str}` : '';
}

module.exports = { showHistory };
