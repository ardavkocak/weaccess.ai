'use strict';

/**
 * Etkileşimli görev onayı servisi.
 *
 * GÖREVLİ BİR GÜN ÖNCEDEN BELİRLENİR
 * ----------------------------------
 * Akış her gün 17:00'de çalışır ve SONRAKİ İŞ GÜNÜNÜN görevlisini arar. Sabah
 * ayrıca bir bildirim gönderilmez; kişi bir akşam öncesinden haberdar olur.
 *
 *   1. GÖREV KANALINA tek bir soru mesajı: "Pazartesinin görevlisi belirleniyor.
 *      Şu an kontrol edilen kişi: @Beril. Pazartesi ofiste misin?"  [✅ Evet] [❌ Hayır]
 *   2. "Evet" → görev kesinleşir; AYNI mesaj "görevli belli oldu" özetine dönüşür
 *      VE görevlinin özel mesajına "yarın görevlisi sensin" gider.
 *      "Hayır" → AYNI mesaj sıradaki kişinin sorusuna güncellenir; yeni mesaj
 *      açılmaz, kanalda tek mesaj kalır.
 *   3. İlk "Evet" alınana kadar devam eder.
 *
 * Cuma 17:00'de sorulan gün Cumartesi değil PAZARTESİ'dir; hafta sonu ve
 * tatiller `calendar.nextWorkingDay()` ile atlanır.
 *
 * SORU NEDEN KANALDA, SONUÇ NEDEN DM'DE?
 * --------------------------------------
 * Soru kanaldadır çünkü kişi özel mesajlarına bakmıyor olabilir; cevap gelmezse
 * ertesi günün görevlisi hiç belirlenemez ve akış sessizce ölür. Kanalda soru
 * herkese görünür, etiketlenen kişi bildirim alır ve gerekirse ekipten biri de
 * cevaplayabilir.
 *
 * Ayrıntılı "görev sende, erken gel" hatırlatması ise yalnızca kesinleşen kişiyi
 * ilgilendirir; o yüzden DM'e gider. DM ulaşmasa bile (ID yok, DM kapalı) görev
 * kanalda kesinleşmiş kalır — kimse görevsiz kalmaz.
 *
 * SIRA YALNIZCA GÖREVİ YAPANLA İLERLER
 * ------------------------------------
 * "Hayır" cevabı kimseyi sıradan düşürmez — yalnızca o günün görevini ofiste olan
 * bir sonraki kişiye devreder. Sıranın sahibi ancak görevi FİİLEN yaptığında bir
 * sonrakine geçer.
 *
 *   Pazartesi 17:00: Beril? Hayır → Doğa? Hayır → Ahmet? Evet
 *                    Salı'nın görevi Ahmet'te, ama sıra hâlâ Beril'de.
 *   Salı 17:00:      Yine Beril'den sorulur. Beril? Evet → sıra Doğa'ya geçer.
 *
 * Kararın tamamı `rotationService.completeDuty()` içindedir; o günün
 * `duty_history` kaydına `consumed_turn` olarak yazılır.
 *
 * TASARIM İLKELERİ
 * ----------------
 * - TEK MESAJ: Akış boyunca tek bir kanal mesajı düzenlenir (interaction.update).
 *   "Hayır" yeni mesaj oluşturmaz; kanal temiz kalır. TAKAS: düzenlenen mesajdaki
 *   etiket anlık push bildirimi göndermez (Discord davranışı); sıradaki kişi
 *   vurgulanır ama telefonuna bildirim düşmeyebilir. Kanalı temiz tutmanın bedeli.
 * - KALICI: Tüm durum `duty_confirmations` tablosundadır. message_id saklandığı
 *   için sunucu yeniden başlasa bile mevcut mesajın butonları çalışır.
 * - DENETİM: Her cevap `duty_confirmation_events`'e yazılır (kim, kime, ne cevap).
 * - GÜVENLİ EŞ ZAMANLILIK: Karar mantığı (`decideAnswer`) TAMAMEN SENKRON bir
 *   veritabanı işlemidir (await içermez). better-sqlite3 senkron olduğu ve Node
 *   tek iş parçacıklı olduğu için, iki hızlı tıklama sıraya girer: ilki step'i
 *   ilerletir, ikincisi "bayat step" görüp reddedilir. Böylece aynı kişi aynı
 *   butona art arda basıp sistemi bozamaz.
 * - SIRA BOZULMAZ: Kişilerin aktif/pasif durumu değişmez. Yalnızca kesinleşen
 *   kişi geçmişe yazılır; rotasyon yalnızca hak edilmişse ilerler (bkz. yukarısı).
 */

const db = require('../database/connection');
const dbRetry = require('../database/dbRetry');
const employeeService = require('./employee.service');
const dutyTypeService = require('./dutyType.service');
const rotationService = require('./rotation.service');
const historyService = require('./history.service');
const scheduledMessageService = require('./scheduledMessage.service');
const settingsService = require('./settings.service');
const dutyNotifier = require('./dutyNotifier.service');
const calendar = require('./calendar.service');
const bot = require('../discord/bot');
const safeMessage = require('../discord/safeMessage');
const {
  renderQuestion,
  renderConfirmed,
  renderExhausted,
  renderResolved,
  renderOutdated,
} = require('../discord/confirmationMessages');
const { buildConfirmButtons } = require('../discord/components');
const { todayISO, formatLongTR } = require('../utils/date');
const log = require('../utils/logger').create('confirm');

