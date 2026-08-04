'use strict';

/**
 * CSRF (Cross-Site Request Forgery) koruması.
 *
 * Panel tamamen form tabanlı çalıştığı için, oturumu açık bir admin'in başka bir
 * sitedeki gizli formla farkında olmadan "çalışan sil" isteği göndermesi mümkün
 * olurdu. Bunu engellemek için her oturuma rastgele bir token verilir; tüm POST
 * formlarında gizli alan olarak gönderilir ve sunucuda karşılaştırılır.
 *
 * Cookie'de ayrıca `sameSite: 'lax'` kullanılır — bu iki katman birlikte çalışır.
 */

const crypto = require('crypto');

/** Oturuma token üretir (yoksa) ve görünümlere aktarır. */
function csrfToken(req, res, next) {
  if (!req.session.csrfToken) {
    req.session.csrfToken = crypto.randomBytes(32).toString('hex');
  }
  // Tüm EJS şablonlarında <%= csrfToken %> olarak kullanılabilir.
  res.locals.csrfToken = req.session.csrfToken;
  next();
}

/** Durum değiştiren isteklerde (POST) token'ı doğrular. */
function verifyCsrf(req, res, next) {
  if (req.method === 'GET' || req.method === 'HEAD' || req.method === 'OPTIONS') {
    return next();
  }

  const submitted = req.body?._csrf;
  const expected = req.session?.csrfToken;

  if (!expected || !submitted || submitted !== expected) {
    // Giriş formu özel durumdur: kullanıcı henüz oturum açmadığı için burada
    // korunacak bir oturum yoktur. Açık kalmış (bayat) bir giriş sayfasından
    // gelen istekte sert bir 403 hata ekranı göstermek yerine, kullanıcıyı
    // temiz bir token'a sahip yeni giriş sayfasına geri gönderiyoruz. Böylece
    // sayfa kendini onarır ve ikinci deneme sorunsuz çalışır. Bu, gerçek CSRF
    // korumasını zayıflatmaz: saldırgan yine kurbanın token'ını okuyamaz.
    if (req.path === '/giris') {
      if (req.session) {
        req.session.csrfToken = undefined; // Bir sonraki GET'te yeni token üretilsin.
        if (!req.session.flash) req.session.flash = [];
        req.session.flash.push({
          type: 'info',
          message: 'Oturum süreniz yenilendi. Lütfen tekrar giriş yapın.',
        });
      }
      return res.redirect('/giris');
    }

    const error = new Error('Oturum doğrulaması başarısız oldu. Sayfayı yenileyip tekrar deneyin.');
    error.status = 403;
    return next(error);
  }

  return next();
}

module.exports = { csrfToken, verifyCsrf };
