'use strict';

/**
 * Kalıcı interaction debug günlüğü.
 *
 * NEDEN AYRI BİR MODÜL?
 * ----------------------
 * "Uygulama zamanında yanıt vermedi" gibi hatalar geriye dönük araştırılması
 * en zor hatalardır: Discord tarafında hiçbir iz bırakmazlar, sunucu tarafında
 * da tek bir log satırı yeterli bağlamı vermez (hangi kullanıcı, hangi mesaj,
 * hangi adımda, kaç ms sürdü?). Bu modül HER interaction için T0-T6 arası
 * adlandırılmış zaman damgaları tutar ve interaction tamamlandığında hem bir
 * özet satırı hem de açık bir T0..T6 zaman çizelgesi yazar.
 *
 * T0..T6 SÖZLEŞMESİ (bkz. discord/interactionRouter.js ve servis katmanı):
 *   T0 - interactionCreate alındı (bu nesnenin oluşturulduğu an, referans 0ms)
 *   T1 - interaction.deferUpdate() CAGRILDI (henüz dönmedi)
 *   T2 - interaction.deferUpdate() BASARIYLA DÖNDÜ
 *   T3 - ilk SQL (decideAnswer/castVote) BASLADI
 *   T4 - o SQL BİTTİ
 *   T5 - Discord mesajı (editReply/followUp) güncellendi
 *   T6 - interaction işlemi tamamen bitti
 *
 * KULLANIM
 *   const ilog = interactionLog.start(interaction, { module: 'duty' });
 *   ilog.mark('T1', 'deferUpdate çağrıldı');
 *   await interaction.deferUpdate();
 *   ilog.mark('T2', 'deferUpdate başarılı döndü');
 *   ...
 *   ilog.finish({ ok: true });
 */

const log = require('../utils/logger').create('interaction');

function hhmmssms(date = new Date()) {
  const pad = (n, len = 2) => String(n).padStart(len, '0');
  return `${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}.${pad(date.getMilliseconds(), 3)}`;
}

const T_DESCRIPTIONS = {
  T0: 'interactionCreate alındı',
  T1: 'deferUpdate/deferReply CAGRILDI',
  T2: 'deferUpdate/deferReply BASARIYLA DÖNDÜ',
  T3: 'ilk SQL başladı',
  T4: 'SQL bitti',
  T5: 'Discord mesajı güncellendi (editReply/followUp)',
  T6: 'işlem tamamlandı',
};

function start(interaction, { module: moduleName = '?' } = {}) {
  const startedAt = process.hrtime.bigint();
  const wallClock = hhmmssms();
  const steps = [];
  const marks = [];

  const context = {
    module: moduleName,
    interactionId: interaction?.id ?? '?',
    customId: interaction?.customId ?? '?',
    userId: interaction?.user?.id ?? '?',
    userName: interaction?.member?.displayName ?? interaction?.user?.username ?? '?',
    messageId: interaction?.message?.id ?? '?',
  };

  function elapsedMs() {
    return Number(process.hrtime.bigint() - startedAt) / 1000000;
  }

  function step(name) {
    steps.push({ name, atMs: Math.round(elapsedMs()) });
  }

  function mark(tLabel, description) {
    marks.push({ tLabel, description: description || T_DESCRIPTIONS[tLabel] || '', atMs: elapsedMs() });
  }

  mark('T0');

  function printTimeline() {
    const header = `[${wallClock}] ${context.module} ${context.customId} user=${context.userName}(${context.userId}) interaction=${context.interactionId}`;
    log.info(`ZAMAN CIZELGESI ${header}`);
    for (const m of marks) {
      log.info(`   ${m.tLabel}  ${m.atMs.toFixed(1)}ms  ${m.description}`);
    }
  }

  function finish({ ok, error = null } = {}) {
    const totalMs = elapsedMs();
    mark('T6');
    printTimeline();

    const timeline = steps.map((s) => `${s.name}(+${s.atMs}ms)`).join(' -> ');
    const header = `[${wallClock}] ${context.module} ${context.customId} user=${context.userName}(${context.userId}) msg=${context.messageId}`;

    if (ok) {
      log.info(`${header} OK ${timeline || '(adim yok)'} - toplam ${totalMs.toFixed(1)}ms`);
    } else {
      const lastStep = steps.length ? steps[steps.length - 1].name : '(defer oncesi)';
      log.error(
        `${header} HATA son adim="${lastStep}" ${timeline || '(adim yok)'} - toplam ${totalMs.toFixed(1)}ms - hata: ${error?.message ?? error}`,
        error instanceof Error ? error : undefined,
      );
    }

    const hasT1 = marks.some((m) => m.tLabel === 'T1');
    const hasT2 = marks.some((m) => m.tLabel === 'T2');
    if (!hasT1) {
      log.error(`${header} UYARI: T1 (deferUpdate cagrisi) HIC OLUSMADI - hata defer mekanizmasinin kendisinde.`);
    } else if (!hasT2) {
      log.error(`${header} UYARI: T1 olustu ama T2 (defer'in basarili donusu) olusmadi - defer Discord API'sine ulasmamis veya reddedilmis olabilir.`);
    }

    if (totalMs > 2500) {
      log.warn(`${header} UYARI: yanit suresi ${totalMs.toFixed(1)}ms - Discord'un 3sn sinirina yakin/uzerinde.`);
    }
  }

  return { step, mark, finish, context, elapsedMs };
}

module.exports = { start };