/* ────────────────────────── Veritabanı yardımcıları ────────────────────────── */

function getFlowById(id) {
  return db.prepare('SELECT * FROM duty_confirmations WHERE id = ?').get(id);
}

function getFlow(dutyTypeId, date) {
  return db.prepare(
    'SELECT * FROM duty_confirmations WHERE duty_type_id = ? AND duty_date = ?'
  ).get(dutyTypeId, date);
}

/** Bugünkü akışı döner. */
function getTodayFlow(dutyTypeId) {
  return getFlow(dutyTypeId, todayISO());
}

/**
 * PANELİN İLGİLENDİĞİ akışı döner: bugünden itibaren en ileri tarihli olan.
 *
 * Görevli bir gün önceden belirlendiği için aynı anda iki akış olabilir —
 * bugünün (dün kararlaştırıldı) ve ertesi iş gününün (bugün 17:00'de). Panel
 * her zaman EN SON verilen kararı göstermeli: 17:00'den sonra "yarın", öncesinde
 * "bugün".
 *
 * Yalnızca `getTodayFlow` kullanılsaydı 17:00'de oluşan yarının akışı panelde
 * hiç görünmezdi; "Onayı Sıfırla" butonu da ortaya çıkmazdı (buton, görünür bir
 * akış olmadan gösterilmiyor).
 */
function getActiveFlow(dutyTypeId) {
  return db.prepare(`
    SELECT * FROM duty_confirmations
    WHERE duty_type_id = ? AND duty_date >= ?
    ORDER BY duty_date DESC
    LIMIT 1
  `).get(dutyTypeId, todayISO());
}

/** Bir akışın cevap geçmişini döner. */
function getEvents(confirmationId) {
  return db.prepare(
    'SELECT * FROM duty_confirmation_events WHERE confirmation_id = ? ORDER BY id ASC'
  ).all(confirmationId);
}

function insertEvent({ confirmationId, step, candidateId, candidateName, answer, userId, userName }) {
  db.prepare(`
    INSERT INTO duty_confirmation_events
      (confirmation_id, step, candidate_employee_id, candidate_name, answer, discord_user_id, discord_user_name)
    VALUES (@confirmationId, @step, @candidateId, @candidateName, @answer, @userId, @userName)
  `).run({ confirmationId, step, candidateId, candidateName, answer, userId, userName });
}

function touch(id) {
  db.prepare("UPDATE duty_confirmations SET updated_at = datetime('now') WHERE id = ?").run(id);
}

/**
 * Soru şablonunun değişkenlerini dolduracak bağlamı hazırlar.
 * Aday çalışan silinmiş olabilir; o zaman isim snapshot'ına düşeriz.
 */
function buildTemplateContext(flow, dutyType) {
  const employee = employeeService.getById(flow.candidate_employee_id) ?? {
    full_name: flow.candidate_name,
    discord_user_id: null,
  };

  return {
    employee,
    dutyType,
    company: settingsService.get('company_name', ''),
    date: flow.duty_date,
  };
}

/* ─────────────────────────────── Başlatma ─────────────────────────────── */

/**
 * Bugünkü akışı bulur; yoksa oluşturur. Tamamen senkron (tek işlem).
 *
 * @returns {{ flow: object, created: boolean } | { error: string }}
 */
function ensureFlow(dutyTypeId, source) {
  // Görevli BİR GÜN ÖNCEDEN belirlenir: 17:00'deki akış, bugünün değil SONRAKİ
  // İŞ GÜNÜNÜN görevlisini arar. Cuma 17:00'de "yarın" Cumartesi'dir ama görev
  // Pazartesi'ye aittir; bu yüzden takvim servisinden sonraki iş günü sorulur.
  const date = calendar.nextWorkingDay();

  const run = db.transaction(() => {
    const existing = getFlow(dutyTypeId, date);
    if (existing) return { flow: existing, created: false };

    // Sıradaki aktif kişi (rotasyonu da normalize eder: pasif/silinmişi atlar).
    const candidate = rotationService.resolveCurrent(dutyTypeId);
    if (!candidate) return { error: 'Aktif çalışan bulunamadı. Önce en az bir çalışanı aktif yapın.' };

    const result = db.prepare(`
      INSERT INTO duty_confirmations
        (duty_type_id, duty_date, status, step, source, start_employee_id, candidate_employee_id, candidate_name)
      VALUES (@dutyTypeId, @date, 'pending', 0, @source, @startId, @startId, @name)
    `).run({
      dutyTypeId,
      date,
      source,
      startId: candidate.id,
      name: candidate.full_name,
    });

    return { flow: getFlowById(result.lastInsertRowid), created: true };
  });

  return run();
}

