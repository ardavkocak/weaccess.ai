'use strict';

/**
 * Çalışan servisi — ekleme, düzenleme, silme ve sıralama işlemleri.
 *
 * SIRA MANTIĞI
 * ------------
 * Sıra, `employees.position` sütununa göre artan biçimde belirlenir. Pasif
 * çalışanlar listede görünür ama rotasyonda atlanır (bkz. rotation.service.js).
 *
 * POSITION HER ZAMAN 1..N ARALIĞINDA VE BOŞLUKSUZDUR
 * --------------------------------------------------
 * Panelde gösterilen sıra numarası (1., 2., 3. ...) doğrudan `position`'dır;
 * bu yüzden araya ekleme ve taşıma işlemleri komşuları kaydırıp numaraları
 * yeniden sıkıştırır. Sırayı değiştiren her fonksiyon `normalizePositions()` ile
 * başlar; eski kayıtlarda boşluk kalmışsa (silme/göç) kendiliğinden onarılır.
 *
 * ROTASYONLA İLİŞKİSİ
 * -------------------
 * `rotation_state` kişiyi ID ile tutar, position ile değil. Bu yüzden sıralama
 * değiştiğinde sıranın sahibi DEĞİŞMEZ; yalnızca ondan sonra kimin geleceği
 * yeni sıralamaya göre belirlenir.
 */

const db = require('../database/connection');

/** Tüm çalışanları sıra düzeninde döner. */
function getAll() {
  return db.prepare(`
    SELECT id, full_name, discord_user_id, is_active, position, created_at
    FROM employees
    ORDER BY position ASC
  `).all();
}

/** Yalnızca aktif çalışanları sıra düzeninde döner. Rotasyonun temeli budur. */
function getActive() {
  return db.prepare(`
    SELECT id, full_name, discord_user_id, is_active, position, created_at
    FROM employees
    WHERE is_active = 1
    ORDER BY position ASC
  `).all();
}

/** Tek çalışanı id ile getirir. Yoksa undefined. */
function getById(id) {
  return db.prepare(`
    SELECT id, full_name, discord_user_id, is_active, position, created_at
    FROM employees
    WHERE id = ?
  `).get(id);
}

/** Toplam ve aktif çalışan sayısı (dashboard kartları için). */
function getCounts() {
  const row = db.prepare(`
    SELECT
      COUNT(*)                                   AS total,
      COALESCE(SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END), 0) AS active
    FROM employees
  `).get();
  return { total: row.total, active: row.active, passive: row.total - row.active };
}

/**
 * Formdan gelen çalışan verisini doğrular ve normalize eder.
 *
 * @param {object} input Ham form verisi.
 * @param {number|null} excludeId Düzenlemede kendi kaydını çakışma kontrolünden çıkarır.
 * @returns {{ errors: string[], data?: object }}
 */
function validate(input, excludeId = null) {
  const errors = [];

  const fullName = String(input.full_name ?? '').trim();
  if (!fullName) {
    errors.push('Ad soyad boş bırakılamaz.');
  } else if (fullName.length < 2) {
    errors.push('Ad soyad en az 2 karakter olmalıdır.');
  } else if (fullName.length > 100) {
    errors.push('Ad soyad en fazla 100 karakter olabilir.');
  }

  // Discord kullanıcı ID'si isteğe bağlıdır; girildiyse snowflake formatında olmalı.
  const discordUserId = String(input.discord_user_id ?? '').trim();
  if (discordUserId && !/^\d{17,20}$/.test(discordUserId)) {
    errors.push('Discord kullanıcı ID yalnızca rakamlardan oluşmalı ve 17-20 haneli olmalıdır.');
  }

  // Aynı Discord ID'nin iki kişide olması etiketlemeyi bozar; engelliyoruz.
  if (discordUserId) {
    const clash = excludeId
      ? db.prepare('SELECT id FROM employees WHERE discord_user_id = ? AND id != ?').get(discordUserId, excludeId)
      : db.prepare('SELECT id FROM employees WHERE discord_user_id = ?').get(discordUserId);
    if (clash) errors.push('Bu Discord kullanıcı ID başka bir çalışana tanımlı.');
  }

  if (errors.length > 0) return { errors };

  return {
    errors: [],
    data: {
      full_name: fullName,
      discord_user_id: discordUserId || null,
      // Checkbox işaretli değilse alan hiç gelmez; bu durumda pasif kabul edilir.
      is_active: input.is_active === 'on' || input.is_active === true || input.is_active === '1' ? 1 : 0,
    },
  };
}

