'use strict';

/** Giriş / çıkış işlemleri. */

const { verifyCredentials } = require('../middleware/auth');
const log = require('../utils/logger').create('auth');

/** GET /giris */
function showLogin(req, res) {
  res.render('pages/login', {
    pageTitle: 'Giriş',
    error: null,
    username: '',
  });
}

/** POST /giris */
function login(req, res) {
  const { username, password } = req.body;

  if (!verifyCredentials(username, password)) {
    // Hangi alanın yanlış olduğunu söylemeyiz (kullanıcı adı sayımını zorlaştırır).
    return res.status(401).render('pages/login', {
      pageTitle: 'Giriş',
      error: 'Kullanıcı adı veya parola hatalı.',
      username: String(username ?? ''),
    });
  }

  // Oturum sabitleme (session fixation) saldırısına karşı oturumu yenile:
  // giriş öncesi verilen oturum kimliği geçersiz kılınır.
  const returnTo = req.session.returnTo;
  req.session.regenerate((error) => {
    if (error) {
      log.error('Oturum yenilenemedi', error);
      return res.status(500).render('pages/login', {
        pageTitle: 'Giriş',
        error: 'Oturum başlatılamadı. Lütfen tekrar deneyin.',
        username: String(username ?? ''),
      });
    }

    req.session.isAuthenticated = true;
    return res.redirect(returnTo ?? '/');
  });
}

/** POST /cikis */
function logout(req, res) {
  req.session.destroy(() => {
    res.clearCookie('ofis.sid');
    res.redirect('/giris');
  });
}

module.exports = { showLogin, login, logout };