/**
 * Etkileşimli onay akışını başlatır (veya mevcut olanı tazeler).
 *
 * Cron veya admin "Gönder" butonu tarafından çağrılır.
 *
 * @param {object} opts
 * @param {number} opts.dutyTypeId
 * @param {'cron'|'manual'} [opts.source]
 * @param {boolean} [opts.isRetry] Sıfırlama sonrası yeniden sorma; mesaja
 *   "onay sıfırlandı" notu eklenir (bkz. resetAndAskAgain).
 * @returns {Promise<{ ok: boolean, message: string, skipped?: boolean }>}
 */
async function startFlow({ dutyTypeId, source = 'cron', isRetry = false }) {
  const dutyType = dutyTypeService.getById(dutyTypeId);
  if (!dutyType) return { ok: false, message: 'Görev türü bulunamadı.' };

  const result = ensureFlow(dutyTypeId, source);
  if (result.error) return { ok: false, message: result.error };

  const { flow, created } = result;

  const dayLabel = formatLongTR(flow.duty_date);

  if (flow.status === 'confirmed') {
    return { ok: true, skipped: true, message: `${dayLabel} görevi zaten kesinleşti: ${flow.confirmed_name}.` };
  }
  if (flow.status === 'exhausted') {
    return { ok: true, skipped: true, message: `${dayLabel} için uygun kişi bulunamadı olarak işaretlenmiş.` };
  }

  // pending: yeni oluşturulduysa soruyu gönder; zaten varsa mevcut DM'i tazele.
  const content = renderQuestion({
    candidateName: flow.candidate_name,
    isFirst: flow.step === 0,
    isRetry,
    // Soru metni Ayarlar'daki görev bildirimi şablonundan gelir.
    template: scheduledMessageService.getDutyMessageFor(dutyTypeId)?.message_template ?? '',
    context: buildTemplateContext(flow, dutyType),
  });
  const components = buildConfirmButtons(flow.id, flow.step);

  // Saklı mesaj GERÇEKTEN görev kanalında mı? Akış kaydı mesajın yerini
  // channel_id ile hatırlar; tazelerken körü körüne o kimliği düzenlemek
  // tehlikelidir. Kanal ayarlardan değiştirilmiş ya da (bu projede yaşandığı
  // gibi) akış eski bir sürümde kişinin DM'inde başlatılmış olabilir. O zaman
  // "tazeleme" soruyu yanlış yere — örneğin bir DM'e — yazar ve kanalda hiçbir
  // şey görünmez. Kimlik uyuşmuyorsa düzenlemeyi atlayıp safeMessage'ın kanala
  // YENİ mesaj göndermesine izin veririz.
  const dutyChannelId = settingsService.getChannelId('duty');
  const storedIsDutyChannel = flow.channel_id && flow.channel_id === dutyChannelId;
  if (flow.channel_id && !storedIsDutyChannel) {
    log.warn(`Akış ${flow.id}: saklı mesaj görev kanalında değil (${flow.channel_id}); düzenleme atlanacak.`);
  }

  // editOrRecreate: mesaj silinmişse (404) ya da hiç yoksa OTOMATİK yeni mesaj
  // gönderir — "eski message_id kullanılmaya devam edilmesin" kuralı burada
  // tek merkezden garanti edilir (bkz. discord/safeMessage.js).
  const sendResult = await safeMessage.editOrRecreate({
    channelKey: 'duty',
    channelId: storedIsDutyChannel ? flow.channel_id : null,
    messageId: storedIsDutyChannel ? flow.message_id : null,
    content,
    components,
  });

  if (!sendResult.ok) {
    // Yeni akış oluşturduysak ve gönderemediysek boş akışı geri al ki bir
    // sonraki deneme baştan başlayabilsin.
    if (created) db.prepare('DELETE FROM duty_confirmations WHERE id = ?').run(flow.id);
    return { ok: false, message: sendResult.message };
  }

  if (sendResult.recreated || created) {
    db.prepare(
      "UPDATE duty_confirmations SET channel_id = ?, message_id = ?, updated_at = datetime('now') WHERE id = ?"
    ).run(sendResult.channelId, sendResult.messageId, flow.id);
  }

  log.info(
    `Onay akışı güncellendi (akış ${flow.id}, ${dutyType.name}, ${flow.duty_date}): ${flow.candidate_name} soruldu` +
    `${sendResult.recreated ? ' (yeni mesaj)' : ''}.`
  );
  return {
    ok: true,
    message: sendResult.recreated
      ? `${dayLabel} için ${flow.candidate_name} soruldu (eski mesaj bulunamadı, yenisi gönderildi).`
      : `${dayLabel} için ${flow.candidate_name} soruldu.`,
  };
}

/* ─────────────────────────── Buton kararı (senkron) ─────────────────────────── */

/**
 * "Bugün görev kimde?" sorusunun kayıtlardan okunan cevabı.
 *
 * Akış kaydına ulaşılamayan buton tıklamalarında mesajın yerine yazılır.
 * customId yalnızca akış id'si taşıdığı için görev türü bilinmez; tek görev
 * türlü kurulumda doğru cevap varsayılan türdür. Günün görev kaydı da yoksa
 * "bu mesaj geçerli değil" denir.
 */
