'use strict';

/**
 * Interaction bazlı tekillik (idempotency) koruması.
 *
 * NEDEN GEREKLİ?
 * --------------
 * Discord Gateway, ağ kesintisi/yeniden bağlanma gibi durumlarda AYNI
 * interaction olayını teorik olarak birden fazla kez teslim edebilir. Bizim
 * kodumuzda da (örn. gelecekte bir refactor hatasıyla) aynı interaction'ın iki
 * yerden işlenmesi ihtimali olabilir. Discord'un kendisi zaten "aynı
 * interaction'a iki kez yanıt" durumunda hata döner (InteractionAlreadyReplied),
 * ama o noktaya gelmeden ÖNCE — yani iş mantığını (DB yazması) iki kez
 * ÇALIŞTIRMADAN — engellemek gerekir; aksi halde "aynı oya iki kez cevap
 * verme" değil ama "aynı tıklamayı iki kez SAYMA" riski oluşur.
 *
 * TASARIM
 * -------
 * Basit bir bellek-içi Set + TTL temizliği. Kalıcı depolamaya (DB) gerek yok:
 * bir interaction token'ı zaten yalnızca birkaç dakika geçerlidir, süreç
 * yeniden başladığında zaten tüm eski interaction'lar geçersizleşmiştir.
 */

const SEEN = new Map(); // interactionId -> eklenme zamanı (ms)
const TTL_MS = 5 * 60 * 1000; // Discord token ömrü (~15dk) ile kıyasla cömert ama sınırlı.
const MAX_ENTRIES = 5000; // Bellek şişmesine karşı sert sınır.

function cleanup() {
  const now = Date.now();
  for (const [id, addedAt] of SEEN) {
    if (now - addedAt > TTL_MS) SEEN.delete(id);
  }
  // Olağandışı büyürse (temizlik yetişmiyorsa) en eskilerden atarak sınırla.
  if (SEEN.size > MAX_ENTRIES) {
    const excess = SEEN.size - MAX_ENTRIES;
    let i = 0;
    for (const id of SEEN.keys()) {
      if (i >= excess) break;
      SEEN.delete(id);
      i += 1;
    }
  }
}

/**
 * Bu interaction daha önce işlenmiş mi? İşlenmemişse ATOMIK olarak
 * "işleniyor" işaretler ve false döner; işlenmişse true döner (çağıran
 * atlamalı).
 *
 * @param {string} interactionId
 * @returns {boolean} true ise bu interaction ZATEN görülmüş, işleme ALINMAMALI.
 */
function alreadySeen(interactionId) {
  if (!interactionId) return false; // Kimliksiz gelirse (olmamalı) engellemeyelim.

  cleanup();

  if (SEEN.has(interactionId)) return true;

  SEEN.set(interactionId, Date.now());
  return false;
}

module.exports = { alreadySeen };