/** Toplam çalışan sayısı (sıra hesapları için). */
function getTotal() {
  return db.prepare('SELECT COUNT(*) AS total FROM employees').get().total;
}

/**
 * `position` değerlerini mevcut sırayı koruyarak 1..N olarak yeniden numaralar.
 *
 * Sırayı değiştiren tüm işlemler buradan başlar: böylece "3. sıraya ekle" gibi
 * istekler, veritabanında boşluk veya çakışma olsa bile panelde görünen numarayla
 * birebir aynı sonucu verir. (transaction içinde çağrılmalıdır)
 */
function normalizePositions() {
  const rows = db.prepare('SELECT id FROM employees ORDER BY position ASC, id ASC').all();
  const setPosition = db.prepare('UPDATE employees SET position = ? WHERE id = ?');
  rows.forEach((row, index) => setPosition.run(index + 1, row.id));
}

/**
 * Bir sıra numarasını geçerli aralığa çeker.
 *
 * @param {*} value Ham girdi (form alanı olabilir).
 * @param {number} max İzin verilen en büyük değer.
 * @param {number|null} fallback Girdi boş/geçersizse dönecek değer.
 */
function normalizePositionInput(value, max, fallback = null) {
  if (value === undefined || value === null || String(value).trim() === '') return fallback;
  const parsed = Number.parseInt(String(value), 10);
  if (!Number.isFinite(parsed)) return fallback;
  return Math.min(Math.max(parsed, 1), max);
}

/**
 * Yeni çalışanı sıraya ekler.
 *
 * @param {object} data validate()'ten geçmiş çalışan verisi.
 * @param {number|null} [position] 1 tabanlı hedef sıra. null/atlanırsa çalışan
 *   sıranın EN SONUNA eklenir (varsayılan davranış). Aralık dışı değerler
 *   kırpılır.
 *
 * Hedeften itibaren tüm çalışanlar bir basamak aşağı kayar:
 *   Beril, Doğa, Ahmet, Ayşe + (Mustafa, 3. sıra)
 *   → Beril, Doğa, Mustafa, Ahmet, Ayşe
 */
function create(data, position = null) {
  const run = db.transaction(() => {
    normalizePositions();

    // Sona ekleme dahil olduğu için üst sınır mevcut sayı + 1'dir.
    const target = normalizePositionInput(position, getTotal() + 1, getTotal() + 1);

    // Hedef ve sonrasındaki herkesi bir basamak aşağı it, yeri aç.
    db.prepare('UPDATE employees SET position = position + 1 WHERE position >= ?').run(target);

    const result = db.prepare(`
      INSERT INTO employees (full_name, discord_user_id, is_active, position)
      VALUES (@full_name, @discord_user_id, @is_active, @position)
    `).run({ ...data, position: target });

    return getById(result.lastInsertRowid);
  });

  return run();
}

/** Mevcut çalışanı günceller. */
function update(id, data) {
  db.prepare(`
    UPDATE employees
    SET full_name = @full_name, discord_user_id = @discord_user_id, is_active = @is_active
    WHERE id = @id
  `).run({ ...data, id });

  return getById(id);
}

/** Aktif/pasif durumunu tersine çevirir ve yeni durumu döner. */
function toggleActive(id) {
  const employee = getById(id);
  if (!employee) return null;

  const nextState = employee.is_active === 1 ? 0 : 1;
  db.prepare('UPDATE employees SET is_active = ? WHERE id = ?').run(nextState, id);
  return getById(id);
}

/**
 * Çalışanı siler ve kalan çalışanların position değerlerini sıkıştırır
 * (1, 2, 3... şeklinde boşluksuz kalsın).
 *
 * duty_history.employee_id FK'si ON DELETE SET NULL olduğu için geçmiş kayıtları
 * silinmez; employee_name snapshot'ı sayesinde isim görünmeye devam eder.
 */
function remove(id) {
  const removeAndCompact = db.transaction((employeeId) => {
    const employee = getById(employeeId);
    if (!employee) return false;

    db.prepare('DELETE FROM employees WHERE id = ?').run(employeeId);
    // Silinenden sonraki herkesi bir basamak yukarı çek.
    db.prepare('UPDATE employees SET position = position - 1 WHERE position > ?').run(employee.position);
    return true;
  });

  return removeAndCompact(id);
}

/**
 * Çalışanı sırada bir yukarı/aşağı taşır (position takası).
 *
 * @param {number} id
 * @param {'up'|'down'} direction
 * @returns {boolean} Taşıma yapıldıysa true; sınırdaysa false.
 */
