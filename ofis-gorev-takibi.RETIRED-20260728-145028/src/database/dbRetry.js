'use strict';

/**
 * SQLite yazmaları için sınırlı, event-loop'u bloke ETMEYEN yeniden deneme.
 *
 * NEDEN busy_timeout YETERLİ DEĞİL?
 * ----------------------------------
 * better-sqlite3 tamamen SENKRONdur. `connection.js`'deki `busy_timeout`
 * ayarı, kilit çakışmasında better-sqlite3'ün kendi içinde (native kod
 * seviyesinde) beklemesini sağlar — ama bu bekleme boyunca TÜM Node.js
 * event loop'u donar: o an başka HİÇBİR interaction, HTTP isteği ya da
 * zamanlanmış iş işlenemez. `busy_timeout`'u yüksek tutmak (örn. 5000ms),
 * "hata verme" sorununu "bütün süreci 5 saniyeliğine dondur" sorununa
 * çevirir — bu da Discord'un 3 saniyelik yanıt penceresini aşmanın başka bir
 * yoludur.
 *
 * BU MODÜLÜN YAKLAŞIMI
 * ---------------------
 * `connection.js`'deki busy_timeout DÜŞÜK tutulur (yalnızca gerçekten anlık
 * mikro-çakışmaları örtmek için, bkz. dosya). Bunun ötesindeki çakışmalar için
 * uygulama katımında SINIRLI SAYIDA deneme yapılır; denemeler arasında
 * `await sleep()` ile event loop'a nefes aldırılır — böylece bir yazma
 * çakışması ne ANINDA çöker ne de tüm süreci donduruır.
 *
 * BU MODÜL YALNIZCA "defer sonrası" iş mantığı için kullanılmalıdır: Discord'a
 * ilk yanıt (deferUpdate/deferReply) ZATEN gönderildikten sonra çağrılan
 * business-logic transaction'ları içindir. defer'DAN ÖNCE hiçbir DB işlemi
 * olmamalı (bkz. interactionRouter.js) — bu sayede burada geçen birkaç yüz ms
 * Discord'un 3sn sınırını hiçbir zaman tehdit etmez (editReply/followUp için
 * süre sınırı ~15 dakikadır).
 */

const log = require('../utils/logger').create('db-retry');

const DEFAULT_DELAYS_MS = [50, 150, 400]; // Toplam ~600ms + transaction süreleri.

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function isBusyError(error) {
  const code = error?.code;
  const message = String(error?.message ?? '');
  return code === 'SQLITE_BUSY' || code === 'SQLITE_LOCKED' || /database is locked/i.test(message);
}

/**
 * Senkron bir fonksiyonu (genellikle `db.transaction(fn)`'in kendisini)
 * çakışma durumunda sınırlı sayıda tekrar dener.
 *
 * @template T
 * @param {() => T} fn Senkron, yan etkisi TAMAMEN transaction içinde olan fonksiyon.
 * @param {object} [opts]
 * @param {string} [opts.label] Log satırlarında görünen işlem adı.
 * @param {number[]} [opts.delaysMs] Denemeler arası bekleme (ms), sırayla.
 * @returns {Promise<T>}
 * @throws Son denemede de başarısız olursa orijinal hatayı fırlatır.
 */
async function withRetry(fn, { label = 'db-islemi', delaysMs = DEFAULT_DELAYS_MS } = {}) {
  const maxAttempts = delaysMs.length + 1;

  for (let attempt = 1; attempt <= maxAttempts; attempt += 1) {
    try {
      return fn();
    } catch (error) {
      const isLast = attempt === maxAttempts;
      if (!isBusyError(error) || isLast) throw error;

      const delay = delaysMs[attempt - 1];
      log.warn(`"${label}" kilitle karşılaştı (deneme ${attempt}/${maxAttempts}), ${delay}ms sonra tekrar denenecek.`);
      await sleep(delay);
    }
  }

  // Buraya asla ulaşılmaz (döngü ya döner ya fırlatır) — TypeScript/lint sakinliği için.
  throw new Error(`"${label}" tüm denemelerde başarısız oldu.`);
}

module.exports = { withRetry, isBusyError };
