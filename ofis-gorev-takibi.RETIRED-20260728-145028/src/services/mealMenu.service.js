'use strict';

/**
 * Yemek menüsü servisi — `meal_menus` tablosunun tek erişim noktası.
 *
 * Excel yalnızca yükleme anında okunur (bkz. mealImport.service.js); buradan
 * sonrası tamamen veritabanı üzerinden yürür.
 *
 * `items` sütunu JSON dizisi olarak saklanır; bu servis dışarıya her zaman
 * ayrıştırılmış `items: Array<{ name: string, kcal: number|null }>` verir,
 * çağıranlar JSON.parse ile uğraşmaz.
 *
 * GERİYE DÖNÜK UYUM: Eski kayıtlar yemekleri düz metin (`string[]`) olarak
 * tutuyordu. `normalizeItem` her iki biçimi de aynı `{ name, kcal }` şekline
 * getirir; kalori bilgisi olmayan (eski) yemeklerde `kcal = null` olur.
 */

const db = require('../database/connection');
const { todayISO, formatLongTR, formatShortTR } = require('../utils/date');
const calendar = require('./calendar.service');
const log = require('../utils/logger').create('meal');

/** Türkçe gün adları — Excel'de "gün" sütunu yoksa tarihten üretmek için. */
const DAY_NAMES = ['Pazar', 'Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma', 'Cumartesi'];

/**
 * Bir yemek girdisini standart `{ name, kcal }` biçimine getirir.
 *   - "Mercimek Çorbası"              (eski) → { name: 'Mercimek Çorbası', kcal: null }
 *   - { name: 'Tavuk', kcal: 420 }    (yeni) → aynen
 * Tanınmayan/boş girdiler için null döner (çağıran eler).
 */
function normalizeItem(item) {
  if (typeof item === 'string') {
    const name = item.trim();
    return name ? { name, kcal: null } : null;
  }
  if (item && typeof item === 'object' && typeof item.name === 'string' && item.name.trim()) {
    const kcal = Number.isFinite(item.kcal) && item.kcal > 0 ? item.kcal : null;
    return { name: item.name.trim(), kcal };
  }
  return null;
}

/** Ham satırı görünüm/servis katmanının beklediği biçime çevirir. */
function hydrate(row) {
  if (!row) return null;

  let items = [];
  try {
    const parsed = JSON.parse(row.items);
    if (Array.isArray(parsed)) items = parsed.map(normalizeItem).filter(Boolean);
  } catch {
    // Elle düzenleme sonucu bozulmuş JSON tüm sayfayı çökertmesin.
    log.warn(`Menü satırı okunamadı (${row.menu_date}); yemek listesi boş kabul edildi.`);
  }

  return {
    ...row,
    items,
    dayName: row.day_name || dayNameOf(row.menu_date),
    dateLong: formatLongTR(row.menu_date),
    dateShort: formatShortTR(row.menu_date),
    isAnnounced: Boolean(row.announced_at),
  };
}

/** "2026-07-23" -> "Perşembe" */
function dayNameOf(isoDate) {
  const date = new Date(`${isoDate}T12:00:00Z`);
  return Number.isNaN(date.getTime()) ? '' : DAY_NAMES[date.getUTCDay()];
}

/** Yarının tarihini "YYYY-MM-DD" olarak döner (ofis saat diliminde). */
function tomorrowISO(from = new Date()) {
  // Bugünün ISO tarihinden ilerlemek, saat dilimi kaymalarına karşı en güvenli
  // yoldur: todayISO() zaten ofis saat dilimine sabitlenmiştir.
  const date = new Date(`${todayISO(from)}T12:00:00Z`);
  date.setUTCDate(date.getUTCDate() + 1);
  return date.toISOString().slice(0, 10);
}

/** Belirli bir günün menüsü. */
function getByDate(menuDate) {
  return hydrate(db.prepare('SELECT * FROM meal_menus WHERE menu_date = ?').get(menuDate));
}

/**
 * Duyurulacak menünün tarihi = SONRAKİ İŞ GÜNÜ.
 *
 * Menü bir iş günü öncesinden duyurulur, böylece çalışanlar hafta sonuna
 * girmeden Pazartesi için tercih yapabilir:
 *   Pazartesi menüsü → Cuma   (hafta sonu atlanır)
 *   Salı menüsü      → Pazartesi
 *   ...
 *   Cuma menüsü      → Perşembe
 *
 * Hafta içi bu "yarın" ile aynıdır; yalnızca Cuma (ve tatil öncesi) farklılaşır.
 * Tatiller de `calendar.nextWorkingDay()` tarafından atlanır.
 */
function nextMenuDateISO(from = new Date()) {
  return calendar.nextWorkingDay(todayISO(from));
}

/** Duyurulacak (sonraki iş günü) menüsü — duyurunun ve panelin tek kaynağı. */
function getNextMenu() {
  return getByDate(nextMenuDateISO());
}

