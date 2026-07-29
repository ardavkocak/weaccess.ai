'use strict';

/**
 * Tablo şeması, göçler (migration) ve ilk veri kurulumu.
 *
 * `initializeDatabase()` her açılışta çalışır ve idempotenttir: tablolar varsa
 * dokunmaz, yoksa oluşturur. Böylece mevcut veriler korunur.
 *
 * İKİ AYRI KAVRAM
 * ---------------
 * 1) `duty_types`       — "sıra kimde?" sorusunu taşıyan görev türleri (çay,
 *                          kahve, çöp...). Her birinin kendi rotasyonu ve
 *                          geçmişi vardır.
 *
 * 2) `scheduled_messages` — "ne zaman ne yazılacak?" sorusunu taşıyan mesajlar.
 *                          İki çeşidi vardır:
 *                            kind='duty'     → etkileşimli onay akışını başlatır;
 *                                              "Evet" alınınca geçmişe yazar ve
 *                                              (hak edilmişse) sırayı ilerletir.
 *                            kind='reminder' → sabit hatırlatma metni gönderir,
 *                                              sıraya ve geçmişe DOKUNMAZ.
 *
 * Bu ayrım kritiktir: 10:30/15:00/17:20 hatırlatmaları sıra ilerletmemelidir,
 * yoksa günde bir kişi yerine dört kişinin sırası yanardı.
 *
 * GENİŞLETİLEBİLİRLİK
 * -------------------
 * Yeni görev türü = `duty_types`'a satır + kind='duty' bir `scheduled_messages`
 * satırı. Yeni hatırlatma = kind='reminder' tek satır. Kod değişikliği gerekmez;
 * cron etkin tüm satırları tarar.
 */

const db = require('./connection');
const { config, SETTINGS_SEED_KEYS } = require('../config');
const log = require('../utils/logger').create('db');

/**
 * kind='duty' mesajının varsayılan şablonu.
 *
 * Bu metin GÖREV KANALINA butonlarla gönderilen ONAY SORUSUDUR (bkz.
 * discord/confirmationMessages.js). Admin panelden değiştirebilir; bu yüzden
 * kimin sorulduğunu belirten bir değişken ({name}/{first}/{mention}) içermelidir.
 *
 * Soru ERTESİ İŞ GÜNÜ içindir: 17:00'de sorulur, görevli bir gün önceden belli
 * olur. Kanala gider (kişiye değil): ilgili kişi özel mesajlarına bakmıyor
 * olabilir ve cevap gelmezse görevli hiç belirlenemez. {mention} kişiyi
 * etiketler, böylece bildirim alır ama soru herkesin görebildiği yerde durur.
 */
// {gunUn}/{gun}: gün etiketi. Hafta içi "Yarının"/"Yarın", Cuma 17:00'de sorulan
// Pazartesi için otomatik "Pazartesinin"/"Pazartesi" olur (bkz. discord/messages.dayLabel).
const DEFAULT_DUTY_QUESTION =
  '📅 {gunUn} görevlisi belirleniyor\n\nŞu an kontrol edilen kişi:\n\n👤 {mention}\n\n{gun} ofiste misin?';

/**
 * kind='reminder' mesajlarının varsayılan metinleri.
 *
 * Bu metinler KANALA DEĞİL, günün görevlisine ÖZEL MESAJ olarak gider (bkz.
 * services/duty.service.js). Bu yüzden çoğul hitap ("arkadaşımız unutmasın")
 * yerine doğrudan kişiye hitap ederler.
 */
const DUTY_REMINDER_TEXT =
  '🔔 Küçük bir hatırlatma.\n\n' +
  'Bugün görev sırası sende.\n\n' +
  'Lütfen;\n\n' +
  '• ☕ Kahveyi\n' +
  '• 🍵 Çayı\n' +
  '• 🧻 Peçeteyi\n\n' +
  'kontrol ederek eksik varsa tamamlamayı unutma.';

const DEFAULT_REMINDER_TEMPLATES = {
  tea_check_1: DUTY_REMINDER_TEXT,
  tea_check_2: DUTY_REMINDER_TEXT,
  end_of_day:
    '🧹 Gün sonu hatırlatması. Çöpleri atmayı ve bulaşık makinesini kontrol etmeyi unutma. ' +
    'İyi çalışmalar.',
};

/** Hatırlatma metinlerinin DM'e çevrildiğini işaretleyen ayar anahtarı. */
const REMINDER_DM_MIGRATION_KEY = 'reminder_dm_migrated';

/** Görev bildiriminin bir gün öncesine alındığını işaretleyen ayar anahtarı. */
const DAY_AHEAD_MIGRATION_KEY = 'day_ahead_notification_migrated';