function move(id, direction) {
  const swap = db.transaction((employeeId, dir) => {
    const employee = getById(employeeId);
    if (!employee) return false;

    // Komşuyu bul: yukarı için kendinden küçük en büyük, aşağı için kendinden
    // büyük en küçük position.
    const neighbour = dir === 'up'
      ? db.prepare('SELECT id, position FROM employees WHERE position < ? ORDER BY position DESC LIMIT 1').get(employee.position)
      : db.prepare('SELECT id, position FROM employees WHERE position > ? ORDER BY position ASC LIMIT 1').get(employee.position);

    if (!neighbour) return false; // Zaten listenin başında/sonunda.

    // UNIQUE kısıtı olmadığı için doğrudan takas güvenli.
    db.prepare('UPDATE employees SET position = ? WHERE id = ?').run(neighbour.position, employee.id);
    db.prepare('UPDATE employees SET position = ? WHERE id = ?').run(employee.position, neighbour.id);
    return true;
  });

  return swap(id, direction);
}

/**
 * Çalışanı doğrudan belirli bir sıra numarasına taşır (numara girişi ve
 * sürükle-bırak tek kişilik hâli).
 *
 * Aradaki çalışanlar otomatik kayar; kimse aynı numarayı paylaşmaz:
 *   Beril, Doğa, Ahmet, Ayşe + (Ayşe → 2. sıra)
 *   → Beril, Ayşe, Doğa, Ahmet
 *
 * @param {number} id
 * @param {*} position 1 tabanlı hedef sıra (aralık dışıysa kırpılır).
 * @returns {{ ok: boolean, message?: string, employee?: object, from?: number, to?: number }}
 */
function moveToPosition(id, position) {
  const run = db.transaction(() => {
    normalizePositions();

    const employee = getById(id);
    if (!employee) return { ok: false, message: 'Çalışan bulunamadı.' };

    const target = normalizePositionInput(position, getTotal(), null);
    if (target === null) return { ok: false, message: 'Geçerli bir sıra numarası girin.' };
    if (target === employee.position) {
      return { ok: true, employee, from: employee.position, to: target };
    }

    if (target < employee.position) {
      // Yukarı taşınıyor: arada kalanlar bir basamak aşağı iner.
      db.prepare('UPDATE employees SET position = position + 1 WHERE position >= ? AND position < ?')
        .run(target, employee.position);
    } else {
      // Aşağı taşınıyor: arada kalanlar bir basamak yukarı çıkar.
      db.prepare('UPDATE employees SET position = position - 1 WHERE position > ? AND position <= ?')
        .run(employee.position, target);
    }

    db.prepare('UPDATE employees SET position = ? WHERE id = ?').run(target, id);

    return { ok: true, employee: getById(id), from: employee.position, to: target };
  });

  return run();
}

/**
 * Tüm sırayı verilen ID dizisine göre yeniden yazar (sürükle-bırak kaydı).
 *
 * Kısmi/bozuk gönderim sırayı bozmasın diye liste ÖNCE doğrulanır: eksik, fazla,
 * tekrarlı veya tanınmayan ID varsa hiçbir şey değişmez. (Tarayıcı listeyi
 * gönderirken bir kişi başka sekmede silinmiş olabilir.)
 *
 * @param {number[]} ids Yeni sıradaki çalışan ID'leri, baştan sona.
 * @returns {{ ok: boolean, message?: string }}
 */
function reorder(ids) {
  const run = db.transaction(() => {
    const current = getAll();
    const knownIds = new Set(current.map((employee) => employee.id));

    if (!Array.isArray(ids) || ids.length !== current.length) {
      return { ok: false, message: 'Sıralama listesi güncel değil. Sayfayı yenileyip tekrar deneyin.' };
    }

    const seen = new Set();
    for (const id of ids) {
      if (!knownIds.has(id) || seen.has(id)) {
        return { ok: false, message: 'Sıralama listesi geçersiz. Sayfayı yenileyip tekrar deneyin.' };
      }
      seen.add(id);
    }

    const setPosition = db.prepare('UPDATE employees SET position = ? WHERE id = ?');
    ids.forEach((id, index) => setPosition.run(index + 1, id));

    return { ok: true };
  });

  return run();
}

module.exports = {
  getAll,
  getActive,
  getById,
  getCounts,
  getTotal,
  validate,
  create,
  update,
  toggleActive,
  remove,
  move,
  moveToPosition,
  reorder,
  normalizePositions,
};
