'use strict';

/**
 * Excel yüklemesi için multipart form ayrıştırıcı (multer).
 *
 * BELLEKTE TUTULUR, DİSKE YAZILMAZ
 * --------------------------------
 * Dosya yalnızca bir kez okunup veritabanına aktarılacağı için diskte
 * saklamanın anlamı yok: yüklenen içerik bellekte ayrıştırılır, istek bitince
 * çöp toplayıcıya bırakılır. Böylece temizlenmesi gereken bir yükleme klasörü,
 * dolayısıyla disk şişmesi veya yol (path traversal) riski oluşmaz.
 *
 * CSRF SIRALAMASI (ÖNEMLİ)
 * ------------------------
 * `verifyCsrf` gövdedeki `_csrf` alanını okur. multipart gövdeyi `express.
 * urlencoded` ayrıştıramaz; bu yüzden bu middleware CSRF kontrolünden ÖNCE
 * çalışmalıdır (bkz. app.js). Sıralama tersine dönerse yükleme her seferinde
 * 403 verir. Middleware yalnızca kendi yoluna bağlandığı için diğer isteklere
 * hiçbir maliyeti yoktur.
 */

const multer = require('multer');

/** Yüklemenin kabul edildiği tek yol. */
const UPLOAD_PATH = '/yemek-menusu/yukle';

/** Form alanının adı (görünümdeki input name ile aynı olmalı). */
const FIELD_NAME = 'file';

/** En büyük dosya boyutu. Aylık menü birkaç KB'dir; 5 MB fazlasıyla yeterli. */
const MAX_FILE_SIZE = 5 * 1024 * 1024;

const ALLOWED_MIME_TYPES = new Set([
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', // .xlsx
  'application/octet-stream', // Bazı tarayıcılar/işletim sistemleri bunu gönderir.
]);

const upload = multer({
  storage: multer.memoryStorage(),
  limits: { fileSize: MAX_FILE_SIZE, files: 1 },
  fileFilter(req, file, callback) {
    const isXlsx = /\.xlsx$/i.test(file.originalname ?? '');

    // Uzantı esas alınır: MIME türü işletim sistemine göre değişkendir, uzantı
    // ise kullanıcının gerçekten seçtiği dosyayı yansıtır.
    if (!isXlsx || !ALLOWED_MIME_TYPES.has(file.mimetype)) {
      const error = new Error('Yalnızca .xlsx uzantılı Excel dosyaları yüklenebilir.');
      error.status = 400;
      error.isFriendly = true;
      return callback(error);
    }
    return callback(null, true);
  },
});

/**
 * Yükleme yolunu ayrıştıran middleware.
 *
 * multer hataları (boyut aşımı, yanlış tür) kullanıcıya gösterilebilir Türkçe
 * mesaja çevrilir ve isteği düşürmek yerine `req.uploadError` olarak taşınır;
 * controller bunu flash mesajına dönüştürür. Böylece admin sert bir hata ekranı
 * yerine sayfada anlaşılır bir uyarı görür.
 */
function excelUpload(req, res, next) {
  if (req.method !== 'POST' || req.path !== UPLOAD_PATH) return next();

  return upload.single(FIELD_NAME)(req, res, (error) => {
    if (!error) return next();

    if (error.code === 'LIMIT_FILE_SIZE') {
      req.uploadError = `Dosya çok büyük. En fazla ${MAX_FILE_SIZE / 1024 / 1024} MB yükleyebilirsiniz.`;
    } else {
      req.uploadError = error.isFriendly
        ? error.message
        : 'Dosya yüklenemedi. Lütfen tekrar deneyin.';
    }

    // Gövde ayrıştırılamadıysa CSRF alanı da yoktur; isteği zincirde tutup
    // controller'a bırakmak yerine burada güvenli biçimde geri döneriz.
    if (!req.body?._csrf) {
      if (req.session) {
        if (!req.session.flash) req.session.flash = [];
        req.session.flash.push({ type: 'error', message: req.uploadError });
      }
      return res.redirect('/yemek-menusu');
    }

    return next();
  });
}

module.exports = { excelUpload, UPLOAD_PATH, FIELD_NAME, MAX_FILE_SIZE };
