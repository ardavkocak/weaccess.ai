'use strict';

/**
 * Kalıcı interaction debug günlüğü.
 *
 * NEDEN AYRI BİR MODÜL?
 * ----------------------
 * "Uygulama zamanında yanıt vermedi" gibi hatalar geriye dönük araştırılması
 * en zor hatalardır: Discord tarafında hiçbir iz bırakmazlar, sunucu tarafında
 * da tek bir log satırı yeterli bağlamı vermez (hangi kullanıcı, hangi mesaj,
 * hangi adımda, kaç ms sürdü?). Bu modül HER interaction için adım adım bir
 * zaman çizelgesi tutar ve interaction tamamlandığında (başarılı ya da
 * başarısız) TEK bir özet satırı yazar.
 *
 * KULLANIM
 *   const log = interactionLog.start(interaction, { module: 'duty' });
 *   log.step('deferUpdate');
 *   log.step('db-baslad');
 *   log.step('db-bitti');
 *   log.step('discord-guncellendi');
 *   log.finish({ ok: true });
 *
 * Örnek çıktı:
 *   [13:41:10.112] dc:12:0:y user=Beril(123) msg=456
 *     → deferUpdate            +8ms
 *     → db-baslad              +9ms
 *     → db-bitti               +11ms
 *     → discord-guncellendi    +187ms
 *   ✓ Tamamlandı, toplam 187ms
 *
 * Hata durumunda `finish({ ok: false, error })` çağrılır; hangi adımda
 * kaldığı (son `step()`) ve hatanın kendisi tek satırda görünür.
 */

const log = require('../utils/logger').create('interaction');

function hhmmssms(date = new Date()) {
  const pad = (n, len = 2) => String(n).padStart(len, '0');
  return `${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}.${pad(date.getMilliseconds(), 3)}`;
}

function start(interaction, { module: moduleName = '?' } = {}) {
  const startedAt = process.hrtime.bigint();
  const wallClock = hhmmssms();
  const steps = [];

  const context = {
    module: moduleName,
    interactionId: interaction?.id ?? '?',
    customId: interaction?.customId ?? '?',
    userId: interaction?.user?.id ?? '?',
    userName: interaction?.member?.displayName ?? interaction?.user?.username ?? '?',
    messageId: interaction?.message?.id ?? '?',
  };

  function elapsedMs() {
    return Number(process.hrtime.bigint() - startedAt) / 1_000_000;
  }

  function step(name) {
    steps.push({ name, atMs: Math.round(elapsedMs()) });
  }

  function finish({ ok, error = null } = {}) {
    const totalMs = Math.round(elapsedMs());
    const timeline = steps.map((s) => `${s.name}(+${s.atMs}ms)`).join(' → ');
    const header = `[${wallClock}] ${context.module} ${context.customId} user=${context.userName}(${context.userId}) msg=${context.messageId}`;

    if (ok) {
      log.info(`${header} ✓ ${timeline || '(adım yok)'} — toplam ${totalMs}ms`);
    } else {
      const lastStep = steps.length ? steps[steps.length - 1].name : '(defer öncesi)';
      log.error(
        `${header} ✗ son adım="${lastStep}" ${timeline || '(adım yok)'} — toplam ${totalMs}ms — hata: ${error?.message ?? error}`,
        error instanceof Error ? error : undefined,
      );
    }

    // Discord'un 3sn yanıt penceresine ne kadar yaklaşıldığı ayrıca uyarılır;
    // sistem "çalışıyor" görünse bile bu, ilerleyen bir performans sorununun
    // erken belirtisidir.
    if (totalMs > 2500) {
      log.warn(`${header} ⚠ yanıt süresi ${totalMs}ms — Discord'un 3sn sınırına yakın/üzerinde.`);
    }
  }

  return { step, finish, context, elapsedMs };
}

module.exports = { start };