function describeToday() {
  const dutyType = dutyTypeService.getDefault();
  const record = dutyType ? historyService.getByDate(dutyType.id, todayISO()) : null;
  return record ? renderResolved(record.employee_name) : renderOutdated();
}

/**
 * Bir buton tıklamasını değerlendirir ve veritabanını günceller.
 *
 * ÖNEMLİ: Bu fonksiyon tamamen senkrondur ve `await` İÇERMEZ. Discord I/O'su
 * (mesaj düzenleme) çağıran tarafından, bu fonksiyon döndükten SONRA yapılır.
 * Bu ayrım, iki eşzamanlı tıklamanın araya girmesini imkânsız kılar (bkz. dosya
 * başlığındaki "güvenli eş zamanlılık" notu).
 *
 * @param {object} p
 * @param {number} p.flowId
 * @param {number} p.step
 * @param {'yes'|'no'} p.answer
 * @param {string} [p.userId]   Discord kullanıcı ID'si
 * @param {string} [p.userName] Discord kullanıcı adı
 * @returns {object} outcome — çağırana ne yapacağını söyler:
 *   { type: 'confirmed'|'advanced'|'exhausted', content, components }  → mesajı güncelle
 *   { type: 'resolved', content }                                      → mesajı kapat (butonsuz)
 *   { type: 'stale', message }                                         → geçici (ephemeral) uyarı
 */
function decideAnswer({ flowId, step, answer, userId = null, userName = null }) {
  const run = db.transaction(() => {
    const flow = getFlowById(flowId);

    // Akış kaydı yok. Neredeyse her zaman sebebi şudur: mesaj, BAŞKA bir
    // veritabanıyla çalışan bir örnek tarafından gönderilmiştir (örn. Docker
    // hacmi ile yerel data/ofis.sqlite ayrı dosyalardır) ya da veritabanı
    // sıfırlanmıştır. id'ler AUTOINCREMENT olduğu için bu buton BİR DAHA ASLA
    // eşleşmez; kullanıcıya hata gösterip butonları bırakmak, mesajı sonsuza
    // kadar tıklanabilir bir çıkmaza çevirir. Onun yerine mesajı kapatırız.
    if (!flow) {
      return { type: 'resolved', content: describeToday() };
    }

    // Görev zaten sonuçlanmış: sorulacak bir şey kalmadı, mesajı sadeleştir.
    if (flow.status !== 'pending') {
      if (flow.status === 'exhausted') return { type: 'resolved', content: renderExhausted() };
      return {
        type: 'resolved',
        content: flow.confirmed_name ? renderResolved(flow.confirmed_name) : describeToday(),
      };
    }

    if (step !== flow.step) {
      // Bayat buton (mesaj daha sonraki bir adıma güncellenmiş).
      return { type: 'stale', message: 'Bu soru zaten yanıtlandı. Lütfen güncel mesajdaki butonları kullanın.' };
    }

    // Cevabı denetim kaydına yaz.
    insertEvent({
      confirmationId: flow.id,
      step: flow.step,
      candidateId: flow.candidate_employee_id,
      candidateName: flow.candidate_name,
      answer,
      userId,
      userName,
    });

    if (answer === 'yes') {
      return confirmCandidate(flow);
    }
    return advanceToNext(flow);
  });

  return run();
}

/**
 * "Evet": görevi kesinleştir, geçmişe yaz, sırayı yalnızca hak edilmişse ilerlet.
 * (transaction içinde)
 *
 * Sıra ancak görevi SIRANIN SAHİBİ yaptığında ilerler. Sahibi ofiste olmadığı için
 * görevi aşağıdaki biri üstlendiyse sıra yerinde kalır ve ertesi gün yine sahibinden
 * sorulur. Karar `rotationService.completeDuty()` içindedir.
 */
function confirmCandidate(flow) {
  const confirmed = employeeService.getById(flow.candidate_employee_id) ?? {
    id: flow.candidate_employee_id,
    full_name: flow.candidate_name,
  };

  const { consumed, holder } = rotationService.completeDuty(flow.duty_type_id, confirmed.id);

  // Günün geçmiş kaydı (sırayı yakıp yakmadığı bilgisiyle birlikte).
  historyService.record({
    dutyTypeId: flow.duty_type_id,
    employee: confirmed,
    date: flow.duty_date,
    source: flow.source,
    notified: true,
    consumedTurn: consumed,
  });

  db.prepare(`
    UPDATE duty_confirmations
    SET status = 'confirmed', confirmed_employee_id = ?, confirmed_name = ?, updated_at = datetime('now')
    WHERE id = ?
  `).run(confirmed.id ?? null, confirmed.full_name, flow.id);

  log.info(
    consumed
      ? `Onay kesinleşti (akış ${flow.id}): görevli ${confirmed.full_name} sırasını kullandı, sıra → ${holder?.full_name ?? 'yok'}.`
      : `Onay kesinleşti (akış ${flow.id}): görevi ${confirmed.full_name} vekaleten yaptı, sıra ${holder?.full_name ?? 'yok'} kişisinde kaldı.`
  );

  return {
    type: 'confirmed',
    // Çağıran, kesinleşen kişiye "günaydın" DM'ini gönderebilsin diye kimliği
    // de döneriz. Discord I/O'su bilerek bu transaction'ın DIŞINDA yapılır.
    dutyTypeId: flow.duty_type_id,
    employee: confirmed,
    content: renderConfirmed({
      name: flow.candidate_name,
      // Discord ID'si varsa görevli mesajda etiketlenir.
      employee: confirmed,
      // Sırayı yakmayan görevlide "sıra kimde kaldı" bilgisi mesaja eklenir.
      holderName: consumed ? null : holder?.full_name ?? null,
      // Gün etiketi ("Yarının" / "Pazartesinin") için görev tarihi.
      dutyDate: flow.duty_date,
    }),
    components: [], // butonları kaldır
  };
}

