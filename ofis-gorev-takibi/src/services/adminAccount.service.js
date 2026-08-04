'use strict';

/**
 * Yönetici hesabı — kullanıcı adı ve parolanın panelden değiştirilmesi.
 *
 * NEDEN AYRI BİR SERVİS?
 * ----------------------
 * Diğer ayarlar düz metin olarak saklanıp forma geri yazılabilir. Parola öyle
 * değildir: asla düz metin tutulmaz, asla arayüze geri gönderilmez ve
 * değiştirilirken mevcut parola sorulur. Bu kurallar tek yerde toplansın diye
 * `settings.service`'in genel akışından ayrıldı.
 *
 * SAKLAMA BİÇİMİ
 * --------------
 * `settings.admin_password_hash` sütununda:
 *
 *     scrypt$<salt-hex>$<hash-hex>
 *
 * scrypt bilerek seçildi: Node'un kendi `crypto` modülünde var (ek bağımlılık
 * yok) ve kaba kuvvet saldırısını pahalı kılacak şekilde bellek-yoğun çalışır.
 * Her parolanın kendi rastgele tuzu (salt) vardır; aynı parola iki kez farklı
 * hash üretir.
 *
 * .env İLE İLİŞKİSİ
 * -----------------
 * Panelden hiç parola belirlenmediyse `.env`deki ADMIN_USERNAME/ADMIN_PASSWORD
 * geçerlidir (ilk kurulum). Panelden bir kez kaydedildiği anda VERİTABANI
 * ÖNCELİKLİ olur; .env değerleri artık dikkate alınmaz. Böylece admin parolasını
 * dosyaya dokunmadan değiştirebilir.
 */

const crypto = require('crypto');
const settingsService = require('./settings.service');
const { config } = require('../config');

const USERNAME_KEY = 'admin_username';
const PASSWORD_KEY = 'admin_password_hash';

// scrypt maliyet parametresi. Yükseltmek güvenliği artırır ama girişi yavaşlatır;
// 16384 (2^14) masaüstü/küçük sunucu için dengeli bir değerdir.
const SCRYPT_COST = 16384;
const KEY_LENGTH = 64;

const MIN_PASSWORD_LENGTH = 8;
const MIN_USERNAME_LENGTH = 3;
const MAX_USERNAME_LENGTH = 50;

/* ─────────────────────────────── Hash işlemleri ─────────────────────────────── */

/** Parolayı rastgele tuzla hash'ler. */
function hashPassword(password) {
  const salt = crypto.randomBytes(16);
  const hash = crypto.scryptSync(String(password), salt, KEY_LENGTH, { N: SCRYPT_COST });
  return `scrypt$${salt.toString('hex')}$${hash.toString('hex')}`;
}

/**
 * Parolayı saklanan hash ile sabit sürede karşılaştırır.
 * Bozuk/eksik kayıtta sessizce false döner (giriş açık kalmasın).
 */
function verifyHash(password, stored) {
  const parts = String(stored ?? '').split('$');
  if (parts.length !== 3 || parts[0] !== 'scrypt') return false;

  try {
    const salt = Buffer.from(parts[1], 'hex');
    const expected = Buffer.from(parts[2], 'hex');
    const actual = crypto.scryptSync(String(password), salt, expected.length, { N: SCRYPT_COST });
    return crypto.timingSafeEqual(expected, actual);
  } catch {
    return false;
  }
}

/** İki metni sabit sürede karşılaştırır (uzunluk sızıntısı olmasın diye önce SHA-256). */
function safeEqual(a, b) {
  const hashA = crypto.createHash('sha256').update(String(a)).digest();
  const hashB = crypto.createHash('sha256').update(String(b)).digest();
  return crypto.timingSafeEqual(hashA, hashB);
}

/* ─────────────────────────────── Okuma ─────────────────────────────── */

/** Panelden özel bir hesap tanımlandı mı? (yoksa .env geçerlidir) */
function isCustomized() {
  return Boolean(settingsService.get(PASSWORD_KEY));
}

/** Geçerli kullanıcı adı: panelde tanımlıysa o, değilse .env'deki. */
function getUsername() {
  return settingsService.get(USERNAME_KEY) || config.admin.username;
}

