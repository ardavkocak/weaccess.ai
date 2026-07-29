'use strict';

/**
 * Rotasyon servisi — sistemin kalbi. "Sıra kimde?" sorusunu yanıtlar.
 *
 * VERİ MODELİ
 * -----------
 * `rotation_state.current_employee_id` = SIRANIN SAHİBİ: bir sonraki görev
 * dağıtımında İLK sorulacak kişi. Soru her zaman bu kişiden başlar.
 *
 * TEMEL KURAL: SIRA, GÖREVİ YAPANIN SONRASINDAN DEVAM EDER
 * -------------------------------------------------------
 * Görevi FİİLEN yapan kişi sırasını tamamlamış sayılır ve sıra onun HEMEN
 * SONRASINA geçer (`completeDuty`). "Hayır" diyip atlanan kişiler haklarını
 * kaybetmez — rotasyon bir döngü olduğu için sıraları tekrar geldiğinde yeniden
 * sorulurlar; ama aynı turda gereksiz yere üst üste sorulmazlar.
 *
 * Örnek — sıra: Doğa → Hasan → Arda
 *
 *   1. dağıtım  Doğa? Hayır → Hasan? Evet
 *               Görevi Hasan yaptı → sıra Hasan'ın sonrasına, Arda'ya geçer.
 *   2. dağıtım  Arda'dan sorulur (sistem tekrar Doğa'ya dönüp durmaz).
 *
 * PANEL GÖSTERİMİ
 * ---------------
 * "Bugünkü görevli" (duty_history kaydı) ile "sıranın sahibi" (current) farklı
 * kişilerdir: kayıt o günü kimin yaptığını, current bir sonraki dağıtımda kimin
 * ilk sorulacağını söyler.
 *
 * PASİF ÇALIŞANLAR
 * ----------------
 * Rotasyon yalnızca `is_active = 1` olan çalışanlar üzerinde döner. Sıradaki kişi
 * pasife alınırsa `resolveCurrent()` onu otomatik olarak atlar ve durumu kalıcı
 * hale getirir. (İzinli çalışan = pasife alınmış çalışan.)
 */

const db = require('../database/connection');
const employeeService = require('./employee.service');
const dutyTypeService = require('./dutyType.service');
const { todayISO } = require('../utils/date');

/** Bir görev türünün rotasyon satırını okur (yoksa oluşturur). */
function getState(dutyTypeId) {
  let state = db.prepare('SELECT * FROM rotation_state WHERE duty_type_id = ?').get(dutyTypeId);
  if (!state) {
    db.prepare('INSERT INTO rotation_state (duty_type_id, current_employee_id) VALUES (?, NULL)').run(dutyTypeId);
    state = db.prepare('SELECT * FROM rotation_state WHERE duty_type_id = ?').get(dutyTypeId);
  }
  return state;
}

/** `current` alanını doğrudan yazar. */
function setCurrent(dutyTypeId, employeeId) {
  getState(dutyTypeId); // Satırın varlığını garantile.
  db.prepare(`
    UPDATE rotation_state
    SET current_employee_id = ?, updated_at = datetime('now')
    WHERE duty_type_id = ?
  `).run(employeeId ?? null, dutyTypeId);
}

/**
 * Verilen çalışandan SONRAKİ aktif çalışanı bulur; liste sonunda başa sarar.
 *
 * @param {number|null} employeeId Referans çalışan. null ise ilk aktif kişi döner.
 * @returns {object|null} Aktif çalışan yoksa null.
 */
function findNextActive(employeeId) {
  const actives = employeeService.getActive();
  if (actives.length === 0) return null;
  if (employeeId == null) return actives[0];

  const index = actives.findIndex((e) => e.id === employeeId);

  if (index !== -1) {
    // Referans kişi aktif listede: bir sonrakine geç, sondaysa başa sar.
    return actives[(index + 1) % actives.length];
  }

  // Referans kişi aktif listede değil (pasife alınmış olabilir). Sıradaki yeri
  // kaybetmemek için position'ına göre kendisinden sonraki ilk aktifi seçeriz.
  const stale = employeeService.getById(employeeId);
  if (!stale) return actives[0]; // Silinmiş: baştan başla.

  return actives.find((e) => e.position > stale.position) ?? actives[0];
}

