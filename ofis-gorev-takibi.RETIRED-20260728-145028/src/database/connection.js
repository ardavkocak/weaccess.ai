'use strict';

/**
 * SQLite bağlantısı (tekil / singleton).
 *
 * better-sqlite3 senkron çalışır; bu yüzden servis katmanında callback veya
 * Promise zinciri kurmaya gerek kalmaz, kod düz ve okunabilir olur. Tek süreçli
 * bir iç uygulama için performansı fazlasıyla yeterlidir.
 */

const fs = require('fs');
const path = require('path');
const Database = require('better-sqlite3');
const { config } = require('../config');

// Veritabanı dosyasının klasörü yoksa oluştur (ilk çalıştırma senaryosu).
const dbDir = path.dirname(config.databaseFile);
if (!fs.existsSync(dbDir)) {
  fs.mkdirSync(dbDir, { recursive: true });
}

const db = new Database(config.databaseFile);

// WAL modu: okuma ve yazmanın birbirini kilitlemesini engeller.
db.pragma('journal_mode = WAL');
// Foreign key kısıtlarını zorunlu kıl (SQLite'ta varsayılan olarak kapalıdır).
db.pragma('foreign_keys = ON');
// Bu dosyaya artık Office Portal (Django) tarafı da eşzamanlı yazıyor. WAL modu
// çoğu çakışmayı önler ama iki yazma tam aynı ana denk gelirse better-sqlite3
// varsayılan olarak ANINDA "database is locked" fırlatır (busy_timeout = 0).
//
// ÖNEMLİ: Bu değer BİLEREK ÇOK DÜŞÜK tutulur (50ms), YÜKSEK değil. better-sqlite3
// senkron çalışır; busy_timeout beklerken TÜM Node.js event loop'u donar — bir
// SQLite kilit çakışması bu bekleme boyunca sunucudaki HİÇBİR isteği/etkileşimi
// işleyemez hale getirir. Yüksek bir busy_timeout (örn. 5sn), "anında hata"
// sorununu "tüm süreci 5sn dondur" sorununa çevirir; bu da Discord'un 3sn'lik
// interaction yanıt penceresini aşmanın başka bir yoludur.
//
// STRES TESTİ BULGUSU: 200ms ile bile, gerçek/uzun süreli bir kilit çakışması
// altında (bkz. dbRetry.withRetry'nin her denemesi) event loop'ta tek bir
// denemede ~200ms'e kadar donma ölçüldü — Discord'un 3sn sınırını tehdit etmez
// (defer zaten önce yapıldığı için) ama sunucunun genel yanıt verebilirliğini
// gereksiz yere düşürür. 50ms, "gerçekten anlık" mikro çakışmaları hâlâ
// örterken tek bir bloklanma penceresini küçültür; daha uzun çakışmalar için
// asıl tolerans YİNE uygulama katmanındadır (bkz. src/database/dbRetry.js):
// event-loop'u bloke etmeyen, denemeler arasında `await` ile nefes alan sınırlı
// bir yeniden deneme mekanizması. Bu mekanizma yalnızca Discord'a İLK yanıt
// (deferUpdate/deferReply) zaten gönderildikten SONRA çalışan iş mantığında
// kullanılır (bkz. discord/interactionRouter.js), böylece SQL süresi Discord'un
// 3sn sınırını hiçbir zaman tehdit etmez.
db.pragma('busy_timeout = 50');

module.exports = db;