/**
 * Artık kullanılmayan görev sorusu varsayılanları.
 *
 * Metin geliştirme sürecinde birkaç kez değişti. Göç yalnızca bu listedekileri
 * yeniler; admin panelden kendi metnini yazdıysa listede olmayacağı için
 * korunur. Yeni bir varsayılan belirlenirse eskisi buraya eklenmelidir.
 */
const OUTDATED_DUTY_QUESTIONS = [
  '☕ Günaydın. Bugünkü sıradaki kişi {mention}. {first} bugün ofiste mi?',
  '📋 Merhaba {first}, yarın ofis görev sırası sende.\n\nYarın ofiste olacak mısın?',
  '📋 Yarın ofis görev sırası {mention} kişisinde.\n\n{first} yarın ofiste olacak mı?',
  '📅 Yarın ofiste olacak mısın?\n\n👤 {mention}\n\nYarın ofiste misin?',
];

/**
 * Görev sorusu metninin hangi sürüme kadar güncellendiğini işaretleyen anahtar.
 *
 * Varsayılan metin her değiştiğinde bu anahtarın SÜRÜMÜ ARTIRILIR: eski sürümü
 * işaretlemiş kurulumlar göçü bir kez daha çalıştırır ve yeni varsayılana geçer.
 * Anahtar aynı kalsaydı göç "zaten yapıldı" deyip metni eski bırakırdı.
 */
const CHANNEL_QUESTION_MIGRATION_KEY = 'duty_question_channel_migrated_v4';

/** Ertesi gün görevlisinin belirlendiği saat. */
const DAY_AHEAD_SEND_TIME = '17:00';

