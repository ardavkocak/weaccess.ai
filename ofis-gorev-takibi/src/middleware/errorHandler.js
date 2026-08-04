'use strict';

const log = require('../utils/logger').create('http');

/**
 * Merkezî hata yakalama.
 *
 * Express 4'te async fonksiyonlardaki hatalar otomatik yakalanmaz; bu yüzden
 * `asyncHandler` sarmalayıcısı ile Promise reddi `next(error)`'a bağlanır.
 */

/**
 * Async controller'ları sarmalar; hata olursa Express'in hata zincirine aktarır.
 *
 * Kullanım:  router.post('/x', asyncHandler(async (req, res) => { ... }));
 */
function asyncHandler(fn) {
  return (req, res, next) => Promise.resolve(fn(req, res, next)).catch(next);
}

/** Eşleşmeyen rotalar için 404. */
function notFound(req, res) {
  res.status(404).render('pages/error', {
    pageTitle: 'Sayfa Bulunamadı',
    activeNav: '',
    status: 404,
    message: 'Aradığınız sayfa bulunamadı.',
  });
}

/** Son durak: tüm hataları yakalar ve kullanıcıya anlaşılır bir sayfa gösterir. */
// eslint-disable-next-line no-unused-vars -- Express hata middleware'i 4 parametre ister.
function errorHandler(error, req, res, next) {
  const status = error.status ?? 500;

  if (status >= 500) {
    log.error(`${req.method} ${req.originalUrl} → ${status}`, error);
  }

  res.status(status).render('pages/error', {
    pageTitle: 'Hata',
    activeNav: '',
    status,
    message: status >= 500
      ? 'Sunucuda beklenmeyen bir hata oluştu. Lütfen tekrar deneyin.'
      : error.message,
  });
}

module.exports = { asyncHandler, notFound, errorHandler };
