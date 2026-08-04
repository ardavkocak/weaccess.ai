'use strict';

/**
 * Uygulama giriş noktası.
 *
 * Açılış sırası önemlidir:
 *   1. Veritabanı şeması hazırlanır (tablolar + varsayılan ayarlar).
 *   2. Discord botu (token varsa) arka planda bağlanır.
 *   3. Cron zamanlayıcı ayarlardaki saate göre kurulur.
 *   4. HTTP sunucusu dinlemeye başlar.
 *
 * 2. ve 3. adım başarısız olsa bile sunucu açılır; admin panelden düzeltebilsin.
 */

const { config, validateConfig } = require('./config');
const { initializeDatabase } = require('./database/schema');
const app = require('./app');
const bot = require('./discord/bot');
const scheduler = require('./cron/scheduler');
const mealScheduler = require('./cron/mealScheduler');
const dutyConfirmationService = require('./services/dutyConfirmation.service');

function printBanner() {
  const status = scheduler.getStatus();

  console.log('');
  console.log('  ╔══════════════════════════════════════════════╗');
  console.log('  ║        Ofis Görev Takip Sistemi              ║');
  console.log('  ╚══════════════════════════════════════════════╝');
  console.log('');
  console.log(`  Panel        : http://localhost:${config.port}`);
  console.log(`  Kullanıcı    : ${config.admin.username}`);
  console.log(`  Veritabanı   : ${config.databaseFile}`);
  console.log(`  Saat dilimi  : ${config.timezone}`);
  console.log(`  Discord bot  : ${bot.isConfigured() ? 'yapılandırıldı' : 'yapılandırılmadı (Ayarlar sayfasından ekleyin)'}`);
  console.log('');
  console.log('  Günlük mesaj takvimi:');
  for (const message of status.messages) {
    const mark = message.running ? '✓' : '✗';
    const note = message.kind === 'duty' ? ' → sırayı ilerletir' : '';
    console.log(`    ${mark} ${message.time}  ${message.name}${note}`);
  }

  const meal = mealScheduler.getStatus();
  console.log(`    ${meal.active ? '✓' : '✗'} ${meal.time}  Yarının Yemek Menüsü`);
  console.log('');
}

function start() {
  // 1. Veritabanı
  initializeDatabase();

  // 1b. Bozuk/eski onay kayıtlarının temizliği. Süreç bir akış ortasındayken
  // çökmüş/yeniden başlatılmışsa, geçmiş tarihli 'pending' satırlar kalıcı
  // olarak "bekliyor" görünmesin diye 'exhausted' işaretlenir (bkz.
  // dutyConfirmation.service.cleanupStalePending). Sıraya/rotasyona dokunmaz.
  dutyConfirmationService.cleanupStalePending();

  // Kurulum uyarıları (zayıf parola, eksik secret vb.)
  for (const warning of validateConfig()) {
    console.warn(`  ⚠ ${warning}`);
  }

  // 2. Discord (bağlanamazsa sunucuyu engellemez)
  bot.initialize();

  // 3. Cron (görev mesajları + yemek menüsü duyurusu ayrı zamanlayıcılardır)
  scheduler.initialize();
  mealScheduler.initialize();

  // 4. HTTP
  const server = app.listen(config.port, () => {
    printBanner();
  });

  server.on('error', (error) => {
    if (error.code === 'EADDRINUSE') {
      console.error(`\n  ✗ ${config.port} portu kullanımda. .env dosyasında PORT değerini değiştirin.\n`);
      process.exit(1);
    }
    throw error;
  });

  // --- Düzgün kapanış ---
  // Ctrl+C veya `docker stop` sonrası Discord soketini ve HTTP'yi temiz kapat.
  const shutdown = async (signal) => {
    console.log(`\n  ${signal} alındı, kapatılıyor...`);
    scheduler.stop();
    mealScheduler.stop();
    await bot.disconnect();
    server.close(() => {
      console.log('  Sunucu kapatıldı.');
      process.exit(0);
    });
    // Bağlantılar 10 sn içinde kapanmazsa zorla çık.
    setTimeout(() => process.exit(0), 10_000).unref();
  };

  process.on('SIGINT', () => shutdown('SIGINT'));
  process.on('SIGTERM', () => shutdown('SIGTERM'));

  return server;
}

// Doğrudan çalıştırıldıysa başlat (test için import edilebilir kalsın).
if (require.main === module) {
  start();
}

module.exports = { start };