/** Tabloları oluşturur (yoksa). */
function createTables() {
  db.exec(`
    -- Çalışanlar. position sütunu görev sırasındaki yeri belirler.
    CREATE TABLE IF NOT EXISTS employees (
      id              INTEGER PRIMARY KEY AUTOINCREMENT,
      full_name       TEXT    NOT NULL,
      discord_user_id TEXT,
      is_active       INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
      position        INTEGER NOT NULL,
      created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
    );

    -- Görev türleri (çay, kahve, çöp...). Rotasyonun sahibi.
    CREATE TABLE IF NOT EXISTS duty_types (
      id         INTEGER PRIMARY KEY AUTOINCREMENT,
      key        TEXT    NOT NULL UNIQUE,
      name       TEXT    NOT NULL,
      emoji      TEXT    NOT NULL DEFAULT '',
      is_enabled INTEGER NOT NULL DEFAULT 1 CHECK (is_enabled IN (0, 1)),
      created_at TEXT    NOT NULL DEFAULT (datetime('now'))
    );

    -- Her görev türü için sıranın kimde olduğunu tutar (tür başına tek satır).
    CREATE TABLE IF NOT EXISTS rotation_state (
      duty_type_id        INTEGER PRIMARY KEY,
      current_employee_id INTEGER,
      updated_at          TEXT NOT NULL DEFAULT (datetime('now')),
      FOREIGN KEY (duty_type_id)        REFERENCES duty_types(id) ON DELETE CASCADE,
      FOREIGN KEY (current_employee_id) REFERENCES employees(id)  ON DELETE SET NULL
    );

    -- Bu TURDA görevini yapmış çalışanlar. Bir kişi görevini yaptığında buraya
    -- eklenir ve sıra tekrar kendisine gelene (tur bitene) kadar aday olmaz;
    -- böylece görev yapan kişi arka arkaya tekrar görev almaz. Herkes bir kez
    -- yaptığında tur tamamlanır ve tablo temizlenir (bkz. rotation.service).
    CREATE TABLE IF NOT EXISTS duty_cycle_served (
      duty_type_id INTEGER NOT NULL,
      employee_id  INTEGER NOT NULL,
      served_at    TEXT    NOT NULL DEFAULT (datetime('now')),
      PRIMARY KEY (duty_type_id, employee_id),
      FOREIGN KEY (duty_type_id) REFERENCES duty_types(id) ON DELETE CASCADE,
      FOREIGN KEY (employee_id)  REFERENCES employees(id)  ON DELETE CASCADE
    );

    -- Zamanlanmış mesajlar: ne zaman, ne yazılacak, sıra ilerleyecek mi?
    CREATE TABLE IF NOT EXISTS scheduled_messages (
      id               INTEGER PRIMARY KEY AUTOINCREMENT,
      key              TEXT    NOT NULL UNIQUE,
      name             TEXT    NOT NULL,
      send_time        TEXT    NOT NULL,   -- 'SS:DD'
      message_template TEXT    NOT NULL,
      kind             TEXT    NOT NULL DEFAULT 'reminder' CHECK (kind IN ('duty', 'reminder')),
      duty_type_id     INTEGER,            -- kind='duty' ise zorunlu
      is_enabled       INTEGER NOT NULL DEFAULT 1 CHECK (is_enabled IN (0, 1)),
      sort_order       INTEGER NOT NULL DEFAULT 0,
      created_at       TEXT    NOT NULL DEFAULT (datetime('now')),
      FOREIGN KEY (duty_type_id) REFERENCES duty_types(id) ON DELETE CASCADE
    );

    -- Günlük görev geçmişi.
    -- employee_name bilerek kopyalanır (snapshot): çalışan sonradan silinse bile
    -- geçmiş kaydı "o gün görev kimdeydi" sorusunu yanıtlamaya devam etsin.
    CREATE TABLE IF NOT EXISTS duty_history (
      id            INTEGER PRIMARY KEY AUTOINCREMENT,
      duty_type_id  INTEGER NOT NULL,
      employee_id   INTEGER,
      employee_name TEXT    NOT NULL,
      duty_date     TEXT    NOT NULL,
      source        TEXT    NOT NULL DEFAULT 'cron' CHECK (source IN ('cron', 'manual')),
      notified      INTEGER NOT NULL DEFAULT 0 CHECK (notified IN (0, 1)),
      -- Bu görev, sıranın sahibinin hakkını yaktı mı?
      -- 1 = görevi sıranın sahibi yaptı, rotasyon bir sonraki kişiye ilerledi.
      -- 0 = görevi sıranın sahibi değil, ofiste olan başka biri yaptı; sıra
      --     yerinde kaldı ve ertesi gün yine aynı kişiden sorulacak.
      consumed_turn INTEGER NOT NULL DEFAULT 0 CHECK (consumed_turn IN (0, 1)),
      created_at    TEXT    NOT NULL DEFAULT (datetime('now')),
      FOREIGN KEY (duty_type_id) REFERENCES duty_types(id) ON DELETE CASCADE,
      FOREIGN KEY (employee_id)  REFERENCES employees(id)  ON DELETE SET NULL,
      -- Aynı gün + aynı görev türü için tek kayıt: cron iki kez tetiklense bile
      -- mükerrer satır oluşmaz.
      UNIQUE (duty_type_id, duty_date)
    );

    -- Panelden yönetilen anahtar/değer ayarları.
    CREATE TABLE IF NOT EXISTS settings (
      key        TEXT PRIMARY KEY,
      value      TEXT NOT NULL DEFAULT '',
      updated_at TEXT NOT NULL DEFAULT (datetime('now'))
    );

    -- Etkileşimli sabah görev onayı (Discord butonlu akış).
    -- Bir gün + görev türü için TEK akış. Akış Discord'da tek bir mesajla yürür;
    -- "Hayır" cevaplarında aynı mesaj düzenlenerek sıradaki kişiye geçilir, ilk
    -- "Evet"te kesinleşir. message_id/channel_id saklandığı için sunucu yeniden
    -- başlasa bile mevcut mesajdaki butonlar çalışmaya devam eder.
    CREATE TABLE IF NOT EXISTS duty_confirmations (
      id                    INTEGER PRIMARY KEY AUTOINCREMENT,
      duty_type_id          INTEGER NOT NULL,
      duty_date             TEXT    NOT NULL,
      status                TEXT    NOT NULL DEFAULT 'pending'
                              CHECK (status IN ('pending', 'confirmed', 'exhausted')),
      step                  INTEGER NOT NULL DEFAULT 0,   -- kaçıncı kişi soruluyor (0 = ilk)
      source                TEXT    NOT NULL DEFAULT 'cron' CHECK (source IN ('cron', 'manual')),
      start_employee_id     INTEGER,                      -- ilk sorulan kişi (tam tur tespiti için)
      candidate_employee_id INTEGER,                      -- şu an sorulan kişi
      candidate_name        TEXT,                         -- snapshot
      previous_name         TEXT,                         -- son "Hayır" denen kişi (mesaj metni için)
      confirmed_employee_id INTEGER,                      -- kesinleşen görevli
      confirmed_name        TEXT,
      channel_id            TEXT,
      message_id            TEXT,
      -- Panelden kaç kez sıfırlandı (yanlışlıkla "Evet"e basıldığında).
      -- Denetim kayıtları (duty_confirmation_events) sıfırlamada SİLİNMEZ;
      -- bu sayaç, eski cevapların hangi turdan kaldığını anlamayı sağlar.
      reset_count           INTEGER NOT NULL DEFAULT 0,
      created_at            TEXT NOT NULL DEFAULT (datetime('now')),
      updated_at            TEXT NOT NULL DEFAULT (datetime('now')),
      FOREIGN KEY (duty_type_id)          REFERENCES duty_types(id) ON DELETE CASCADE,
      FOREIGN KEY (start_employee_id)     REFERENCES employees(id)  ON DELETE SET NULL,
      FOREIGN KEY (candidate_employee_id) REFERENCES employees(id)  ON DELETE SET NULL,
      FOREIGN KEY (confirmed_employee_id) REFERENCES employees(id)  ON DELETE SET NULL,
      UNIQUE (duty_type_id, duty_date)
    );

    -- Onay akışındaki her cevabın denetim kaydı: kime, ne cevap verildi, kim verdi.
    CREATE TABLE IF NOT EXISTS duty_confirmation_events (
      id                    INTEGER PRIMARY KEY AUTOINCREMENT,
      confirmation_id       INTEGER NOT NULL,
      step                  INTEGER NOT NULL,
      candidate_employee_id INTEGER,
      candidate_name        TEXT,
      answer                TEXT NOT NULL CHECK (answer IN ('yes', 'no')),
      discord_user_id       TEXT,
      discord_user_name     TEXT,
      created_at            TEXT NOT NULL DEFAULT (datetime('now')),
      FOREIGN KEY (confirmation_id) REFERENCES duty_confirmations(id) ON DELETE CASCADE
    );

    -- ─────────────────────────── Yemek menüsü modülü ───────────────────────────
    -- Görev takibinden BAĞIMSIZ bir modüldür: kendi tabloları, kendi zamanlayıcısı
    -- ve kendi Discord mesajı vardır. Görev tablolarıyla hiçbir yabancı anahtar
    -- ilişkisi yoktur; modül tamamen kaldırılsa görev sistemi etkilenmez.

    -- Bir günün menüsü. Excel YALNIZCA yükleme anında okunur; sonrasında sistem
    -- hep bu tabloyu kullanır.
    CREATE TABLE IF NOT EXISTS meal_menus (
      id           INTEGER PRIMARY KEY AUTOINCREMENT,
      menu_date    TEXT    NOT NULL UNIQUE,     -- 'YYYY-MM-DD'
      day_name     TEXT    NOT NULL DEFAULT '', -- Excel'deki gün adı (boşsa tarihten üretilir)
      -- Yemekler JSON dizisi olarak tutulur: ["Mercimek Çorbası", "Tavuk Sote", ...]
      -- Excel'de kaç sütun/satır olduğu dosyadan dosyaya değiştiği için sabit
      -- sütunlar yerine sıralı liste saklanır.
      items        TEXT    NOT NULL,
      source_file  TEXT,                        -- yüklendiği dosyanın adı (panelde gösterilir)
      announced_at TEXT,                        -- Discord'a duyurulduğu an; çift gönderimi önler
      created_at   TEXT    NOT NULL DEFAULT (datetime('now')),
      updated_at   TEXT    NOT NULL DEFAULT (datetime('now'))
    );

    -- Yarının menüsü için "yiyeceğim / yemeyeceğim" oyları.
    --
    -- menu_id yerine menu_date ile ilişkilendirilir: admin ay ortasında dosyayı
    -- yeniden yüklerse menü satırları silinip yeniden yazılır, oylar ise güne ait
    -- olduğu için korunmalıdır.
    --
    -- UNIQUE (menu_date, discord_user_id): bir kişi bir gün için TEK oy kullanır.
    -- Karar değiştirme, yeni satır eklemek yerine bu satırın güncellenmesidir;
    -- böylece "aynı anda iki oy" veritabanı düzeyinde imkânsızdır.
    CREATE TABLE IF NOT EXISTS meal_votes (
      id                INTEGER PRIMARY KEY AUTOINCREMENT,
      menu_date         TEXT NOT NULL,
      discord_user_id   TEXT NOT NULL,
      discord_user_name TEXT,
      choice            TEXT NOT NULL CHECK (choice IN ('yes', 'no')),
      created_at        TEXT NOT NULL DEFAULT (datetime('now')),
      updated_at        TEXT NOT NULL DEFAULT (datetime('now')),
      UNIQUE (menu_date, discord_user_id)
    );

    CREATE INDEX IF NOT EXISTS idx_meal_menus_date ON meal_menus(menu_date);
    CREATE INDEX IF NOT EXISTS idx_meal_votes_date ON meal_votes(menu_date);

    CREATE INDEX IF NOT EXISTS idx_employees_position ON employees(position);
    CREATE INDEX IF NOT EXISTS idx_history_date       ON duty_history(duty_date DESC);
    CREATE INDEX IF NOT EXISTS idx_history_type_date  ON duty_history(duty_type_id, duty_date DESC);
    CREATE INDEX IF NOT EXISTS idx_scheduled_enabled  ON scheduled_messages(is_enabled, sort_order);
    CREATE INDEX IF NOT EXISTS idx_confirm_date       ON duty_confirmations(duty_date DESC);
    CREATE INDEX IF NOT EXISTS idx_confirm_events     ON duty_confirmation_events(confirmation_id, id);
  `);
}

