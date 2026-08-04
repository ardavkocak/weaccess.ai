'use strict';

/**
 * Yemek katılım oyları — "Yiyeceğim / Yemeyeceğim".
 *
 * TEK OY, DEĞİŞTİRİLEBİLİR
 * ------------------------
 * Bir kişi bir gün için tek oy kullanır. Karar değiştirmek yeni satır eklemez,
 * mevcut satırı GÜNCELLER. Bu kural veritabanı düzeyinde `UNIQUE (menu_date,
 * discord_user_id)` ile garanti altındadır; "aynı anda iki oy" durumu koda bağlı
 * değildir, şema gereği imkânsızdır.
 *
 * EŞ ZAMANLILIK
 * -------------
 * `castVote` tamamen SENKRON tek bir SQL işlemidir (better-sqlite3 senkron
 * çalışır). İki kişi aynı anda butona bastığında istekler sıraya girer; sayaçlar
 * her zaman tutarlı okunur. Discord I/O'su bu fonksiyon döndükten SONRA yapılır.
 */

const db = require('../database/connection');
const { todayISO } = require('../utils/date');

/**
 * Bir anketin hâlâ açık olup olmadığını söyler.
 *
 * KURAL: Anket, menünün ait olduğu günün SONUNDA otomatik kapanır — yani
 * `menuDate` bugünden eskiyse anket kapalıdır. Bugüne veya ileri bir tarihe ait
 * anketler açıktır (menü henüz duyurulmamış olsa bile "gelecek" anket sayılır,
 * pratikte oy yalnızca duyurulmuş menülerde Discord butonlarıyla mümkündür).
 *
 * @param {string} menuDate 'YYYY-MM-DD'
 */
function isOpen(menuDate) {
  return menuDate >= todayISO();
}

/**
 * Oyu kaydeder veya değiştirir.
 *
 * @param {object} params
 * @param {string} params.menuDate  'YYYY-MM-DD'
 * @param {string} params.userId    Discord kullanıcı ID'si
 * @param {string} [params.userName] Görünen ad (panelde listelemek için)
 * @param {'yes'|'no'} params.choice
 * @returns {{ changed: boolean, previous: 'yes'|'no'|null, choice: 'yes'|'no', closed?: boolean }}
 *   changed  — oy gerçekten değişti mi? (aynı butona tekrar basıldıysa false)
 *   previous — değişiklikten önceki tercih; ilk oysa null.
 *   closed   — true ise anket kapanmıştır, oy KAYDEDİLMEMİŞTİR.
 */
function castVote({ menuDate, userId, userName = null, choice }) {
  // Anket kapandıysa (gün geçtiyse) ne yeni oy ne de oy değişikliği kabul edilir.
  // Bu kontrol transaction'ın dışındadır çünkü veritabanına hiç dokunmadan erken
  // dönebiliriz — gereksiz bir yazma/transaction açmaya gerek yok.
  if (!isOpen(menuDate)) {
    const existing = db
      .prepare('SELECT choice FROM meal_votes WHERE menu_date = ? AND discord_user_id = ?')
      .get(menuDate, userId);
    return { changed: false, previous: existing?.choice ?? null, choice, closed: true };
  }

  const run = db.transaction(() => {
    const existing = db
      .prepare('SELECT choice FROM meal_votes WHERE menu_date = ? AND discord_user_id = ?')
      .get(menuDate, userId);

    const previous = existing?.choice ?? null;

    if (previous === choice) {
      // Aynı seçeneğe tekrar basıldı: kayıt zaten doğru, gereksiz yazma yapma.
      return { changed: false, previous, choice };
    }

    db.prepare(`
      INSERT INTO meal_votes (menu_date, discord_user_id, discord_user_name, choice)
      VALUES (@menuDate, @userId, @userName, @choice)
      ON CONFLICT(menu_date, discord_user_id) DO UPDATE SET
        choice            = excluded.choice,
        discord_user_name = excluded.discord_user_name,
        updated_at        = datetime('now')
    `).run({ menuDate, userId, userName, choice });

    return { changed: true, previous, choice };
  });

  return run();
}

/**
 * Bir günün katılım sayıları.
 * @returns {{ yes: number, no: number, total: number }}
 */
function getCounts(menuDate) {
  const row = db.prepare(`
    SELECT
      COALESCE(SUM(CASE WHEN choice = 'yes' THEN 1 ELSE 0 END), 0) AS yes,
      COALESCE(SUM(CASE WHEN choice = 'no'  THEN 1 ELSE 0 END), 0) AS no
    FROM meal_votes
    WHERE menu_date = ?
  `).get(menuDate);

  return { yes: row.yes, no: row.no, total: row.yes + row.no };
}