/* ───────────────────────────── Tur (cycle) servisi ───────────────────────────── */
/*
 * "Bu turda kim görevini yaptı" bilgisi `duty_cycle_served` tablosunda tutulur.
 * Görev yapan kişi tur bitene kadar tekrar ADAY OLMAZ; böylece aynı kişi arka
 * arkaya görev almaz. Herkes bir kez yaptığında tur tamamlanır ve tablo
 * temizlenir (yeni tur başlar).
 */

/** Bu turda görevini yapmış çalışan ID'lerini küme olarak döner. */
function getServedIds(dutyTypeId) {
  const rows = db.prepare(
    'SELECT employee_id FROM duty_cycle_served WHERE duty_type_id = ?'
  ).all(dutyTypeId);
  return new Set(rows.map((r) => r.employee_id));
}

/** Bir çalışanı "bu turda yaptı" olarak işaretler. */
function markServed(dutyTypeId, employeeId) {
  db.prepare(`
    INSERT INTO duty_cycle_served (duty_type_id, employee_id)
    VALUES (?, ?)
    ON CONFLICT(duty_type_id, employee_id) DO NOTHING
  `).run(dutyTypeId, employeeId);
}

/** Turu sıfırlar (herkes yeniden aday olur). */
function clearServed(dutyTypeId) {
  db.prepare('DELETE FROM duty_cycle_served WHERE duty_type_id = ?').run(dutyTypeId);
}

/** Bir çalışanı tur işaretinden çıkarır (onay sıfırlama / iade için). */
function unmarkServed(dutyTypeId, employeeId) {
  if (employeeId == null) return;
  db.prepare('DELETE FROM duty_cycle_served WHERE duty_type_id = ? AND employee_id = ?')
    .run(dutyTypeId, employeeId);
}

/**
 * Verilen çalışandan sonraki, bu turda HENÜZ GÖREV YAPMAMIŞ aktif çalışanı bulur.
 * Görev yapmış (served) kişileri atlar. Liste sonunda başa sarar.
 *
 * @param {number|null} afterId Referans çalışan (bu kişi hariç sonrakiler taranır).
 * @param {Set<number>} served  Bu turda görev yapanların ID kümesi.
 * @returns {object|null} Uygun aday yoksa null (herkes yapmış demektir).
 */
function nextUnservedAfter(afterId, served) {
  const actives = employeeService.getActive();
  if (actives.length === 0) return null;

  // afterId'nin listedeki yeri; yoksa (pasif/silinmiş) position'a göre yaklaşık yer.
  let startIndex;
  const index = actives.findIndex((e) => e.id === afterId);
  if (afterId == null) {
    startIndex = -1; // baştan başla (ilk aktif dahil)
  } else if (index !== -1) {
    startIndex = index;
  } else {
    const stale = employeeService.getById(afterId);
    const afterPos = stale ? stale.position : -Infinity;
    const found = actives.findIndex((e) => e.position > afterPos);
    startIndex = found === -1 ? actives.length - 1 : found - 1;
  }

  // startIndex'ten sonra dairesel tara, served olanları atla.
  for (let step = 1; step <= actives.length; step += 1) {
    const candidate = actives[(startIndex + step) % actives.length];
    if (!served.has(candidate.id)) return candidate;
  }
  return null; // Herkes bu turda görev yapmış.
}

/** Bu turda henüz görev yapmamış EN ÖNDEKİ (en düşük position) aktif çalışan. */
function frontUnserved(dutyTypeId) {
  const served = getServedIds(dutyTypeId);
  const actives = employeeService.getActive();
  return actives.find((e) => !served.has(e.id)) ?? null;
}

/**
 * Bir sonraki dağıtımda İLK sorulacak kişiyi (turun önünü) döner ve kalıcılaştırır.
 *
 * `current`, turun başladığı kişidir. Bir dağıtım hep buradan başlar. Ancak bu
 * kişi bu turda görevini YAPMIŞSA (served) artık aday değildir; bu durumda tur
 * içinde henüz yapmamış en öndeki kişiye kaydırılır. Kimse kalmadıysa (herkes
 * yapmış) tur tamamlanmıştır; tablo temizlenir ve yeni tur baştan başlar.
 *
 * Ayrıca current pasif/silinmişse otomatik atlanır (eski davranış korunur).
 *
 * @returns {object|null} Bu turda ilk sorulacak çalışan; hiç aktif çalışan yoksa null.
 */