/** Bir tabloda sütun var mı? (göçlerin idempotent kalması için) */
function hasColumn(table, column) {
  return db.prepare(`PRAGMA table_info(${table})`).all().some((c) => c.name === column);
}

/**
 * Göç: `duty_history.consumed_turn`.
 *
 * Eski sürümde sıra, görevi kimin yaptığından bağımsız olarak her gün bir adım
 * ilerlerdi; dolayısıyla mevcut tüm kayıtlar "sırayı yakmış" sayılır (1).
 * Yeni kayıtlar `rotation.service.completeDuty()` sonucuna göre yazılır.
 */
function migrateConsumedTurn() {
  if (hasColumn('duty_history', 'consumed_turn')) return;

  log.info('Göç uygulanıyor: duty_history.consumed_turn ekleniyor');
  db.exec(`
    ALTER TABLE duty_history ADD COLUMN consumed_turn INTEGER NOT NULL DEFAULT 0;
    UPDATE duty_history SET consumed_turn = 1;
  `);
  log.info('Göç tamamlandı.');
}

/**
 * Göç: `duty_confirmations.reset_count`.
 *
 * Mevcut akışlar hiç sıfırlanmamış sayılır (0 — sütun varsayılanı).
 */
function migrateResetCount() {
  if (hasColumn('duty_confirmations', 'reset_count')) return;

  log.info('Göç uygulanıyor: duty_confirmations.reset_count ekleniyor');
  db.exec('ALTER TABLE duty_confirmations ADD COLUMN reset_count INTEGER NOT NULL DEFAULT 0');
  log.info('Göç tamamlandı.');
}