/** "Hayır": bu turda henüz görev yapmamış sıradaki kişiye geç; tur bittiyse
 *  tükendi. Görev yapanlar (served) atlanır — böylece aynı kişi tekrar sorulmaz.
 *  (transaction içinde) */
function advanceToNext(flow) {
  // Bu turda görev yapmış kişileri atla: onlar sıra kendilerine tekrar gelene
  // (tur bitene) kadar tekrar aday olmaz.
  const served = rotationService.getServedIds(flow.duty_type_id);
  const next = rotationService.nextUnservedAfter(flow.candidate_employee_id, served);

  // Kimse kalmadı: ya hiç uygun aday yok ya da başlangıç kişisine geri döndük.
  if (!next || next.id === flow.start_employee_id) {
    db.prepare(
      "UPDATE duty_confirmations SET status = 'exhausted', updated_at = datetime('now') WHERE id = ?"
    ).run(flow.id);
    log.warn(`Onay tükendi (akış ${flow.id}): herkese soruldu, ofiste kimse yok.`);
    return { type: 'exhausted', content: renderExhausted(flow.duty_date), components: [] };
  }

  const newStep = flow.step + 1;

  // channel_id/message_id KORUNUR: akış TEK bir kanal mesajında yürür. "Hayır"
  // denince aynı mesaj sıradaki kişinin sorusuna güncellenir; yeni mesaj
  // açılmaz, kanal temiz kalır (kullanıcının açık isteği).
  //
  // TAKAS: Discord, DÜZENLENEN bir mesajdaki etiketi anlık bildirim (push)
  // olarak göndermez. Sıradaki kişi etiketlenir ve mesajda vurgulanır ama
  // telefonuna bildirim düşmeyebilir. Kanalı tek mesajla temiz tutmanın bedeli
  // budur; kalabalık akış yerine bu tercih edildi.
  db.prepare(`
    UPDATE duty_confirmations
    SET step = ?, previous_name = ?, candidate_employee_id = ?, candidate_name = ?,
        updated_at = datetime('now')
    WHERE id = ?
  `).run(newStep, flow.candidate_name, next.id, next.full_name, flow.id);

  log.info(`Onay ilerledi (akış ${flow.id}): ${flow.candidate_name} → ${next.full_name} (adım ${newStep}).`);

  const dutyType = dutyTypeService.getById(flow.duty_type_id);
  const refreshed = getFlowById(flow.id);

  // Aynı mesaj sıradaki kişinin sorusuyla güncellenir.
  return {
    type: 'advanced',
    content: renderQuestion({
      candidateName: next.full_name,
      isFirst: false,
      template: scheduledMessageService.getDutyMessageFor(flow.duty_type_id)?.message_template ?? '',
      context: buildTemplateContext(refreshed, dutyType ?? { name: '', emoji: '' }),
    }),
    components: buildConfirmButtons(flow.id, newStep),
  };
}

/* ─────────────────────────── Onayı sıfırlama ─────────────────────────── */

/**
 * Bugünkü onay akışını başa sarar ("Yanlışlıkla Evet'e basıldı" kurtarması).
 *
 * Yanlış "Evet" üç yeri birden etkiler; sıfırlama üçünü de geri alır:
 *   1. Geçmiş  — o günün `duty_history` kaydı silinir (görevli yeniden belirsiz).
 *   2. Rotasyon — kayıt sıranın sahibinin hakkını yakmışsa hak iade edilir.
 *   3. Akış     — durum yeniden 'pending', adım 0, aday = sıranın sahibi olur.
 *
 * DENETİM KAYDI SİLİNMEZ: `duty_confirmation_events` satırları olduğu gibi kalır,
 * yalnızca `reset_count` artar. Böylece "kim yanlışlıkla Evet'e basmıştı"
 * sorusunun cevabı kaybolmaz.
 *
 * Discord güncellemesi çağıranın işidir. Transaction, `dbRetry.withRetry` ile
 * sarmalanır: bu fonksiyon panelden (Express route) tetiklendiği için Discord'un
 * 3sn kuralına tabi değildir, ama Office Portal'ın (Django) aynı SQLite
 * dosyasına eşzamanlı yazması burada da SQLITE_BUSY'ye yol açabilir — retry
 * olmadan bu, admin'e ham bir "database is locked" 500 hatası olarak yansırdı.
 *
 * @returns {Promise<{ ok: boolean, message: string, flow?: object, previousName?: string|null }>}
 */
