'use strict';

/**
 * Tüm görünümlerde ortak olan değişkenleri hazırlar.
 * (şirket adı, aktif menü, flash mesajları, giriş durumu)
 */

const settingsService = require('../services/settings.service');
const { initials, avatarColor } = require('../utils/view');

/**
 * Flash mesajı: bir sonraki sayfa yüklemesinde bir kez gösterilip silinir.
 * "Çalışan eklendi" gibi işlem sonucu bildirimleri için kullanılır.
 *
 * Kullanım (controller içinde):  req.flash('success', 'Kaydedildi.');
 */
function flash(req, res, next) {
  req.flash = (type, message) => {
    if (!req.session.flash) req.session.flash = [];
    req.session.flash.push({ type, message });
  };

  // Oturumdaki mesajları görünüme aktar ve kuyruğu boşalt (tek seferlik gösterim).
  res.locals.flashMessages = req.session.flash ?? [];
  req.session.flash = [];

  next();
}

/** Şablonların ihtiyaç duyduğu genel değişkenler. */
function viewLocals(req, res, next) {
  res.locals.companyName = settingsService.get('company_name', 'Şirketiniz');
  res.locals.isAuthenticated = Boolean(req.session?.isAuthenticated);
  res.locals.currentPath = req.path;
  // Her sayfa kendi controller'ında bunu ezer; menü vurgusu için kullanılır.
  res.locals.activeNav = '';
  res.locals.pageTitle = '';

  // Şablon yardımcıları: <%= initials(name) %>
  res.locals.initials = initials;
  res.locals.avatarColor = avatarColor;

  next();
}

module.exports = { flash, viewLocals };