function resolveCurrent(dutyTypeId) {
  const state = getState(dutyTypeId);
  const actives = employeeService.getActive();

  if (actives.length === 0) {
    if (state.current_employee_id != null) setCurrent(dutyTypeId, null);
    return null;
  }

  const served = getServedIds(dutyTypeId);
  const current = state.current_employee_id != null
    ? employeeService.getById(state.current_employee_id)
    : null;

  // Geçerli, aktif ve bu turda henüz yapmamışsa dokunma.
  if (current && current.is_active === 1 && !served.has(current.id)) return current;

  // Aksi halde: pasif/silinmiş veya bu turda görevini yapmış. Turda henüz
  // yapmamış bir sonraki aktif kişiye kaydır.
  let next = nextUnservedAfter(state.current_employee_id, served);

  // Kimse kalmadı → herkes bu turda yaptı: tur tamamlandı, baştan başlat.
  if (!next) {
    clearServed(dutyTypeId);
    next = findNextActive(state.current_employee_id) ?? actives[0];
  }

  setCurrent(dutyTypeId, next ? next.id : null);
  return next;
}

/** Bugünün geçmiş kaydını döner (varsa). */
function getTodayRecord(dutyTypeId) {
  return db.prepare(
    'SELECT * FROM duty_history WHERE duty_type_id = ? AND duty_date = ?'
  ).get(dutyTypeId, todayISO());
}

/**
 * Bir görev türü için panelin ihtiyaç duyduğu tüm rotasyon bilgisini üretir.
 *
 * @returns {{
 *   dutyType: object,
 *   today: object|null,        // Bugünkü görevli (çalışan kaydı veya snapshot)
 *   todayName: string|null,
 *   next: object|null,         // Sıranın sahibi (yarın ilk sorulacak kişi)
 *   isSentToday: boolean,      // Bugünün görevi kesinleşti mi?
 *   isStandIn: boolean,        // Bugünkü görevi sıranın sahibi değil, yerine biri mi yaptı?
 *   queue: object[],           // Tüm çalışanlar, sıra işaretleriyle
 * }}
 */
function getOverview(dutyTypeId) {
  const dutyType = dutyTypeService.getById(dutyTypeId);
  const current = resolveCurrent(dutyTypeId);
  const todayRecord = getTodayRecord(dutyTypeId);
  const isSentToday = Boolean(todayRecord);

  // Bugünkü görevli YALNIZCA geçmiş kaydından okunur.
  //
  // Görevli artık bir gün önceden (dün 17:00'de) belirlenip `duty_history`'ye
  // yazılıyor. Kayıt yoksa bugün için gerçekten görevli atanmamıştır — eskiden
  // olduğu gibi "sıranın sahibi"ne düşmek YANILTICIDIR: sıranın sahibi henüz
  // kendisine soru sorulacak kişidir, bugünün görevlisi değildir. (Panelde
  // "Bugünkü Görevli: Doğa" yazarken görevi Beril'in üstlenmiş olması bu
  // karışıklıktan doğuyordu.)
  let today = null;
  let todayName = null;
  if (isSentToday) {
    today = todayRecord.employee_id ? employeeService.getById(todayRecord.employee_id) : null;
    todayName = todayRecord.employee_name; // Çalışan silinse bile isim durur.
  }

  // Sıradaki = sıranın sahibi, yani bir sonraki 17:00'de İLK sorulacak kişi.
  // `current` bu bilgiyi zaten doğru taşır: görevi sahibi yaptıysa ilerlemiştir,
  // vekaleten biri yaptıysa yerinde durur.
  const next = current;

  // Bugünkü görevi sıranın sahibi değil, yerine ofiste olan biri yaptıysa panelde
  // "sırası yanmadı" notu gösterilir.
  const isStandIn = isSentToday && todayRecord.consumed_turn === 0;

  // Sıra listesi: tüm çalışanlar, bugünkü ve sıradaki işaretlenmiş halde.
  // "Bugün" rozeti yalnızca gerçekten atanmış görevliye takılır.
  const todayId = isSentToday ? todayRecord.employee_id : null;
  const queue = employeeService.getAll().map((employee) => ({
    ...employee,
    isToday: todayId != null && employee.id === todayId,
    // Tek aktif çalışan varsa "bugünkü" ve "sıradaki" aynı kişidir; rozetin
    // iki kez çıkmaması için isToday önceliklidir.
    isNext: next != null && employee.id === next.id && employee.id !== todayId,
  }));

  return { dutyType, today, todayName, next, isSentToday, isStandIn, queue };
}