async function resetToday(dutyTypeId) {
  // HANGİ GÜN SIFIRLANIR?
  // Görevli bir gün önceden belirlendiği için aynı anda iki akış olabilir:
  // bugünün (dün kararlaştırıldı) ve ertesi iş gününün (bugün 17:00'de). Yanlış
  // "Evet" düzeltmesi neredeyse her zaman EN SON verilen kararı hedefler; bu
  // yüzden bugünden itibaren en ileri tarihli akış seçilir. Böylece 17:00'den
  // sonra "yarın", öncesinde ise "bugün" sıfırlanır — kullanıcının beklediği gibi.
  const run = db.transaction(() => {
    const flow = getActiveFlow(dutyTypeId);

    if (!flow) {
      return { ok: false, message: 'Sıfırlanacak bir onay akışı yok. Önce "Görev Onayını Başlat" deyin.' };
    }
    if (flow.status === 'pending' && flow.step === 0) {
      return { ok: false, message: 'Onay akışı zaten en baştan bekliyor; sıfırlanacak bir cevap yok.' };
    }

    // 1) AKIŞIN KENDİ GÜNÜNÜN geçmiş kaydını kaldır ve yakılmışsa sırayı iade et.
    //    `date` (bugün) değil `flow.duty_date` kullanılır: sıfırlanan akış ertesi
    //    güne ait olabilir; bugünün kaydını silmek yanlış günü bozardı.
    const record = historyService.getByDate(dutyTypeId, flow.duty_date);
    if (record) {
      if (record.consumed_turn === 1) {
        rotationService.restoreTurn(dutyTypeId, record.employee_id);
      }
      historyService.removeByDate(dutyTypeId, flow.duty_date);
    }

    // 2) Akışı, sıranın (iade sonrası) güncel sahibinden yeniden başlat.
    const candidate = rotationService.resolveCurrent(dutyTypeId);
    if (!candidate) {
      return { ok: false, message: 'Aktif çalışan bulunamadı. Önce en az bir çalışanı aktif yapın.' };
    }

    db.prepare(`
      UPDATE duty_confirmations
      SET status = 'pending', step = 0,
          start_employee_id = @candidateId,
          candidate_employee_id = @candidateId, candidate_name = @candidateName,
          previous_name = NULL,
          confirmed_employee_id = NULL, confirmed_name = NULL,
          reset_count = reset_count + 1,
          updated_at = datetime('now')
      WHERE id = @id
    `).run({ id: flow.id, candidateId: candidate.id, candidateName: candidate.full_name });

    const previousName = flow.confirmed_name ?? null;
    log.warn(`Onay sıfırlandı (akış ${flow.id}): önceki sonuç ${previousName ?? 'yok'}, yeniden ${candidate.full_name} sorulacak.`);

    return {
      ok: true,
      message: `Onay sıfırlandı. Yeniden ${candidate.full_name} soruluyor.`,
      flow: getFlowById(flow.id),
      previousName,
    };
  });

  return dbRetry.withRetry(run, { label: 'resetToday' });
}

/**
 * Onayı sıfırlar ve Discord'daki soruyu yeniden sorar (panel butonu).
 *
 * Sıfırlama senkron yapılır, ardından `startFlow` mevcut mesajı düzenleyerek
 * butonlu soruyu tazeler (mesaj silinmişse yenisini gönderir).
 *
 * @returns {Promise<{ ok: boolean, message: string }>}
 */
async function resetAndAskAgain(dutyTypeId) {
  const reset = await resetToday(dutyTypeId);
  if (!reset.ok) return reset;

  const sent = await startFlow({ dutyTypeId, source: 'manual', isRetry: true });
  if (!sent.ok) {
    // Veritabanı sıfırlandı ama Discord'a yazılamadı: durum panelde görünür,
    // admin "Görev Onayını Başlat" ile tekrar deneyebilir.
    return { ok: false, message: `Onay sıfırlandı ancak Discord mesajı güncellenemedi: ${sent.message}` };
  }

  const previous = reset.previousName ? ` Önceki sonuç (${reset.previousName}) iptal edildi.` : '';
  return { ok: true, message: `${reset.message}${previous}` };
}

/**
 * Bekleyen bir akışı panelden verilen kararla kapatır ("Sırayı Geç").
 *
 * Geçmiş kaydı ve rotasyon güncellemesi çağıran tarafın (rotation.service) işidir;
 * burada yalnızca akış sonuçlandırılır ki Discord'daki butonlar paneldeki kararı
 * ezmesin. Tamamen senkron — çağıranın transaction'ı içinde çalışır.
 *
 * @returns {{ channelId: string, messageId: string, name: string }|null}
 *   Discord mesajının güncellenmesi gerekiyorsa bilgisi; gerekmiyorsa null.
 */
