'use strict';

/**
 * Express uygulamasının kurulumu (middleware zinciri + rotalar).
 * Sunucuyu dinlemeye alma işi `server.js` içindedir; bu ayrım sayesinde
 * uygulama test edilirken port açmadan içe aktarılabilir.
 */

const path = require('path');
const express = require('express');
const session = require('express-session');
const SqliteStore = require('better-sqlite3-session-store')(session);

const { config } = require('./config');
const db = require('./database/connection');
const routes = require('./routes');
const { flash, viewLocals } = require('./middleware/locals');
const { csrfToken, verifyCsrf } = require('./middleware/csrf');
const { excelUpload } = require('./middleware/upload');
const { notFound, errorHandler } = require('./middleware/errorHandler');

const app = express();

// --- Görünüm motoru ---
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));

// Ters vekil (nginx vb.) arkasında secure cookie'nin çalışması için.
if (config.session.secure) app.set('trust proxy', 1);

// --- Temel middleware ---
app.use(express.urlencoded({ extended: false })); // Form gövdelerini ayrıştır.
app.use(express.static(path.join(config.rootDir, 'public'), { maxAge: '1h' }));

app.use(session({
  name: 'ofis.sid',
  secret: config.session.secret,
  resave: false,
  saveUninitialized: false,
  // Oturumlar SQLite'ta saklanır (bellekte değil). Böylece sunucu yeniden
  // başladığında oturumlar ve CSRF anahtarları KAYBOLMAZ; açık kalmış giriş
  // sayfaları "Oturum doğrulaması başarısız" (403) hatası vermez.
  store: new SqliteStore({
    client: db,
    expired: {
      clear: true,
      intervalMs: 15 * 60 * 1000, // Süresi dolmuş oturumları 15 dakikada bir temizle.
    },
  }),
  cookie: {
    httpOnly: true,          // JavaScript cookie'yi okuyamaz (XSS azaltma).
    sameSite: 'lax',         // CSRF için ilk savunma katmanı.
    secure: config.session.secure,
    maxAge: 12 * 60 * 60 * 1000, // 12 saat
  },
}));

// --- Uygulama middleware'leri ---
app.use(flash);
app.use(viewLocals);
app.use(csrfToken);

// Yemek menüsü modülünün Excel yüklemesi multipart gövde gönderir; bunu
// `express.urlencoded` ayrıştıramaz. `verifyCsrf` gövdedeki `_csrf` alanını
// okuduğu için ayrıştırma ondan ÖNCE yapılmalıdır. Middleware yalnızca kendi
// yolunda çalışır (bkz. middleware/upload.js), diğer isteklere etkisi yoktur.
app.use(excelUpload);

app.use(verifyCsrf);

// --- Rotalar ---
app.use(routes);

// --- Hata yakalama (en sonda olmalı) ---
app.use(notFound);
app.use(errorHandler);

module.exports = app;