/**
 * Göç: kind='duty' şablonunu SORU biçimine çevirir.
 *
 * Etkileşimli onay akışına geçildiğinde sabah mesajının metni koda taşınmış,
 * `message_template` alanı kullanılmaz (ölü) hâle gelmişti. Metin artık yeniden
 * panelden yönetildiği ve doğrudan onay SORUSU olarak gönderildiği için, eski
 * bildirim metinleri ("Bugünkü çay görevlisi: {name}") soru olarak anlamsız
 * kalırdı — butonların altında cevaplanacak bir soru bulunmazdı.
 *
 * Yalnızca soru gibi görünmeyen şablonlar değiştirilir; admin daha önce bilerek
 * bir soru yazmışsa ona dokunulmaz.
 */
function migrateDutyQuestionTemplate() {
  const rows = db.prepare("SELECT id, name, message_template FROM scheduled_messages WHERE kind = 'duty'").all();

  const stale = rows.filter((row) => !/ofiste mi|\?\s*$/i.test(String(row.message_template ?? '').trim()));
  if (stale.length === 0) return;

  log.info(`Göç uygulanıyor: ${stale.length} görev mesajı şablonu onay sorusuna çevriliyor`);

  const update = db.prepare('UPDATE scheduled_messages SET message_template = ? WHERE id = ?');
  const run = db.transaction(() => {
    for (const row of stale) update.run(DEFAULT_DUTY_QUESTION, row.id);
  });
  run();

  log.info('Göç tamamlandı.');
}

/**
 * Göç: görev bildirimini SABAHTAN BİR GÜN ÖNCESİNE taşır. Yalnızca bir kez çalışır.
 *
 * Akış değişti: görevli artık sabah değil, bir önceki iş günü 17:00'de belirlenir
 * ve kişiye DM ile sorulur. Mevcut kurulumlarda `morning_tea` satırı hâlâ 08:05'te
 * ve metni "bugün ofiste mi?" diye soruyor; ikisi de yeni akışta yanlıştır.
 *
 * Bu göç üç şeyi düzeltir: saat, ad ve soru metni. Ayrıca gün içi hatırlatmaların
 * metni de görevliye hitap eden yeni metinle güncellenir.
 *
 * TEK SEFERLİK: bittiğinde `settings`'e işaret bırakılır. Admin sonradan saati
 * veya metni panelden değiştirirse bir daha ezilmez.
 */