function closeFlowManually(dutyTypeId, employee) {
  // Güncel akış: 17:00'den sonra yarının bekleyen sorusu. `getTodayFlow`
  // kullanılsaydı o soru açık kalır ve Discord'daki butonlar paneldeki kararı
  // ezebilirdi.
  const flow = getActiveFlow(dutyTypeId);
  if (!flow || flow.status !== 'pending') return null;

  db.prepare(`
    UPDATE duty_confirmations
    SET status = 'confirmed', confirmed_employee_id = ?, confirmed_name = ?,
        source = 'manual', updated_at = datetime('now')
    WHERE id = ?
  `).run(employee.id ?? null, employee.full_name, flow.id);

  log.info(`Onay akışı panelden kapatıldı (akış ${flow.id}): görevli ${employee.full_name}.`);

  if (!flow.channel_id || !flow.message_id) return null;
  return { channelId: flow.channel_id, messageId: flow.message_id, name: employee.full_name };
}

/* ─────────────────────────── Buton olay işleyicisi ─────────────────────────── */

/**
 * `interaction.editReply()`'i güvenli biçimde çağırır: başarısız olursa
 * (örn. "Unknown Message" — mesaj interaction ile aynı anda silinmişse)
 * ESKİ message_id'ye bir daha dokunmadan flow'un kanalına YENİ mesaj gönderir
 * ve veritabanını günceller. Kullanıcıya asla ham bir Discord hatası sızmaz.
 *
 * @param {import('discord.js').ButtonInteraction} interaction
 * @param {{content: string, components?: any[]}} payload
 * @param {number|null} flowId Kurtarma gerekirse hangi akışın güncelleneceği.
 */
async function safeEditReply(interaction, payload, flowId = null) {
  try {
    await interaction.editReply(payload);
    return true;
  } catch (error) {
    log.error('interaction.editReply başarısız (mesaj silinmiş olabilir)', error);

    if (flowId == null) return false;
    const flow = getFlowById(flowId);
    if (!flow) return false;

    const sent = await bot.sendInteractive('duty', payload.content, payload.components ?? []);
    if (!sent.ok) {
      log.error(`Kurtarma mesajı da gönderilemedi (akış ${flowId}): ${sent.message}`);
      return false;
    }

    db.prepare(
      "UPDATE duty_confirmations SET channel_id = ?, message_id = ?, updated_at = datetime('now') WHERE id = ?"
    ).run(sent.channelId, sent.messageId, flowId);
    log.warn(`Akış ${flowId}: eski mesaj bulunamadı, yeni mesaj gönderildi ve kayıt güncellendi.`);
    return true;
  }
}

/**
 * `interaction.followUp()`'ı güvenli biçimde çağırır (yalnızca ephemeral
 * bildirimler için — ana mesaj bu yolla değişmez).
 */
async function safeFollowUp(interaction, payload) {
  try {
    await interaction.followUp(payload);
  } catch (error) {
    log.error('interaction.followUp başarısız', error);
  }
}

/**
 * Bir buton tıklamasının İŞ MANTIĞI kısmı.
 *
 * ÖNEMLİ MİMARİ KURAL: Bu fonksiyon yalnızca `discord/interactionRouter.js`
 * tarafından, Discord'a İLK yanıt (`interaction.deferUpdate()`) ZATEN
 * gönderildikten SONRA çağrılır. Bu fonksiyonun kendisi Discord'a hiçbir
 * "ilk yanıt" göndermez — yalnızca `editReply`/`followUp` kullanır (defer
 * sonrası geçerli tek yollar). Böylece:
 *   - SQL süresi (kilit çakışması dahil) Discord'un 3sn'lik yanıt penceresini
 *     ASLA tehdit etmez (editReply/followUp için süre sınırı ~15 dakikadır).
 *   - decideAnswer'ın SQLite transaction'ı `dbRetry.withRetry` ile sarmalanır:
 *     event-loop'u bloke etmeden, sınırlı sayıda ve aralıklı olarak yeniden
 *     denenir (bkz. database/dbRetry.js).
 *
 * @param {import('discord.js').ButtonInteraction} interaction Zaten deferUpdate() yapılmış.
 * @param {{flowId: number, step: number, answer: 'yes'|'no'}} parsed
 * @param {import('../discord/interactionLog').ReturnType<typeof import('../discord/interactionLog').start>} [ilog]
 */
async function handleDeferredButton(interaction, parsed, ilog = null) {
  const userId = interaction.user?.id ?? null;
  const userName = interaction.member?.displayName ?? interaction.user?.username ?? null;

  let outcome;
  try {
    outcome = await dbRetry.withRetry(() => decideAnswer({ ...parsed, userId, userName }), { label: 'decideAnswer' });
    ilog?.step('db-bitti');
  } catch (error) {
    log.error('Buton kararı işlenemedi (decideAnswer, tüm denemeler tükendi)', error);
    await safeEditReply(interaction, {
      content: 'Bir hata oluştu, lütfen birkaç saniye sonra tekrar deneyin.',
      components: [],
    }, parsed.flowId);
    ilog?.step('hata-yaniti-gonderildi');
    return;
  }

  if (outcome.type === 'stale') {
    // Mesaj güncel, buton eski (önbellekten tıklanmış). Ana mesaja dokunulmaz;
    // yalnızca tıklayana ayrı (ephemeral) bir uyarı gider.
    await safeFollowUp(interaction, { content: outcome.message, ephemeral: true });
    ilog?.step('stale-yaniti-gonderildi');
    return;
  }

  if (outcome.type === 'resolved') {
    await safeEditReply(interaction, { content: outcome.content, components: [] }, parsed.flowId);
    ilog?.step('discord-guncellendi');
    return;
  }

  // confirmed | advanced | exhausted → butona basılan TEK mesajı güncelle.
  // "Hayır"da bu mesaj sıradaki kişinin sorusuna dönüşür; yeni mesaj açılmaz.
  await safeEditReply(interaction, { content: outcome.content, components: outcome.components }, parsed.flowId);
  ilog?.step('discord-guncellendi');

  // Görev kesinleştiyse görevliye ÖZEL MESAJ gönder. Ana yanıttan SONRA
  // yapılır ve hata fırlatmaz (bkz. dutyNotifier): kişi DM'lerini kapatmış
  // olsa bile kanaldaki akış sonuçlanmış kalır.
  if (outcome.type === 'confirmed') {
    await dutyNotifier.sendDutyAssigned(outcome.dutyTypeId, outcome.employee);
    ilog?.step('dm-gonderildi');
  }
}