/**
 * Menüleri listeler.
 * @param {object} [options]
 * @param {boolean} [options.upcomingOnly] Yalnızca bugün ve sonrası.
 * @param {number} [options.limit]
 */
function list({ upcomingOnly = false, limit = null } = {}) {
  const where = upcomingOnly ? 'WHERE menu_date >= @today' : '';
  const limitSql = limit ? 'LIMIT @limit' : '';

  return db
    .prepare(`SELECT * FROM meal_menus ${where} ORDER BY menu_date ASC ${limitSql}`)
    .all({ today: todayISO(), limit })
    .map(hydrate);
}

/**
 * Panelin özet kutusu: kaç kayıt var, hangi aralıkta, en son ne zaman yüklendi.
 */
function getSummary() {
  const row = db.prepare(`
    SELECT
      COUNT(*)          AS total,
      MIN(menu_date)    AS first_date,
      MAX(menu_date)    AS last_date,
      MAX(updated_at)   AS last_updated
    FROM meal_menus
  `).get();

  const upcoming = db
    .prepare('SELECT COUNT(*) AS total FROM meal_menus WHERE menu_date >= ?')
    .get(todayISO()).total;

  // Son yüklenen dosyanın adı (en son güncellenen satırdan).
  const source = db
    .prepare('SELECT source_file FROM meal_menus ORDER BY updated_at DESC, id DESC LIMIT 1')
    .get();

  return {
    total: row.total,
    upcoming,
    firstDate: row.first_date,
    lastDate: row.last_date,
    firstDateLong: row.first_date ? formatLongTR(row.first_date) : null,
    lastDateLong: row.last_date ? formatLongTR(row.last_date) : null,
    lastUpdated: row.last_updated,
    sourceFile: source?.source_file ?? null,
  };
}

/**
 * Yüklenen satırları veritabanına yazar.
 *
 * ÜZERİNE YAZAR, ÇOĞALTMAZ: aynı tarih yeniden yüklenirse satır güncellenir
 * (UNIQUE menu_date + ON CONFLICT). Böylece admin düzeltilmiş dosyayı tekrar
 * yükleyebilir; ay ortasında değişen menü çift kayıt oluşturmaz.
 *
 * `announced_at` bilerek SIFIRLANIR: menü değiştiyse o günün duyurusu artık eski
 * içeriği yansıtır; yeniden duyurulabilmelidir.
 *
 * @param {Array<{menu_date: string, day_name: string, items: string[]}>} rows
 * @param {object} [options]
 * @param {string} [options.sourceFile] Yüklenen dosyanın adı.
 * @param {boolean} [options.replaceAll] true ise mevcut tüm menüler silinir.
 * @returns {{ inserted: number, updated: number, removed: number }}
 */
function saveRows(rows, { sourceFile = null, replaceAll = false } = {}) {
  const upsert = db.prepare(`
    INSERT INTO meal_menus (menu_date, day_name, items, source_file)
    VALUES (@menu_date, @day_name, @items, @source_file)
    ON CONFLICT(menu_date) DO UPDATE SET
      day_name     = excluded.day_name,
      items        = excluded.items,
      source_file  = excluded.source_file,
      announced_at = NULL,
      updated_at   = datetime('now')
  `);

  const run = db.transaction(() => {
    let removed = 0;
    if (replaceAll) {
      removed = db.prepare('DELETE FROM meal_menus').run().changes;
    }

    let inserted = 0;
    let updated = 0;

    for (const row of rows) {
      const existed = !replaceAll && Boolean(getByDate(row.menu_date));
      upsert.run({
        menu_date: row.menu_date,
        day_name: row.day_name ?? '',
        items: JSON.stringify(row.items ?? []),
        source_file: sourceFile,
      });
      if (existed) updated += 1;
      else inserted += 1;
    }

    return { inserted, updated, removed };
  });

  return run();
}

/** Tek bir günün menüsünü siler. */
function removeByDate(menuDate) {
  return db.prepare('DELETE FROM meal_menus WHERE menu_date = ?').run(menuDate).changes > 0;
}

/**
 * Tüm menüleri siler ("Menüyü Sil").
 *
 * Oylar (`meal_votes`) BİLEREK silinmez: geçmiş günlerin katılım sayıları menü
 * kaydından bağımsız bir bilgidir. Oyların da temizlenmesi istenirse
 * `mealVote.service.removeAll()` ayrıca çağrılır.
 */
function removeAll() {
  return db.prepare('DELETE FROM meal_menus').run().changes;
}

/** Bir günün menüsünü "duyuruldu" olarak işaretler (çift gönderim koruması). */
function markAnnounced(menuDate) {
  db.prepare("UPDATE meal_menus SET announced_at = datetime('now') WHERE menu_date = ?").run(menuDate);
}

module.exports = {
  getByDate,
  tomorrowISO,
  getNextMenu,
  nextMenuDateISO,
  list,
  getSummary,
  saveRows,
  removeByDate,
  removeAll,
  markAnnounced,
  dayNameOf,
};