function migrateChannelQuestion() {
  const done = db.prepare('SELECT value FROM settings WHERE key = ?').get(CHANNEL_QUESTION_MIGRATION_KEY);
  if (done) return;

  const run = db.transaction(() => {
    // Soru metni birkaç kez değişti (DM üslubu → kanal üslubu → son biçim).
    // Yalnızca ESKİ VARSAYILANLAR yenilenir; admin panelden kendi metnini
    // yazdıysa ona DOKUNULMAZ.
    const rows = db.prepare("SELECT id, message_template FROM scheduled_messages WHERE kind = 'duty'").all();
    let changed = 0;

    for (const row of rows) {
      const text = String(row.message_template ?? '').trim();
      const isOldDefault = OUTDATED_DUTY_QUESTIONS.some((old) => text === old);
      if (!isOldDefault) continue; // Özel metin veya zaten güncel.

      db.prepare('UPDATE scheduled_messages SET message_template = ? WHERE id = ?')
        .run(DEFAULT_DUTY_QUESTION, row.id);
      changed += 1;
    }

    db.prepare("INSERT INTO settings (key, value) VALUES (?, '1') ON CONFLICT(key) DO NOTHING")
      .run(CHANNEL_QUESTION_MIGRATION_KEY);

    return changed;
  });

  const changed = run();
  if (changed > 0) {
    log.info(`Göç uygulandı: ${changed} görev sorusu kanal metnine çevrildi.`);
  }
}

function migrateDayAheadNotification() {
  const done = db.prepare('SELECT value FROM settings WHERE key = ?').get(DAY_AHEAD_MIGRATION_KEY);
  if (done) return;

  const run = db.transaction(() => {
    const duty = db.prepare("SELECT id, send_time, message_template FROM scheduled_messages WHERE kind = 'duty'").all();

    for (const row of duty) {
      // Metin "yarın"dan söz etmiyorsa eski (bugün odaklı) sorudur; yenilenir.
      const isStale = !/yarın/i.test(String(row.message_template ?? ''));

      db.prepare(`
        UPDATE scheduled_messages
        SET send_time = ?, name = ?, message_template = ?
        WHERE id = ?
      `).run(
        DAY_AHEAD_SEND_TIME,
        'Ertesi Gün Görev Bildirimi',
        isStale ? DEFAULT_DUTY_QUESTION : row.message_template,
        row.id
      );
    }

    // Gün içi hatırlatmalar: görevliye hitap eden yeni metin.
    const select = db.prepare("SELECT id FROM scheduled_messages WHERE key = ? AND kind = 'reminder'");
    for (const key of ['tea_check_1', 'tea_check_2']) {
      const row = select.get(key);
      if (row) {
        db.prepare('UPDATE scheduled_messages SET message_template = ? WHERE id = ?')
          .run(DUTY_REMINDER_TEXT, row.id);
      }
    }

    db.prepare("INSERT INTO settings (key, value) VALUES (?, '1') ON CONFLICT(key) DO NOTHING")
      .run(DAY_AHEAD_MIGRATION_KEY);

    return duty.length;
  });

  const changed = run();
  log.info(`Göç uygulandı: görev bildirimi ${DAY_AHEAD_SEND_TIME}'e alındı (bir gün önceden), ${changed} satır güncellendi.`);
}

/**
 * Göç: hatırlatma metinlerini DM diline çevirir. YALNIZCA BİR KEZ çalışır.
 *
 * Hatırlatmalar artık kanala değil, günün görevlisine özel mesaj olarak gidiyor.
 * Eski metinler kanaldaki topluluğa sesleniyordu ("Görevli arkadaşımız
 * unutmasın", "Herkese iyi akşamlar") ve tek kişinin DM kutusunda anlamsız
 * kalıyordu; bu yüzden varsayılan takvimdeki üç hatırlatma kişiye hitap eden
 * metinlerle değiştirilir.
 *
 * TEK SEFERLİK OLMASI KRİTİK: göç tamamlandığında `settings` tablosuna bir
 * işaret bırakılır. Sonraki açılışlarda hiçbir şey yapılmaz; admin metinleri
 * panelden dilediği gibi düzenler ve yazdıkları bir daha ezilmez.
 *
 * Yalnızca varsayılan takvimin hatırlatmaları (tea_check_1/2, end_of_day)
 * kapsamdadır; sonradan eklenen mesajlara dokunulmaz.
 */
function migrateReminderDmTemplates() {
  const done = db.prepare('SELECT value FROM settings WHERE key = ?').get(REMINDER_DM_MIGRATION_KEY);
  if (done) return;

  const select = db.prepare("SELECT id FROM scheduled_messages WHERE key = ? AND kind = 'reminder'");
  const update = db.prepare('UPDATE scheduled_messages SET message_template = ? WHERE id = ?');

  const run = db.transaction(() => {
    let changed = 0;
    for (const [key, template] of Object.entries(DEFAULT_REMINDER_TEMPLATES)) {
      const row = select.get(key);
      if (!row) continue;
      update.run(template, row.id);
      changed += 1;
    }

    db.prepare("INSERT INTO settings (key, value) VALUES (?, '1') ON CONFLICT(key) DO NOTHING")
      .run(REMINDER_DM_MIGRATION_KEY);

    return changed;
  });

  const changed = run();
  if (changed > 0) {
    log.info(`Göç uygulandı: ${changed} hatırlatma metni özel mesaj (DM) diline çevrildi.`);
  }
}

