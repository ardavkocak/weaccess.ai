'use strict';

/**
 * Kimlik doğrulama katmanı.
 *
 * Sistemde yalnızca admin oturum açar; çalışanların giriş yapmasına gerek yoktur.
 * Bu yüzden kullanıcı tablosu yerine tek bir yönetici hesabı kullanılır.
 *
 * Hesabın kendisi (kullanıcı adı + parola hash'i) `adminAccount.service` içinde
 * yönetilir: panelden değiştirilebilir, parola scrypt ile hash'lenir ve
 * karşılaştırma sabit sürede yapılır (timing attack'a karşı). Panelden hiç
 * değiştirilmediyse .env'deki değerler geçerlidir.
 */

const adminAccount = require('../services/adminAccount.service');

/**
 * Giriş bilgilerini doğrular.
 * @returns {boolean}
 */
function verifyCredentials(username, password) {
  return adminAccount.verifyCredentials(username, password);
}

/** Korumalı sayfalar için: oturum yoksa giriş ekranına yönlendirir. */
function requireAuth(req, res, next) {
  if (req.session?.isAuthenticated) return next();

  // Giriş sonrası kullanıcıyı gitmek istediği sayfaya geri götürmek için sakla.
  if (req.method === 'GET') {
    req.session.returnTo = req.originalUrl;
  }
  return res.redirect('/giris');
}

/** Giriş sayfası için: zaten oturum açıksa panele gönderir. */
function redirectIfAuthenticated(req, res, next) {
  if (req.session?.isAuthenticated) return res.redirect('/');
  return next();
}

module.exports = { verifyCredentials, requireAuth, redirectIfAuthenticated };
