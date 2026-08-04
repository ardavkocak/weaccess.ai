'use strict';

/**
 * Güvenli yönlendirme yardımcısı.
 *
 * Formlar, işlem sonrası kullanıcıyı geldiği sayfaya döndürmek için gizli bir
 * `redirectTo` alanı gönderir. Bu değer istemciden geldiği için doğrudan
 * `res.redirect()`e verilmesi "açık yönlendirme" (open redirect) oluşturur:
 * `redirectTo=https://kotu-site.example` gönderen biri, panelden çıkan bir
 * bağlantıyla kullanıcıyı dış siteye taşıyabilir.
 *
 * Bu yüzden yalnızca uygulama içi göreli yollara izin verilir.
 */

/**
 * Verilen hedefi doğrular; güvenli değilse yedek yola düşer.
 *
 * Kabul edilir : "/", "/personeller", "/gorev-sirasi?tur=1"
 * Reddedilir   : "https://site.example", "//site.example", "javascript:alert(1)"
 *
 * @param {unknown} target Formdan gelen ham değer.
 * @param {string} fallback Geçersizse kullanılacak yol.
 * @returns {string}
 */
function safeRedirect(target, fallback = '/') {
  const value = String(target ?? '');

  // Tek bir "/" ile başlamalı. "//host" protokole duyarlı dış bağlantıdır,
  // "/\host" bazı tarayıcılarda aynı şekilde yorumlanır; ikisi de reddedilir.
  if (!value.startsWith('/') || value.startsWith('//') || value.startsWith('/\\')) {
    return fallback;
  }

  return value;
}

module.exports = { safeRedirect };