/* ─────────────────────────────── Doğrulama ─────────────────────────────── */

/**
 * Giriş bilgilerini doğrular (auth middleware buradan geçer).
 *
 * Kullanıcı adı ve parola kontrolleri DAİMA ikisi de çalıştırılır (erken çıkış
 * yok); yanıt süresinden hangisinin yanlış olduğu anlaşılmasın.
 */
function verifyCredentials(username, password) {
  const userOk = safeEqual(username ?? '', getUsername());

  const storedHash = settingsService.get(PASSWORD_KEY);
  const passOk = storedHash
    ? verifyHash(password ?? '', storedHash)
    : safeEqual(password ?? '', config.admin.password);

  return userOk && passOk;
}

/**
 * Hesap değiştirme formunu doğrular.
 *
 * Mevcut parola HER ZAMAN istenir: oturumu açık bırakılmış bir bilgisayarda
 * başkasının parolayı ele geçirmesini engeller.
 *
 * @param {object} input req.body
 * @returns {{ errors: string[], data?: { username: string, password: string|null } }}
 */
function validateChange(input) {
  const errors = [];

  const username = String(input.admin_username ?? '').trim();
  const currentPassword = String(input.current_password ?? '');
  const newPassword = String(input.new_password ?? '');
  const repeatPassword = String(input.new_password_repeat ?? '');

  // 1) Kimlik kanıtı.
  if (!currentPassword) {
    errors.push('Değişiklik için mevcut parolanızı girmelisiniz.');
  } else if (!verifyCredentials(getUsername(), currentPassword)) {
    errors.push('Mevcut parola hatalı.');
  }

  // 2) Kullanıcı adı.
  if (username.length < MIN_USERNAME_LENGTH || username.length > MAX_USERNAME_LENGTH) {
    errors.push(`Kullanıcı adı ${MIN_USERNAME_LENGTH}-${MAX_USERNAME_LENGTH} karakter olmalıdır.`);
  } else if (/\s/.test(username)) {
    errors.push('Kullanıcı adı boşluk içeremez.');
  }

  // 3) Yeni parola (isteğe bağlı: boş bırakılırsa yalnızca kullanıcı adı değişir).
  if (newPassword || repeatPassword) {
    if (newPassword.length < MIN_PASSWORD_LENGTH) {
      errors.push(`Yeni parola en az ${MIN_PASSWORD_LENGTH} karakter olmalıdır.`);
    }
    if (newPassword !== repeatPassword) {
      errors.push('Yeni parola ve tekrarı aynı değil.');
    }
    if (newPassword && newPassword === currentPassword) {
      errors.push('Yeni parola mevcut parolayla aynı olamaz.');
    }
  }

  if (errors.length > 0) return { errors };

  return { errors: [], data: { username, password: newPassword || null } };
}

/**
 * Doğrulanmış değişikliği kaydeder.
 *
 * Parola boş geçildiyse yalnızca kullanıcı adı güncellenir; mevcut parola hash'i
 * korunur. İlk kayıtta, .env'deki parola panele taşınsın diye hash mutlaka yazılır.
 *
 * @returns {{ usernameChanged: boolean, passwordChanged: boolean }}
 */
function saveChange({ username, password }) {
  const previousUsername = getUsername();

  settingsService.set(USERNAME_KEY, username);

  let passwordChanged = false;
  if (password) {
    settingsService.set(PASSWORD_KEY, hashPassword(password));
    passwordChanged = true;
  } else if (!isCustomized()) {
    // Henüz panele taşınmamış: .env parolasını hash'leyip veritabanına al ki
    // bundan sonra tek bir kaynak (veritabanı) geçerli olsun.
    settingsService.set(PASSWORD_KEY, hashPassword(config.admin.password));
  }

  return { usernameChanged: username !== previousUsername, passwordChanged };
}

module.exports = {
  verifyCredentials,
  getUsername,
  isCustomized,
  validateChange,
  saveChange,
  // Test edilebilirlik için:
  hashPassword,
  verifyHash,
  MIN_PASSWORD_LENGTH,
};