/**
 * Göçler.
 *
 * v1 şemasında mesaj şablonu `duty_types.message_template` sütunundaydı. Artık
 * şablonlar `scheduled_messages` tablosuna taşındı: bir görev türü birden fazla
 * mesaja konu olabilir (sabah bildirimi + gün içi hatırlatmalar) ve şablonun
 * sahibi "gönderilen mesaj"dır, "görev türü" değil.
 *
 * Eski kurulumlardaki şablon kaybolmasın diye önce sabah mesajına kopyalanır,
 * sonra sütun düşürülür.
 */
function migrate() {
  migrateConsumedTurn();
  migrateResetCount();
  // seedSettings()'ten ÖNCE çalışmalı: yeni kanal anahtarlarını eski değerle
  // oluşturur, tohumlama da ON CONFLICT DO NOTHING olduğu için üzerine yazmaz.
  migrateSplitDiscordChannels();

  if (!hasColumn('duty_types', 'message_template')) return; // Zaten güncel.

  log.info('Göç uygulanıyor: duty_types.message_template → scheduled_messages');

  const runMigration = db.transaction(() => {
    // Eski şablonu, varsa, ilgili sabah mesajına taşı.
    const oldRows = db.prepare('SELECT id, key, message_template FROM duty_types').all();

    for (const row of oldRows) {
      const messageKey = `morning_${row.key}`;
      const exists = db.prepare('SELECT 1 FROM scheduled_messages WHERE key = ?').get(messageKey);
      if (exists || !row.message_template) continue;

      db.prepare(`
        INSERT INTO scheduled_messages (key, name, send_time, message_template, kind, duty_type_id, sort_order)
        VALUES (@key, @name, @send_time, @template, 'duty', @dutyTypeId, 0)
      `).run({
        key: messageKey,
        name: 'Sabah Görev Bildirimi',
        send_time: db.prepare("SELECT value FROM settings WHERE key = 'notify_time'").get()?.value || '08:05',
        template: row.message_template,
        dutyTypeId: row.id,
      });
    }

    db.exec('ALTER TABLE duty_types DROP COLUMN message_template');
  });

  runMigration();
  log.info('Göç tamamlandı.');
}

/**
 * İlk kurulumda varsayılan ayarları yazar. Mevcut değerlerin üzerine YAZMAZ.
 * Saat alanları burada değil, seedScheduledMessages() içinde tohumlanır.
 */
function seedSettings() {
  const insert = db.prepare(
    'INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO NOTHING'
  );
  const seedAll = db.transaction((entries) => {
    for (const [key, value] of entries) insert.run(key, String(value));
  });
  seedAll(SETTINGS_SEED_KEYS.map((key) => [key, config.seedSettings[key] ?? '']));
}

/** Varsayılan görev türünü (çay) ekler. Zaten varsa dokunmaz. */
function seedDutyTypes() {
  db.prepare(`
    INSERT INTO duty_types (key, name, emoji)
    VALUES (@key, @name, @emoji)
    ON CONFLICT(key) DO NOTHING
  `).run({ key: 'tea', name: 'Çay', emoji: '☕' });
}

/**
 * Varsayılan günlük mesaj takvimini kurar.
 *
 * Saatler `.env`/ayarlardan gelen değerlerle tohumlanır; sonrasında panelden
 * değiştirilir. Mevcut satırlara DOKUNULMAZ (admin'in düzenlemesi ezilmesin).
 *
 * Şablonlardaki \n karakterleri Discord'da satır sonu olarak görünür.
 */
function seedScheduledMessages() {
  const tea = db.prepare("SELECT id FROM duty_types WHERE key = 'tea'").get();
  if (!tea) return;

  const defaults = [
    {
      key: 'morning_tea',
      // Ad ve saat değişti: bildirim artık sabah değil, BİR GÜN ÖNCEDEN akşam
      // gidiyor. `key` bilerek korunuyor — mevcut kurulumlardaki satır (ve
      // admin'in düzenlediği metin) kaybolmasın.
      name: 'Ertesi Gün Görev Bildirimi',
      send_time: config.seedSettings.notify_time || '17:00',
      kind: 'duty',
      duty_type_id: tea.id,
      sort_order: 1,
      // kind='duty' şablonu, Discord'a butonlarla gönderilen ONAY SORUSUDUR.
      // {name} veritabanındaki sıradan gelir; sabit değildir.
      message_template: DEFAULT_DUTY_QUESTION,
    },
    {
      key: 'tea_check_1',
      name: 'Birinci Çay Kontrol',
      send_time: config.seedSettings.tea_check_1_time || '10:30',
      kind: 'reminder',
      duty_type_id: null,
      sort_order: 2,
      message_template: DEFAULT_REMINDER_TEMPLATES.tea_check_1,
    },
    {
      key: 'tea_check_2',
      name: 'İkinci Çay Kontrol',
      send_time: config.seedSettings.tea_check_2_time || '15:00',
      kind: 'reminder',
      duty_type_id: null,
      sort_order: 3,
      message_template: DEFAULT_REMINDER_TEMPLATES.tea_check_2,
    },
    {
      key: 'end_of_day',
      name: 'Gün Sonu Hatırlatması',
      send_time: config.seedSettings.end_of_day_time || '17:20',
      kind: 'reminder',
      duty_type_id: null,
      sort_order: 4,
      message_template: DEFAULT_REMINDER_TEMPLATES.end_of_day,
    },
  ];

  const insert = db.prepare(`
    INSERT INTO scheduled_messages (key, name, send_time, message_template, kind, duty_type_id, sort_order)
    VALUES (@key, @name, @send_time, @message_template, @kind, @duty_type_id, @sort_order)
    ON CONFLICT(key) DO NOTHING
  `);
  const seedAll = db.transaction((rows) => {
    for (const row of rows) insert.run(row);
  });
  seedAll(defaults);
}