/**
 * Açılışta (ve isteğe bağlı periyodik olarak) çağrılır: `duty_date`'i
 * geçmişte kalmış ama hâlâ `pending` görünen akışları temizler.
 *
 * NEDEN GEREKLİ?
 * ---------------
 * Normal akışta her gün kendi satırını alır (UNIQUE(duty_type_id, duty_date))
 * ve `getActiveFlow` zaten "bugünden itibaren en ileri tarihli" akışı seçtiği
 * için eski pending satırlar panelde/Discord akışında görünmeye devam etmez.
 * Ama süreç bir akış ortasındayken çökerse/yeniden başlarsa, o günün satırı
 * sonsuza dek "pending" kalabilir — bu veri bozukluğu değildir ama panelde
 * "hâlâ bekliyor" gibi yanıltıcı görünebilir. Bu fonksiyon bu satırları
 * `exhausted` olarak işaretler ki geçmiş net kalsın; SIRAYA veya rotasyona
 * DOKUNMAZ (o gün zaten geçmiştir, hiçbir Discord mesajı gönderilmez).
 *
 * @returns {number} Temizlenen satır sayısı.
 */
function cleanupStalePending() {
  const result = db.prepare(`
    UPDATE duty_confirmations
    SET status = 'exhausted', updated_at = datetime('now')
    WHERE status = 'pending' AND duty_date < ?
  `).run(todayISO());

  if (result.changes > 0) {
    log.warn(`Başlangıç temizliği: ${result.changes} eski (geçmiş tarihli) bekleyen onay akışı 'exhausted' işaretlendi.`);
  }
  return result.changes;
}

/* ─────────────────────────────── Panel görünümü ─────────────────────────────── */

/**
 * Panelde göstermek için GÜNCEL onay durumunu özetler.
 *
 * Bugünün değil, en son verilen kararın akışını gösterir (bkz. getActiveFlow):
 * 17:00'den sonra yarının, öncesinde bugünün akışı. Etiketler de o akışın
 * gününe göre yazılır — 24 Temmuz'un görevlisi "bugünkü görevli" diye
 * gösterilmemeli.
 *
 * @returns {{ state: string, label: string, detail: string, events: object[] }|null}
 */
function getTodayStatus(dutyTypeId) {
  const flow = getActiveFlow(dutyTypeId);
  if (!flow) return null;

  const events = getEvents(flow.id);

  // Akış bugüne mi ertesi güne mi ait? Metinler buna göre değişir.
  const isToday = flow.duty_date === todayISO();
  const dayWord = isToday ? 'Bugünkü' : 'Yarınki';
  const dayLabel = isToday ? 'bugün' : formatLongTR(flow.duty_date);

  const labels = {
    pending: {
      state: 'pending',
      label: 'Onay bekleniyor',
      detail: `${dayLabel} görevi için ${flow.candidate_name} soruluyor.`,
    },
    confirmed: {
      state: 'confirmed',
      label: 'Kesinleşti',
      detail: `${dayWord} görevli: ${flow.confirmed_name}.`,
    },
    exhausted: {
      state: 'exhausted',
      label: 'Kimse bulunamadı',
      detail: `${dayLabel} için uygun kişi bulunamadı.`,
    },
  };

  const status = { ...(labels[flow.status] ?? labels.pending), flow, events };

  // Sıfırlanmış akışta denetim kayıtları önceki turlardan da cevap içerir;
  // panel bunu açıkça belirtsin ki eski cevaplar kafa karıştırmasın.
  if (flow.reset_count > 0) {
    status.resetCount = flow.reset_count;
    status.detail += ` (${flow.reset_count} kez sıfırlandı; aşağıdaki cevapların bir kısmı önceki turlardan.)`;
  }

  return status;
}

module.exports = {
  startFlow,
  handleDeferredButton, // interactionRouter tarafından, deferUpdate() SONRASI çağrılır
  decideAnswer, // test edilebilirlik için
  cleanupStalePending,
  resetToday,
  resetAndAskAgain,
  closeFlowManually,
  getTodayFlow,
  getActiveFlow,
  getTodayStatus,
  getEvents,
  getFlowById,
};