/**
 * BUGÜNKÜ GÖREVİ bir sonraki aktif çalışana devreder ("Sırayı Geç" butonu).
 *
 * Discord'daki "Hayır" cevabının panel karşılığıdır: devredilen kişi görevi
 * yapmamış sayılır ve SIRA HAKKINI KAYBETMEZ. Sıra yalnızca görevi yeni üstlenen
 * kişi zaten sıranın sahibiyse ilerler (bkz. `completeDuty`).
 *
 * İşleyiş:
 *   1. Bugünün görevlisi (kayıt varsa o, yoksa sıranın sahibi) belirlenir.
 *   2. Görev, ondan sonraki aktif kişiye geçer ve bugünün `duty_history` kaydı
 *      'manual' olarak yazılır/güncellenir.
 *   3. Eski görevli sırasını YAKMIŞSA hakkı kendisine iade edilir; ardından yeni
 *      görevli için `completeDuty` çalışır.
 *   4. Bekleyen bir Discord onay akışı varsa kapatılır (butonlar sonuçlanmış
 *      sayılır); çağıran taraf mesajı güncelleyebilsin diye bilgisi döndürülür.
 *
 * @returns {{
 *   ok: boolean, message: string, from?: string, to?: string,
 *   closedFlow?: { channelId: string, messageId: string, name: string }|null
 * }}
 */
function skipToNext(dutyTypeId) {
  const run = db.transaction(() => {
    const actives = employeeService.getActive();
    if (actives.length === 0) {
      return { ok: false, message: 'Aktif çalışan bulunmadığı için sıra geçilemiyor.' };
    }
    if (actives.length === 1) {
      return { ok: false, message: 'Sırada tek aktif çalışan var; geçilecek başka kişi yok.' };
    }

    const todayRecord = getTodayRecord(dutyTypeId);
    const current = resolveCurrent(dutyTypeId);

    // Bugünün görevlisi kim? (Veri modeli açıklamasına bakınız.)
    const todayHolderId = todayRecord ? todayRecord.employee_id : (current ? current.id : null);
    const fromName = todayRecord ? todayRecord.employee_name : (current ? current.full_name : '—');

    // Eski görevliyi "görevi yapmadı" durumuna al (served'dan çıkar, önü ona ver).
    if (todayRecord && todayRecord.consumed_turn === 1) {
      restoreTurn(dutyTypeId, todayRecord.employee_id);
    }

    // Yeni görevli: eski görevliden sonraki, bu turda henüz görev yapmamış aktif
    // kişi (görev yapanlar atlanır). Herkes yapmışsa yine de bir sonrakine devret.
    const served = getServedIds(dutyTypeId);
    const newHolder = nextUnservedAfter(todayHolderId, served) ?? findNextActive(todayHolderId);
    if (!newHolder) {
      return { ok: false, message: 'Sıradaki aktif çalışan bulunamadı.' };
    }

    // Yeni görevli için görevi tamamla (served'a ekle + turu ilerlet).
    const { consumed } = completeDuty(dutyTypeId, newHolder.id);

    // Lazy require: history → rotation döngüsel bağımlılığını kırar.
    require('./history.service').record({
      dutyTypeId,
      employee: newHolder,
      date: todayISO(),
      source: 'manual',
      notified: todayRecord ? todayRecord.notified === 1 : false,
      consumedTurn: consumed,
    });

    // Bekleyen onay akışı varsa kapat: Discord butonları artık bu kararı ezmesin.
    const closedFlow = require('./dutyConfirmation.service').closeFlowManually(dutyTypeId, newHolder);

    return {
      ok: true,
      message: consumed
        ? `Görev ${fromName} kişisinden ${newHolder.full_name} kişisine geçirildi. Sıra ilerledi.`
        : `Görev ${fromName} kişisinden ${newHolder.full_name} kişisine geçirildi. ${fromName} sırasını kaybetmedi.`,
      from: fromName,
      to: newHolder.full_name,
      closedFlow,
    };
  });

  return run();
}