/**
 * Göç: tek `discord_channel_id` → `discord_duty_channel_id` + `discord_meal_channel_id`.
 *
 * Görev ve yemek sistemleri artık ayrı kanallara yazar. Eski kurulumlarda tek bir
 * kanal ID'si vardır; bu değer HER İKİ yeni ayara da kopyalanır. Böylece göç
 * sonrası davranış birebir aynı kalır (her şey eski kanalına gider) ve admin
 * hazır olduğunda yalnızca yemek kanalını değiştirir.
 *
 * Kopyalama bittikten sonra eski anahtar silinir: iki kaynaklı doğruluk
 * (hangisi geçerli?) karışıklığı yaşanmasın.
 */
function migrateSplitDiscordChannels() {
  const legacy = db.prepare("SELECT value FROM settings WHERE key = 'discord_channel_id'").get();
  if (!legacy) return; // Zaten güncel ya da hiç kurulmamış.

  const value = String(legacy.value ?? '').trim();

  const run = db.transaction(() => {
    // Yeni anahtarlar boşsa eski değerle doldurulur; doluysa dokunulmaz
    // (admin panelden çoktan ayarlamış olabilir).
    const fill = db.prepare(`
      INSERT INTO settings (key, value) VALUES (?, ?)
      ON CONFLICT(key) DO UPDATE SET value = excluded.value
      WHERE settings.value = ''
    `);
    fill.run('discord_duty_channel_id', value);
    fill.run('discord_meal_channel_id', value);

    db.prepare("DELETE FROM settings WHERE key = 'discord_channel_id'").run();
  });

  run();

  log.info(
    value
      ? `Göç uygulandı: Discord kanalı ayrıştırıldı (görev + yemek → ${value}). ` +
        'Yemek kanalını Ayarlar sayfasından değiştirebilirsiniz.'
      : 'Göç uygulandı: Discord kanal ayarı görev/yemek olarak ayrıştırıldı.'
  );
}

/**
 * Yemek menüsü modülünün ayarlarını tohumlar.
 *
 * `SETTINGS_SEED_KEYS` listesine BİLEREK eklenmez: o liste Ayarlar sayfasındaki
 * genel formun alanlarını tanımlar. Duyuru saati modülün kendi sayfasından
 * yönetilir, böylece modül eklenip çıkarıldığında Ayarlar formu değişmez.
 */
function seedMealSettings() {
  db.prepare("INSERT INTO settings (key, value) VALUES ('meal_notify_time', ?) ON CONFLICT(key) DO NOTHING")
    .run(config.seedSettings.meal_notify_time || '15:00');
}

/** Görev türü olup da rotasyon satırı olmayanlar için boş satır açar. */
function ensureRotationRows() {
  db.exec(`
    INSERT INTO rotation_state (duty_type_id, current_employee_id)
    SELECT dt.id, NULL
    FROM duty_types dt
    WHERE NOT EXISTS (
      SELECT 1 FROM rotation_state rs WHERE rs.duty_type_id = dt.id
    )
  `);
}

/** Uygulama açılışında çağrılır. */
function initializeDatabase() {
  createTables();
  migrate();
  seedSettings();
  seedMealSettings();
  seedDutyTypes();
  seedScheduledMessages();
  // Tohumlamadan SONRA: yeni kurulumda satır zaten doğru şablonla gelir,
  // eski kurulumlarda ise mevcut satır soru biçimine çevrilir.
  migrateDutyQuestionTemplate();
  migrateReminderDmTemplates();
  migrateDayAheadNotification();
  migrateChannelQuestion();
  ensureRotationRows();
  log.info('Veritabanı hazır.');
}

module.exports = { initializeDatabase, ensureRotationRows };