/** Bir günün oy verenleri (panelde kim ne demiş listesi). */
function listVoters(menuDate) {
  return db.prepare(`
    SELECT discord_user_id, discord_user_name, choice, updated_at
    FROM meal_votes
    WHERE menu_date = ?
    ORDER BY choice ASC, updated_at ASC
  `).all(menuDate);
}

/**
 * Bir günün katılım dökümü: kim yiyecek, kim yemeyecek, kim henüz cevap vermedi.
 *
 * YALNIZCA ADMİN PANELİNDE KULLANILIR. Discord mesajında isim listesi
 * gösterilmez; orada sadece sayılar vardır (bkz. discord/mealMessages.js).
 *
 * KİMLİK EŞLEŞTİRME
 * -----------------
 * Oylar Discord kullanıcı ID'siyle tutulur, personel kaydı ise `employees`
 * tablosundadır. İkisi `discord_user_id` üzerinden eşleştirilir:
 *   • Eşleşen oy   → personelin sistemdeki tam adı gösterilir (Discord takma adı
 *                    değişse bile panel tutarlı kalır).
 *   • Eşleşmeyen oy → sunucudaki görünen ad kullanılır ve "personel listesinde
 *                    yok" olarak işaretlenir (misafir/dış kullanıcı).
 *   • Oy vermemiş aktif personel → "cevap vermeyen" listesine düşer.
 *
 * Discord ID'si girilmemiş personel oy KULLANAMAZ; cevap vermeyenler arasında
 * ayrıca işaretlenir ki admin eksik yapılandırmayı fark etsin.
 *
 * @param {string} menuDate
 * @returns {{
 *   yes: object[], no: object[], pending: object[],
 *   counts: { yes: number, no: number, pending: number, total: number, responded: number }
 * }}
 */
function getParticipation(menuDate) {
  const votes = db.prepare(`
    SELECT v.discord_user_id, v.discord_user_name, v.choice, v.updated_at,
           e.id AS employee_id, e.full_name, e.is_active
    FROM meal_votes v
    LEFT JOIN employees e ON e.discord_user_id = v.discord_user_id
    WHERE v.menu_date = ?
    ORDER BY v.updated_at ASC
  `).all(menuDate);

  const toEntry = (row) => ({
    employeeId: row.employee_id ?? null,
    name: row.full_name ?? row.discord_user_name ?? row.discord_user_id,
    discordUserId: row.discord_user_id,
    // Personel listesinde olmayan biri oy vermişse panelde ayırt edilebilsin.
    isExternal: row.employee_id == null,
    updatedAt: row.updated_at,
  });

  const yes = votes.filter((row) => row.choice === 'yes').map(toEntry);
  const no = votes.filter((row) => row.choice === 'no').map(toEntry);

  // Cevap vermeyenler: oy kullanmamış AKTİF personel. Pasif çalışanlar (izinli)
  // beklenen katılımcı sayılmaz, listeyi kirletmesinler.
  const voted = new Set(votes.map((row) => row.discord_user_id));
  const pending = db
    .prepare('SELECT id, full_name, discord_user_id FROM employees WHERE is_active = 1 ORDER BY position ASC')
    .all()
    .filter((employee) => !employee.discord_user_id || !voted.has(employee.discord_user_id))
    .map((employee) => ({
      employeeId: employee.id,
      name: employee.full_name,
      discordUserId: employee.discord_user_id,
      // Discord ID yoksa bu kişi butonlara basamaz; eksiklik panelde belirtilir.
      hasNoDiscordId: !employee.discord_user_id,
    }));

  return {
    yes,
    no,
    pending,
    counts: {
      yes: yes.length,
      no: no.length,
      pending: pending.length,
      responded: yes.length + no.length,
      // Beklenen toplam katılımcı = aktif personel + dışarıdan oy verenler.
      total: pending.length + yes.length + no.length,
    },
  };
}

/** Bir kişinin o güne verdiği oy (yoksa null). */
function getVote(menuDate, userId) {
  const row = db
    .prepare('SELECT choice FROM meal_votes WHERE menu_date = ? AND discord_user_id = ?')
    .get(menuDate, userId);
  return row?.choice ?? null;
}

/** Bir günün tüm oylarını siler (panelden "oyları sıfırla"). */
function removeByDate(menuDate) {
  return db.prepare('DELETE FROM meal_votes WHERE menu_date = ?').run(menuDate).changes;
}

/** Tüm oyları siler. */
function removeAll() {
  return db.prepare('DELETE FROM meal_votes').run().changes;
}

module.exports = {
  castVote,
  isOpen,
  getCounts,
  getParticipation,
  listVoters,
  getVote,
  removeByDate,
  removeAll,
};
