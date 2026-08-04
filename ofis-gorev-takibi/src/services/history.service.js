'use strict';

/**
 * Görev geçmişi servisi.
 *
 * Her gün için "görev kimdeydi" kaydını tutar. `employee_name` bilerek kopyalanır:
 * çalışan sonradan silinse bile geçmiş okunabilir kalır.
 */

const db = require('../database/connection');
const { todayISO, formatLongTR, formatShortTR, isToday } = require('../utils/date');

/**
 * Bir güne görev kaydı yazar.
 *
 * UNIQUE (duty_type_id, duty_date) kısıtı sayesinde aynı gün ikinci kez çağrılırsa
 * yeni satır açılmaz; mevcut kayıt güncellenir. Bu, cron'un yanlışlıkla iki kez
 * tetiklenmesine karşı koruma sağlar (idempotent).
 *
 * @param {object} params
 * @param {number} params.dutyTypeId
 * @param {object} params.employee   Çalışan kaydı.
 * @param {string} [params.date]     Varsayılan: bugün.
 * @param {'cron'|'manual'} [params.source]
 * @param {boolean} [params.notified] Discord mesajı başarıyla gitti mi?
 * @param {boolean} [params.consumedTurn] Bu görev sıranın sahibinin hakkını yaktı mı?
 *   Görevi ofiste olmadığı için atlanan birinin yerine başkası yaptıysa `false`
 *   olur; o gün sıra ilerlemez. Bkz. rotation.service.completeDuty().
 */
function record({
  dutyTypeId,
  employee,
  date = todayISO(),
  source = 'cron',
  notified = false,
  consumedTurn = false,
}) {
  const result = db.prepare(`
    INSERT INTO duty_history (duty_type_id, employee_id, employee_name, duty_date, source, notified, consumed_turn)
    VALUES (@duty_type_id, @employee_id, @employee_name, @duty_date, @source, @notified, @consumed_turn)
    ON CONFLICT(duty_type_id, duty_date) DO UPDATE SET
      employee_id   = excluded.employee_id,
      employee_name = excluded.employee_name,
      source        = excluded.source,
      notified      = excluded.notified,
      consumed_turn = excluded.consumed_turn
  `).run({
    duty_type_id: dutyTypeId,
    employee_id: employee.id,
    employee_name: employee.full_name,
    duty_date: date,
    source,
    notified: notified ? 1 : 0,
    consumed_turn: consumedTurn ? 1 : 0,
  });

  return result;
}

/** Bir görev türü + tarih için kaydı döner. */
function getByDate(dutyTypeId, date) {
  return db.prepare(
    'SELECT * FROM duty_history WHERE duty_type_id = ? AND duty_date = ?'
  ).get(dutyTypeId, date);
}

/**
 * Bir günün görev kaydını siler.
 *
 * Yalnızca onay sıfırlamada kullanılır: yanlışlıkla "Evet" denip kesinleşen gün
 * yeniden sorulacağı için o günün görevlisi henüz belli değildir. Geçmişte yanlış
 * bir kayıt bırakmaktansa satırı kaldırıp yeniden yazdırmak doğrudur.
 *
 * @returns {boolean} Silinen kayıt var mıydı?
 */
function removeByDate(dutyTypeId, date) {
  const result = db.prepare(
    'DELETE FROM duty_history WHERE duty_type_id = ? AND duty_date = ?'
  ).run(dutyTypeId, date);
  return result.changes > 0;
}

/**
 * Var olan bir kaydın bildirim durumunu günceller.
 * Mesaj yeniden gönderildiğinde sırayı ilerletmeden yalnızca bu alan değişir.
 */
function markNotified(historyId, notified) {
  db.prepare('UPDATE duty_history SET notified = ? WHERE id = ?').run(notified ? 1 : 0, historyId);
}

/**
 * Geçmişi filtreli ve sayfalı olarak listeler.
 *
 * @param {object} options
 * @param {number} [options.dutyTypeId] Belirli bir görev türü.
 * @param {string} [options.from]       Başlangıç tarihi (YYYY-MM-DD).
 * @param {string} [options.to]         Bitiş tarihi (YYYY-MM-DD).
 * @param {number} [options.page]       1'den başlar.
 * @param {number} [options.pageSize]
 * @returns {{ rows: object[], total: number, page: number, pageSize: number, totalPages: number }}
 */
function list({ dutyTypeId = null, from = null, to = null, page = 1, pageSize = 20 } = {}) {
  const where = [];
  const params = {};

  if (dutyTypeId) {
    where.push('h.duty_type_id = @dutyTypeId');
    params.dutyTypeId = dutyTypeId;
  }
  if (from) {
    where.push('h.duty_date >= @from');
    params.from = from;
  }
  if (to) {
    where.push('h.duty_date <= @to');
    params.to = to;
  }

  const whereSql = where.length > 0 ? `WHERE ${where.join(' AND ')}` : '';

  const { total } = db.prepare(`SELECT COUNT(*) AS total FROM duty_history h ${whereSql}`).get(params);

  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const safePage = Math.min(Math.max(1, page), totalPages);

  const rows = db.prepare(`
    SELECT
      h.id, h.duty_date, h.employee_id, h.employee_name, h.source, h.notified, h.consumed_turn,
      d.name AS duty_name, d.emoji AS duty_emoji
    FROM duty_history h
    JOIN duty_types d ON d.id = h.duty_type_id
    ${whereSql}
    ORDER BY h.duty_date DESC, h.id DESC
    LIMIT @limit OFFSET @offset
  `).all({ ...params, limit: pageSize, offset: (safePage - 1) * pageSize });

  // Görünüm katmanının tarih biçimlendirme yükünü almaması için burada zenginleştiriyoruz.
  const enriched = rows.map((row) => ({
    ...row,
    dateLong: formatLongTR(row.duty_date),
    dateShort: formatShortTR(row.duty_date),
    isToday: isToday(row.duty_date),
    // Sıranın sahibi değil, onun yerine ofiste olan biri yapmışsa "vekaleten".
    isStandIn: row.consumed_turn === 0,
  }));

  return { rows: enriched, total, page: safePage, pageSize, totalPages };
}

/** Son N kaydı döner (dashboard'daki özet liste için). */
function getRecent(limit = 5) {
  return list({ page: 1, pageSize: limit }).rows;
}

/**
 * Kişi bazlı özet: kim kaç kez görev yapmış (yük dengesi görünürlüğü).
 */
function getStatsByEmployee(dutyTypeId = null) {
  const whereSql = dutyTypeId ? 'WHERE duty_type_id = @dutyTypeId' : '';
  return db.prepare(`
    SELECT employee_name, COUNT(*) AS duty_count, MAX(duty_date) AS last_duty
    FROM duty_history
    ${whereSql}
    GROUP BY employee_name
    ORDER BY duty_count DESC, employee_name ASC
  `).all(dutyTypeId ? { dutyTypeId } : {});
}

/** Toplam kayıt sayısı. */
function getTotalCount() {
  return db.prepare('SELECT COUNT(*) AS total FROM duty_history').get().total;
}

module.exports = {
  record,
  getByDate,
  removeByDate,
  markNotified,
  list,
  getRecent,
  getStatsByEmployee,
  getTotalCount,
};