/**
 * Bir görevin TAMAMLANDIĞINI rotasyona bildirir.
 *
 * KURAL: Görevi FİİLEN yapan kişi bu TURDAKİ hakkını tamamlamış sayılır ve tur
 * bitene kadar tekrar aday olmaz (served'a eklenir). Böylece aynı kişi arka
 * arkaya görev almaz. Herkes bir kez yaptığında tur tamamlanır, tablo temizlenir.
 *
 * Örnek — sıra: Doğa → Hasan → Arda → Zeynep (Doğa sürekli ofiste yok)
 *   Dağıtım 1: Doğa? Hayır → Hasan? Evet   → served={Hasan}, ön hâlâ Doğa
 *   Dağıtım 2: Doğa? Hayır → (Hasan atlanır) Arda? Evet → served={Hasan,Arda}
 *   Dağıtım 3: Doğa? Hayır → (Hasan,Arda atlanır) Zeynep? Evet
 *   Hasan, sıra kendisine tekrar gelene (tur bitene) kadar bir daha sorulmaz.
 *
 * "Hayır" diyen (atlanan) kişiler haklarını kaybetmez: served'a girmezler, bir
 * sonraki dağıtımda yine ilk onlar sorulur.
 *
 * @param {number} dutyTypeId
 * @param {number|null} employeeId Görevi fiilen yapan kişi.
 * @returns {{ consumed: boolean, holder: object|null }}
 *   consumed — her zaman true (görev yapıldıysa served'a eklenir). Geriye dönük
 *              uyum için `duty_history.consumed_turn` alanına yazılır.
 *   holder   — işlem sonrası turun önü (bir sonraki dağıtımda ilk sorulacak kişi).
 */
function completeDuty(dutyTypeId, employeeId) {
  if (employeeId == null) {
    return { consumed: false, holder: resolveCurrent(dutyTypeId) };
  }

  const state = getState(dutyTypeId);
  const wasFront = state.current_employee_id === employeeId;

  // 1) Görevi yapan kişiyi bu tura işaretle → tur bitene kadar tekrar aday olmaz.
  markServed(dutyTypeId, employeeId);

  const served = getServedIds(dutyTypeId);
  const activeIds = employeeService.getActive().map((e) => e.id);
  const allServed = activeIds.length > 0 && activeIds.every((id) => served.has(id));

  if (allServed) {
    // TUR TAMAMLANDI: herkes bir kez yaptı. Tabloyu sıfırla; yeni tur, görevi son
    // yapan kişinin HEMEN SONRASINDAN başlasın (aynı kişi başa dönüp tekrar
    // görev almasın).
    clearServed(dutyTypeId);
    const next = findNextActive(employeeId);
    setCurrent(dutyTypeId, next ? next.id : null);
    return { consumed: true, holder: next };
  }

  if (wasFront) {
    // TURUN ÖNÜ görevini yaptı: önü, turda henüz yapmamış sonraki kişiye taşı.
    const next = nextUnservedAfter(employeeId, served);
    setCurrent(dutyTypeId, next ? next.id : null);
    return { consumed: true, holder: next };
  }

  // Görevi yapan kişi turun önü DEĞİL — ofiste olmayan bir öndekinin yerine
  // vekaleten yaptı. Ön YERİNDE KALIR (o kişi hâlâ aday); yapan kişi yalnızca
  // served'a eklendi ki tur bitene kadar tekrar sorulmasın.
  return { consumed: true, holder: resolveCurrent(dutyTypeId) };
}

/**
 * `completeDuty`'nin tersi: bir kişiye "görevi yapmadı" durumunu geri verir.
 *
 * İki yerde kullanılır:
 *   - Onay sıfırlama (yanlışlıkla "Evet"): kişi görevi yapmamış sayılır.
 *   - Panelden "Sırayı Geç": görev başkasına devredilir.
 *
 * Kişi bu turun "görev yaptı" (served) işaretinden çıkarılır ve turun önü yeniden
 * ona getirilir — böylece bir sonraki dağıtımda yine ilk o sorulur.
 */
function restoreTurn(dutyTypeId, employeeId) {
  if (employeeId == null) return;
  const employee = employeeService.getById(employeeId);
  unmarkServed(dutyTypeId, employeeId); // Silinmiş olsa bile served kaydını temizle.
  if (!employee || employee.is_active !== 1) return; // Pasif/silinmişe önü vermeyiz.
  setCurrent(dutyTypeId, employeeId);
}

module.exports = {
  getState,
  setCurrent,
  findNextActive,
  nextUnservedAfter,
  getServedIds,
  frontUnserved,
  resolveCurrent,
  getTodayRecord,
  getOverview,
  skipToNext,
  completeDuty,
  restoreTurn,
  clearServed,
  unmarkServed,
};
