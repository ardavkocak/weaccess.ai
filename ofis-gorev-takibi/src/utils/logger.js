'use strict';

/**
 * Basit, bağımlılıksız kayıt (log) altyapısı.
 *
 * Neden hazır bir kütüphane (winston/pino) değil?
 * Bu uygulamanın tüm ihtiyacı: zaman damgası, seviye, kaynak etiketi ve isteğe
 * bağlı dosyaya yazma. Bunun için ek bağımlılık taşımak, "klonla ve tek komutla
 * çalıştır" hedefini pahalılaştırır. İhtiyaç büyürse buradaki `write()`
 * fonksiyonunu bir kütüphaneye bağlamak yeterlidir; çağrı yerleri değişmez.
 *
 * KULLANIM
 *   const log = require('../utils/logger').create('cron');
 *   log.info('Görev başladı');
 *   log.error('Mesaj gönderilemedi', error);
 *
 * DOSYAYA YAZMA
 *   .env içinde LOG_FILE=logs/app.log tanımlanırsa kayıtlar hem konsola hem
 *   dosyaya yazılır. Tanımlı değilse yalnızca konsola yazılır.
 */

const fs = require('fs');
const path = require('path');

const LEVELS = { debug: 10, info: 20, warn: 30, error: 40 };

// Seviye eşiği: .env'deki LOG_LEVEL (varsayılan info).
const threshold = LEVELS[String(process.env.LOG_LEVEL || 'info').toLowerCase()] ?? LEVELS.info;

// Konsolda seviyeyi hızlı ayırt etmek için renkler. TTY değilse (dosyaya
// yönlendirilmişse) renk kodları kirlilik yaratacağı için kapatılır.
const useColor = process.stdout.isTTY;
const COLORS = {
  debug: '\x1b[90m', // gri
  info: '\x1b[36m',  // camgöbeği
  warn: '\x1b[33m',  // sarı
  error: '\x1b[31m', // kırmızı
  reset: '\x1b[0m',
  dim: '\x1b[2m',
};

/** Dosyaya yazma akışı (yalnızca LOG_FILE tanımlıysa). */
let fileStream = null;
if (process.env.LOG_FILE) {
  const filePath = path.resolve(process.cwd(), process.env.LOG_FILE);
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fileStream = fs.createWriteStream(filePath, { flags: 'a' });
}

/** "2026-07-17 08:05:00" biçiminde yerel zaman damgası. */
function timestamp() {
  const now = new Date();
  const pad = (n) => String(n).padStart(2, '0');
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())} ` +
         `${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}`;
}

/**
 * Error nesnelerini okunabilir metne çevirir.
 * Hata dışındaki değerler olduğu gibi bırakılır.
 */
function formatExtra(value) {
  if (value instanceof Error) {
    // Yığın izi yalnızca debug seviyesinde ilgi çekicidir; aksi halde gürültü yapar.
    return threshold <= LEVELS.debug && value.stack ? `\n${value.stack}` : ` ${value.message}`;
  }
  if (value === undefined) return '';
  if (typeof value === 'object') {
    try { return ` ${JSON.stringify(value)}`; } catch { return ' [nesne]'; }
  }
  return ` ${value}`;
}

function write(level, scope, message, extra) {
  if (LEVELS[level] < threshold) return;

  const time = timestamp();
  const label = level.toUpperCase().padEnd(5);
  const text = `${message}${formatExtra(extra)}`;

  // Dosyaya renksiz yaz.
  if (fileStream) {
    fileStream.write(`${time} ${label} [${scope}] ${text}\n`);
  }

  const line = useColor
    ? `${COLORS.dim}${time}${COLORS.reset} ${COLORS[level]}${label}${COLORS.reset} ${COLORS.dim}[${scope}]${COLORS.reset} ${text}`
    : `${time} ${label} [${scope}] ${text}`;

  // Uyarı ve hatalar stderr'e gider; böylece `npm start 2> hatalar.log` çalışır.
  if (level === 'error' || level === 'warn') console.error(line);
  else console.log(line);
}

/**
 * Bir kaynak etiketine bağlı logger üretir.
 * @param {string} scope Örn. 'cron', 'discord', 'http'
 */
function create(scope) {
  return {
    debug: (message, extra) => write('debug', scope, message, extra),
    info: (message, extra) => write('info', scope, message, extra),
    warn: (message, extra) => write('warn', scope, message, extra),
    error: (message, extra) => write('error', scope, message, extra),
  };
}

module.exports = { create };
