'use strict';

/**
 * Discord bot istemcisi.
 *
 * TASARIM NOTLARI
 * ---------------
 * - Token veritabanındaki ayarlardan okunur, .env'e gömülü değildir. Panelden
 *   token değiştirildiğinde `reconnect()` çağrılır ve istemci yeniden kurulur.
 * - Token tanımlı değilse uygulama ÇÖKMEZ; bot "yapılandırılmamış" durumda kalır
 *   ve panel bunu bildirir. Böylece Discord kurulmadan da sistem kullanılabilir.
 * - Bağlantı tembel (lazy) kurulur: ilk mesaj gönderiminde veya açılışta token
 *   varsa devreye girer.
 *
 * Yalnızca `Guilds` intent'i kullanılır; bot mesaj okumaz, sadece yazar. Bu
 * nedenle Discord Developer Portal'da ayrıcalıklı (privileged) intent açmak
 * GEREKMEZ.
 *
 * GÖNDERİM YOLLARI
 * ----------------
 *   sendInteractive(channelKey, …)  → KANAL. Hedef kanal her çağrıda açıkça
 *                                     verilir: 'duty' (görev onayı) veya
 *                                     'meal' (yemek duyurusu). Varsayılan
 *                                     bilerek yoktur — bir sistemin mesajı
 *                                     diğerinin kanalına düşemesin.
 *   editInteractive(channelId, …)   → Var olan mesajı kendi kanalında günceller.
 *   sendDirectMessage(userId, …)    → KİŞİ (DM), düz metin. Hatırlatmalar.
 *   sendInteractiveDirect(userId, …)→ KİŞİ (DM), BUTONLU. 17:00 "yarın ofiste
 *                                     misin?" onay sorusu buradan gider.
 *
 * Kanala düz metin yazan genel bir yardımcı bilerek YOKTUR: hatırlatmaların
 * yanlışlıkla kanala düşmesi bu şekilde yapısal olarak engellenir.
 *
 * Kanal ID'leri `settings.service.CHANNEL_KEYS` üzerinden okunur; yeni bir kanal
 * eklemek için orada bir satır yeterlidir, bu dosya değişmez.
 */

const { Client, GatewayIntentBits } = require('discord.js');
const settingsService = require('../services/settings.service');
const interactionRouter = require('./interactionRouter');
const log = require('../utils/logger').create('discord');

/** @type {import('discord.js').Client|null} */
let client = null;
/** Bağlantı kurulumunun tekrar tekrar başlatılmasını engelleyen kilit. */
let loginPromise = null;
/** İstemcinin hangi token ile kurulduğunu hatırlar (token değişimini yakalamak için). */
let activeToken = null;
/** Son hata mesajı; panelde durum göstergesinde kullanılır. */
let lastError = null;

/**
 * Zaten Türkçe/anlaşılır olan hatalar; tekrar sarmalanmamaları için işaretlenir.
 * @param {string} message
 */
function friendlyError(message) {
  const error = new Error(message);
  error.isFriendly = true;
  return error;
}

/**
 * Discord API hatalarını kullanıcıya gösterilebilir Türkçe mesaja çevirir.
 * @param {Error} error
 */
function toFriendlyError(error) {
  // Kendi ürettiğimiz mesajlar zaten anlaşılır; olduğu gibi geçir.
  if (error?.isFriendly) return error.message;

  const message = String(error?.message ?? error);

  if (/TOKEN_INVALID|An invalid token/i.test(message)) {
    return 'Discord bot token geçersiz. Ayarlar sayfasından doğru token\'ı girin.';
  }
  if (/disallowed intents/i.test(message)) {
    return 'Bot için gerekli intent izinleri reddedildi. Discord Developer Portal ayarlarını kontrol edin.';
  }
  if (/Unknown Channel/i.test(message)) {
    return 'Kanal bulunamadı. Kanal ID\'sini kontrol edin ve botun sunucuya ekli olduğundan emin olun.';
  }
  if (/Unknown Guild/i.test(message)) {
    return 'Sunucu bulunamadı. Guild ID\'sini kontrol edin ve botun bu sunucuya ekli olduğundan emin olun.';
  }
  if (/Missing Access|Missing Permissions/i.test(message)) {
    return 'Botun bu kanala mesaj gönderme yetkisi yok. Kanal izinlerini kontrol edin.';
  }
  if (/Cannot send messages to this user/i.test(message)) {
    return 'Kullanıcıya özel mesaj gönderilemiyor. Kişi sunucu üyelerinden DM almayı kapatmış ' +
           'veya botu engellemiş olabilir.';
  }
  if (/Unknown User/i.test(message)) {
    return 'Discord kullanıcısı bulunamadı. Çalışan kaydındaki Discord ID\'yi kontrol edin.';
  }
  if (/getaddrinfo|ENOTFOUND|ETIMEDOUT|ECONNREFUSED|fetch failed/i.test(message)) {
    return 'Discord sunucularına ulaşılamıyor. İnternet bağlantısını kontrol edin.';
  }
  return `Discord hatası: ${message}`;
}

/** Bot yapılandırılmış mı? (token girilmiş mi) */
function isConfigured() {
  return Boolean(settingsService.get('discord_bot_token'));
}

/**
 * İstemciyi kurar ve giriş yapar. Zaten bağlıysa mevcut istemciyi döner.
 * @returns {Promise<import('discord.js').Client>}
 * @throws {Error} Token yoksa veya giriş başarısızsa.
 */
async function connect() {
  const token = settingsService.get('discord_bot_token');
  if (!token) {
    throw friendlyError('Discord bot token tanımlı değil. Ayarlar sayfasından ekleyin.');
  }

  // Token değiştiyse eski istemciyi kapat.
  if (client && activeToken !== token) {
    await disconnect();
  }

  // Hazır ve bağlı istemci varsa yeniden kullan.
  if (client?.isReady()) return client;

  // Süren bir giriş varsa ona katıl (eşzamanlı çağrılarda çift giriş olmasın).
  if (loginPromise) return loginPromise;

  loginPromise = (async () => {
    const newClient = new Client({ intents: [GatewayIntentBits.Guilds] });

    // Bağlantı koptuğunda süreç çökmesin; hata kaydedilsin.
    newClient.on('error', (error) => {
      lastError = toFriendlyError(error);
      log.error('İstemci hatası', lastError);
    });

    // GATEWAY KOPMALARI GÖRÜNÜR OLMALI.
    //
    // Önceden bu olaylar hiç dinlenmiyordu: WebSocket sessizce koparsa (ağ
    // sorunu, Discord tarafı oturum geçersizleştirmesi, AYNI TOKEN ile
    // eşzamanlı başka bir giriş — örn. bir teşhis/test script'inin
    // `bot.connect()` çağırması yeni bir IDENTIFY açar ve Discord bazen eski
    // oturumu kapatır) süreç canlı kalmaya, `client.isReady()` bile true
    // dönmeye devam edebilir ama gateway ölüdür: butonlar Discord'da görünür
    // ama HİÇBİR interactionCreate olayı ulaşmaz, kullanıcı sessizce
    // "Uygulama zamanında yanıt vermedi" görür ve loglarda hiçbir iz kalmaz.
    // Bu blok önce durumu LOGLAR (geriye dönük teşhis için), watchdog
    // (aşağıda) ise fiilen YENİDEN BAĞLANIR.
    newClient.on('shardDisconnect', (event, shardId) => {
      lastError = 'Discord bağlantısı koptu, yeniden bağlanılacak.';
      log.error(`Shard ${shardId} koptu (code=${event?.code}, reason=${event?.reason || '-'}).`);
    });
    newClient.on('shardError', (error, shardId) => {
      log.error(`Shard ${shardId} hata verdi`, error);
    });
    newClient.on('shardReconnecting', (shardId) => {
      log.warn(`Shard ${shardId} yeniden bağlanmayı deniyor...`);
    });
    newClient.on('shardResume', (shardId, replayedEvents) => {
      lastError = null;
      log.info(`Shard ${shardId} bağlantıyı geri kazandı (${replayedEvents} olay tekrar oynatıldı).`);
    });

    // Buton etkileşimleri. Yalnızca `Guilds` intent'i yeterli; etkileşimler
    // intent'e bağlı değildir. Tüm işleme mantığı (defer-first, yönlendirme,
    // hata güvenlik ağı, debug günlüğü) `interactionRouter.js`'de merkezîdir —
    // bkz. o dosyanın başındaki mimari not. Sunucu yeniden başlasa bile mevcut
    // mesajlardaki butonlar bu dinleyici sayesinde çalışmaya devam eder.
    newClient.on('interactionCreate', (interaction) => {
      interactionRouter.handleInteraction(interaction).catch((error) => {
        // interactionRouter kendi içinde tüm hataları yakalar; bu satır yalnızca
        // gerçekten imkansız bir durumda (örn. router'ın kendisinde bir hata)
        // sürecin sessizce çökmesini engelleyen son bir emniyet kemeridir.
        log.error('interactionRouter beklenmedik şekilde reddetti', error);
      });
    });

    try {
      await newClient.login(token);
      // login() çözülse bile "ready" olayını beklemek gerekir; aksi halde
      // channels.fetch() erken çağrılabilir.
      if (!newClient.isReady()) {
        await new Promise((resolve, reject) => {
          const timer = setTimeout(
            () => reject(new Error('Discord bağlantısı zaman aşımına uğradı (15sn).')),
            15_000
          );
          newClient.once('clientReady', () => { clearTimeout(timer); resolve(); });
          // discord.js v14 'ready', v15 'clientReady' kullanır; ikisini de dinle.
          newClient.once('ready', () => { clearTimeout(timer); resolve(); });
        });
      }

      client = newClient;
      activeToken = token;
      lastError = null;
      log.info(`Bot bağlandı: ${newClient.user.tag}`);

      // Bağlanır bağlanmaz botun hangi sunucularda olduğunu raporla. Yanlış
      // Guild ID gibi yapılandırma hataları böylece 08:05'i beklemeden görünür.
      logDiagnostics(newClient, 'açılış');

      return client;
    } catch (error) {
      // Başarısız istemciyi arkada bırakma; soket sızıntısı olmasın.
      newClient.destroy().catch(() => {});
      lastError = toFriendlyError(error);
      // lastError zaten çevrilmiş metin; çağıran tekrar sarmalamasın.
      throw friendlyError(lastError);
    } finally {
      loginPromise = null;
    }
  })();

  return loginPromise;
}

/** Bağlantıyı kapatır. */
async function disconnect() {
  if (client) {
    await client.destroy().catch(() => {});
    client = null;
    activeToken = null;
  }
}

/** Ayarlar değiştiğinde çağrılır: token değiştiyse yeniden bağlanır. */
async function reconnect() {
  await disconnect();
  if (!isConfigured()) {
    lastError = null;
    return { ok: false, message: 'Token tanımlı değil.' };
  }
  try {
    await connect();
    return { ok: true, message: 'Discord bağlantısı yenilendi.' };
  } catch (error) {
    return { ok: false, message: error.message };
  }
}

/**
 * Bağlantı teşhis bilgisi toplar.
 *
 * "Unknown Guild" hatasının nedeni neredeyse her zaman yapılandırmadır: ya
 * girilen ID yanlış türdedir (kanal/kullanıcı ID'si guild alanına yazılmıştır)
 * ya da bot o sunucuya davet edilmemiştir. `guilds.fetch(id)` yalnızca botun
 * ÜYE OLDUĞU sunucuları getirebilir; üye değilse Discord "Unknown Guild" (10004)
 * döner. Yani hata, kodun değil yapılandırmanın sorunudur.
 *
 * Bu fonksiyon, hangisi olduğunu söyleyebilmek için botun GERÇEKTE hangi
 * sunucularda olduğunu raporlar.
 *
 * `Guilds` intent'i sayesinde istemci "ready" olduğunda üye olduğu tüm sunucular
 * `guilds.cache` içine dolar; bu yüzden cache bu soru için güvenilir kaynaktır.
 *
 * @param {import('discord.js').Client} activeClient
 * @returns {object} Loglanabilir/gösterilebilir teşhis nesnesi.
 */
function getDiagnostics(activeClient) {
  const guildId = settingsService.get('discord_guild_id');

  // Tanımlı her kanal ayrı ayrı raporlanır (görev + yemek).
  const channels = Object.entries(settingsService.CHANNEL_KEYS).map(([key, meta]) => ({
    key,
    label: meta.label,
    id: settingsService.get(meta.settingKey) || '',
  }));

  const cachedGuilds = activeClient?.guilds?.cache
    ? [...activeClient.guilds.cache.values()].map((g) => ({ id: g.id, name: g.name }))
    : [];

  return {
    botTag: activeClient?.user?.tag ?? '(bağlı değil)',
    botId: activeClient?.user?.id ?? null,
    isReady: Boolean(activeClient?.isReady?.()),
    settingsGuildId: guildId || '',
    channels,
    guildCacheSize: activeClient?.guilds?.cache?.size ?? 0,
    guilds: cachedGuilds,
    // Girilen ID, botun bulunduğu sunucularla eşleşiyor mu?
    guildIdMatches: Boolean(guildId) && cachedGuilds.some((g) => g.id === guildId),
    // Sık yapılan hata: guild alanına kanal ID'si yazılmış.
    idsAreIdentical: Boolean(guildId) && channels.some((c) => c.id === guildId),
  };
}

/** Teşhis bilgisini loglara döker ve nesneyi döner. */
function logDiagnostics(activeClient, context = '') {
  const info = getDiagnostics(activeClient);

  log.info(`── Discord teşhis${context ? ` (${context})` : ''} ──`);
  log.info(`   Bot                  : ${info.botTag}${info.botId ? `  (id: ${info.botId})` : ''}`);
  log.info(`   Hazır (ready)        : ${info.isReady}`);
  log.info(`   Ayarlardaki Guild ID : ${info.settingsGuildId || '(boş)'}`);
  for (const channel of info.channels) {
    log.info(`   ${channel.label.padEnd(21)}: ${channel.id || '(boş)'}`);
  }
  log.info(`   guilds.cache.size    : ${info.guildCacheSize}`);

  if (info.guilds.length === 0) {
    log.warn('   Bot HİÇBİR sunucuda değil — OAuth2 bağlantısıyla sunucuya eklenmeli.');
  } else {
    log.info('   Botun bulunduğu sunucular:');
    for (const guild of info.guilds) {
      const mark = guild.id === info.settingsGuildId ? '  ←  ayarlardaki ID ile EŞLEŞİYOR' : '';
      log.info(`     • ${guild.name}  (id: ${guild.id})${mark}`);
    }
  }

  if (info.settingsGuildId && !info.guildIdMatches) {
    log.error(`   ⚠ Ayarlardaki Guild ID (${info.settingsGuildId}) botun bulunduğu sunucular arasında YOK.`);
  }
  if (info.idsAreIdentical) {
    log.error('   ⚠ Guild ID ile bir kanal ID\'si aynı girilmiş; bunlar farklı ID\'lerdir.');
  }
  log.info('── teşhis sonu ──');

  return info;
}

/**
 * "Sunucu bulunamadı" durumunda kullanıcıya NE YAPACAĞINI söyleyen mesaj üretir.
 * Genel bir "ID'yi kontrol edin" yerine botun gerçekte bulunduğu sunucuları listeler.
 */
function buildGuildNotFoundMessage(info) {
  if (info.idsAreIdentical) {
    return 'Guild ID ile Kanal ID aynı girilmiş; bunlar farklı ID\'lerdir. ' +
           'Sunucu simgesine sağ tıklayıp "Sunucu ID\'sini Kopyala", kanala sağ tıklayıp "Kanal ID\'sini Kopyala" deyin.';
  }

  if (info.guilds.length === 0) {
    return `Bot (${info.botTag}) hiçbir Discord sunucusunda değil. ` +
           'Developer Portal → OAuth2 → URL Generator ile "bot" kapsamını seçin ve üretilen bağlantıdan botu sunucunuza ekleyin.';
  }

  const list = info.guilds.map((g) => `"${g.name}" (${g.id})`).join(', ');

  if (info.guilds.length === 1) {
    return `Girdiğiniz Guild ID (${info.settingsGuildId}) bu bota ait bir sunucu değil. ` +
           `Bot şu anda yalnızca ${list} sunucusunda. Doğru ID'yi girin veya alanı boş bırakın.`;
  }

  return `Girdiğiniz Guild ID (${info.settingsGuildId}) botun bulunduğu sunucular arasında yok. ` +
         `Bot şu sunucularda: ${list}.`;
}

/**
 * Sunucuyu (guild) çözer: ÖNCE önbellek, sonra API.
 *
 * Önbellek `Guilds` intent'i ile ready anında dolar ve botun üye olduğu tüm
 * sunucuları içerir; önce oraya bakmak hem daha hızlıdır hem gereksiz API
 * çağrısı yapmaz. Önbellekte yoksa (nadir durum: bot ready sonrası sunucuya
 * eklenmiş olabilir) API'den istenir.
 *
 * @throws {Error} Bulunamazsa yol gösteren Türkçe mesajla.
 */
async function resolveGuild(activeClient, guildId) {
  const cached = activeClient.guilds.cache.get(guildId);
  if (cached) {
    log.debug(`Sunucu önbellekten alındı: ${cached.name} (${cached.id})`);
    return cached;
  }

  log.warn(`Sunucu önbellekte yok (${guildId}), API'den isteniyor...`);
  const fetched = await activeClient.guilds.fetch(guildId).catch((error) => {
    log.warn(`guilds.fetch(${guildId}) başarısız: ${error.message}`);
    return null;
  });

  if (fetched) {
    log.info(`Sunucu API'den alındı: ${fetched.name} (${fetched.id})`);
    return fetched;
  }

  // Bulunamadı: teşhisi logla ve yol gösteren hatayı fırlat.
  const info = logDiagnostics(activeClient, 'sunucu bulunamadı');
  throw friendlyError(buildGuildNotFoundMessage(info));
}

/**
 * Ayarlarda tanımlı kanalı çözer.
 *
 * İKİ KANAL, TEK ÇÖZÜMLEYİCİ
 * --------------------------
 * Görev ve yemek sistemleri aynı botu ama farklı kanalları kullanır. Kanal
 * anahtarı ('duty' | 'meal') ayarlardaki ID'ye `settings.service.CHANNEL_KEYS`
 * üzerinden çevrilir; çözümleme mantığı tek yerde durur, kanal eklemek yeni kod
 * gerektirmez.
 *
 * Guild ID tanımlıysa kanal sunucu üzerinden aranır. Bu, "kanal başka bir
 * sunucuda" gibi yapılandırma hatalarını erkenden ve anlaşılır biçimde yakalar.
 * Guild ID tanımlı değilse doğrudan kanal ID'siyle çözülür (alan isteğe bağlı).
 *
 * @param {import('discord.js').Client} activeClient
 * @param {'duty'|'meal'} channelKey
 * @returns {Promise<object>} Metin kanalı
 * @throws {Error} Kullanıcıya gösterilebilir Türkçe mesajla.
 */
async function resolveChannel(activeClient, channelKey) {
  const meta = settingsService.CHANNEL_KEYS[channelKey];
  if (!meta) throw friendlyError(`Bilinmeyen kanal anahtarı: ${channelKey}`);

  const channelId = settingsService.get(meta.settingKey);
  const guildId = settingsService.get('discord_guild_id');

  log.debug(`resolveChannel(${channelKey}): guildId=${guildId || '(boş)'} channelId=${channelId || '(boş)'}`);

  if (!channelId) {
    throw friendlyError(`${meta.label} ID tanımlı değil. Ayarlar sayfasından ekleyin.`);
  }

  let channel;

  if (guildId) {
    const guild = await resolveGuild(activeClient, guildId);

    channel = guild.channels.cache.get(channelId)
           ?? await guild.channels.fetch(channelId).catch((error) => {
                log.warn(`guild.channels.fetch(${channelId}) başarısız: ${error.message}`);
                return null;
              });

    if (!channel) {
      logDiagnostics(activeClient, 'kanal bulunamadı');
      throw friendlyError(
        `Kanal (${channelId}) "${guild.name}" sunucusunda bulunamadı. ` +
        'Kanal ID\'sinin bu sunucuya ait olduğundan ve botun kanalı görebildiğinden emin olun.'
      );
    }
  } else {
    // Guild ID girilmemiş: doğrudan kanal ID'siyle çöz.
    channel = activeClient.channels.cache.get(channelId)
           ?? await activeClient.channels.fetch(channelId).catch((error) => {
                log.warn(`channels.fetch(${channelId}) başarısız: ${error.message}`);
                return null;
              });

    if (!channel) {
      logDiagnostics(activeClient, 'kanal bulunamadı');
      throw friendlyError(
        `Kanal (${channelId}) bulunamadı. Kanal ID'sini kontrol edin ve botun o sunucuya ekli olduğundan emin olun.`
      );
    }
  }

  if (!channel.isTextBased?.()) {
    throw friendlyError(`"${channel.name}" bir metin kanalı değil. Mesaj gönderilebilir bir kanal seçin.`);
  }

  log.debug(`Kanal çözüldü: #${channel.name} (${channel.id})`);
  return channel;
}

/**
 * Bir Discord kullanıcısına ÖZEL MESAJ (DM) gönderir.
 *
 * Görev hatırlatmaları kanala değil, yalnızca o günün görevlisine gider; kanal
 * yalnızca sabahki onay sorusu için kullanılır. Kullanıcı `users.fetch()` ile
 * çalışan kaydındaki Discord ID üzerinden bulunur, mesaj `user.send()` ile
 * iletilir (discord.js gerekli DM kanalını kendisi açar).
 *
 * HATA FIRLATMAZ. DM kapalıysa, bot engellenmişse veya ID yanlışsa sonuç
 * `{ ok: false }` olarak döner; çağıran log'a yazıp devam eder — cron durmaz.
 *
 * `lastError` bilerek GÜNCELLENMEZ: tek bir kişinin DM ayarı, botun genel
 * bağlantı durumu değildir; panelde bot "hata" görünmemelidir.
 *
 * @param {string} userId Discord kullanıcı ID'si (snowflake).
 * @param {string} content Gönderilecek metin.
 * @returns {Promise<{ ok: boolean, message: string, reason?: string }>}
 *   message — kullanıcıya gösterilebilir Türkçe açıklama.
 *   reason  — Discord'un ham hata metni (log satırlarında kullanılır).
 */
async function sendDirectMessage(userId, content) {
  try {
    const activeClient = await connect();
    const user = await activeClient.users.fetch(userId);

    await user.send(content);
    log.debug(`DM gönderildi → ${user.tag} (${userId})`);
    return { ok: true, message: 'Özel mesaj gönderildi.' };
  } catch (error) {
    return {
      ok: false,
      message: toFriendlyError(error),
      reason: String(error?.message ?? error),
    };
  }
}

/**
 * BUTONLU özel mesaj (DM) gönderir ve sonradan düzenlemek için kimliklerini döner.
 *
 * Görev onayı artık kanalda değil, adayın kendi DM'inde yürür: 17:00'de sıradaki
 * kişiye "yarın ofiste misin?" sorusu butonlarla buradan gider. Dönen
 * channelId, kullanıcıyla açılan DM kanalının kimliğidir; `editInteractive`
 * bununla mesajı sonradan güncelleyebilir.
 *
 * `sendDirectMessage` gibi HATA FIRLATMAZ ve `lastError`'ı kirletmez: bir kişinin
 * DM'i kapalıysa bu botun genel sağlığı değildir, akış sıradaki kişiye geçer.
 *
 * @param {string} userId Discord kullanıcı ID'si (snowflake).
 * @param {string} content
 * @param {import('discord.js').ActionRowBuilder[]} components
 * @returns {Promise<{ ok: boolean, message: string, channelId?: string, messageId?: string, reason?: string }>}
 */
async function sendInteractiveDirect(userId, content, components) {
  try {
    const activeClient = await connect();
    const user = await activeClient.users.fetch(userId);

    const sent = await user.send({ content, components });
    log.debug(`Butonlu DM gönderildi → ${user.tag} (${userId})`);

    return {
      ok: true,
      message: 'Özel mesaj gönderildi.',
      channelId: sent.channelId,
      messageId: sent.id,
    };
  } catch (error) {
    return {
      ok: false,
      message: toFriendlyError(error),
      reason: String(error?.message ?? error),
    };
  }
}

/**
 * Butonlu (etkileşimli) mesaj gönderir; sonradan düzenlemek için kimliklerini döner.
 *
 * Kanal her çağrıda AÇIKÇA belirtilir — görev mesajı yanlışlıkla yemek kanalına
 * (veya tersi) düşemesin diye varsayılan kanal bilerek yoktur.
 *
 * @param {'duty'|'meal'} channelKey Hedef kanal.
 * @param {string} content
 * @param {import('discord.js').ActionRowBuilder[]} components
 * @returns {Promise<{ ok: boolean, message: string, channelId?: string, messageId?: string }>}
 */
async function sendInteractive(channelKey, content, components) {
  try {
    const activeClient = await connect();
    const channel = await resolveChannel(activeClient, channelKey);

    const sent = await channel.send({ content, components });
    lastError = null;
    log.debug(`Etkileşimli mesaj gönderildi → #${channel.name} (${sent.id})`);
    return { ok: true, message: 'Mesaj gönderildi.', channelId: channel.id, messageId: sent.id };
  } catch (error) {
    const friendly = toFriendlyError(error);
    lastError = friendly;
    log.error('Etkileşimli mesaj gönderilemedi', friendly);
    return { ok: false, message: friendly };
  }
}

/**
 * Var olan bir mesajı (id ile) düzenler. Onay akışını tazelemek için kullanılır.
 *
 * Kanal doğrudan `channelId` ile çözülür (ayarlardaki kanaldan bağımsız); böylece
 * mesaj hangi kanalda gönderildiyse orada düzenlenir — sunucu yeniden başlasa bile.
 *
 * @returns {Promise<{ ok: boolean, message: string }>}
 */
async function editInteractive(channelId, messageId, content, components) {
  try {
    const activeClient = await connect();
    const channel = await activeClient.channels.fetch(channelId);
    if (!channel?.isTextBased?.()) {
      return { ok: false, message: 'Kanal bulunamadı veya metin kanalı değil.' };
    }
    const message = await channel.messages.fetch(messageId);
    await message.edit({ content, components: components ?? [] });
    log.debug(`Etkileşimli mesaj düzenlendi (${messageId}).`);
    return { ok: true, message: 'Mesaj güncellendi.' };
  } catch (error) {
    // Mesaj silinmiş olabilir; çağıran yeni mesaj göndermeye karar verir.
    const friendly = toFriendlyError(error);
    log.warn(`Etkileşimli mesaj düzenlenemedi (${messageId}): ${friendly}`);
    return { ok: false, message: friendly };
  }
}

/**
 * Bağlantıyı sınar (Ayarlar sayfasındaki "Bağlantıyı Test Et").
 *
 * Teşhis bilgisini HER ZAMAN loglar — başarılı olsa bile. Böylece bir sorun
 * çıktığında "bot hangi sunucularda?" sorusunun yanıtı loglarda hazır durur.
 *
 * @returns {Promise<{ ok: boolean, message: string, diagnostics?: object }>}
 */
async function testConnection() {
  try {
    const activeClient = await connect();
    const info = logDiagnostics(activeClient, 'bağlantı testi');

    // Her kanal AYRI AYRI sınanır: biri yanlışsa diğerinin doğru olduğu bilgisi
    // kaybolmasın, admin hangisini düzelteceğini görsün.
    const results = [];
    for (const [key, meta] of Object.entries(settingsService.CHANNEL_KEYS)) {
      if (!settingsService.get(meta.settingKey)) {
        results.push({ ok: false, text: `${meta.label}: tanımlı değil` });
        continue;
      }
      try {
        const channel = await resolveChannel(activeClient, key);
        results.push({ ok: true, text: `${meta.label}: #${channel.name}`, guildName: channel.guild?.name });
      } catch (error) {
        results.push({ ok: false, text: `${meta.label}: ${toFriendlyError(error)}` });
      }
    }

    const guildName = results.find((r) => r.guildName)?.guildName;
    const allOk = results.every((r) => r.ok);
    const header = `Bot: ${activeClient.user.tag}${guildName ? ` — Sunucu: ${guildName}` : ''}`;

    if (results.every((r) => !r.ok) && info.guilds.length > 0) {
      return {
        ok: false,
        message: `${header}. Hiçbir kanal kullanılamıyor — ${results.map((r) => r.text).join(' · ')}. ` +
                 `Bot şu sunucularda: ${info.guilds.map((g) => `"${g.name}" (${g.id})`).join(', ')}.`,
        diagnostics: info,
      };
    }

    return {
      ok: allOk,
      message: `${allOk ? 'Bağlantı başarılı' : 'Bağlantı kuruldu, bazı kanallar eksik'}. ` +
               `${header} — ${results.map((r) => r.text).join(' · ')}`,
      diagnostics: info,
    };
  } catch (error) {
    return {
      ok: false,
      message: toFriendlyError(error),
      diagnostics: client ? getDiagnostics(client) : null,
    };
  }
}

/**
 * Panelde gösterilecek anlık durum.
 *
 * `guilds` alanı Ayarlar sayfasında listelenir: kullanıcı doğru Guild ID'yi
 * terminale bakmadan, kopyalayabileceği biçimde görür.
 */
function getStatus() {
  if (!isConfigured()) {
    return { state: 'unconfigured', label: 'Yapılandırılmadı', detail: 'Discord bot token girilmemiş.', guilds: [] };
  }
  if (client?.isReady()) {
    const info = getDiagnostics(client);
    return {
      state: 'online',
      label: 'Bağlı',
      detail: `Bot: ${client.user.tag}`,
      guilds: info.guilds,
      guildIdMatches: info.guildIdMatches,
      settingsGuildId: info.settingsGuildId,
    };
  }
  if (lastError) {
    // Bot bağlanmış ama yapılandırma hatası varsa (örn. yanlış Guild ID),
    // sunucu listesini yine göster — kullanıcının ihtiyacı tam olarak budur.
    const info = client ? getDiagnostics(client) : null;
    return {
      state: 'error',
      label: 'Hata',
      detail: lastError,
      guilds: info?.guilds ?? [],
      guildIdMatches: info?.guildIdMatches ?? false,
      settingsGuildId: info?.settingsGuildId ?? '',
    };
  }
  return { state: 'offline', label: 'Bağlanmadı', detail: 'Bot henüz bağlanmadı.', guilds: [] };
}

/**
 * Açılışta çağrılır. Token varsa arka planda bağlanmayı dener.
 * Bağlantı başarısız olsa bile sunucunun açılmasını engellemez.
 */
function initialize() {
  if (!isConfigured()) {
    log.warn('Token tanımlı değil, bot devre dışı. Ayarlar sayfasından ekleyebilirsiniz.');
    return;
  }
  connect().catch((error) => {
    log.error('Açılışta bağlanılamadı', error.message);
  });
  startConnectionWatchdog();
}

/**
 * GATEWAY WATCHDOG — "sessiz zombi bağlantı" koruması.
 *
 * NEDEN GEREKLİ?
 * ---------------
 * discord.js normalde kopan bağlantıyı kendi içinde yeniden kurar; ama bir
 * oturum Discord tarafında TAMAMEN geçersiz kılınırsa (örn. AYNI TOKEN ile
 * eşzamanlı ikinci bir `client.login()` — bir teşhis script'i, ikinci bir
 * kopya süreç vb. — Discord bazen ESKİ oturumu kapatır) istemci süreç
 * çökmeden "yarı ölü" kalabilir: `client.isReady()` hâlâ true dönebilir,
 * process ayaktadır, HTTP sağlık kontrolü (yalnızca Express portunu yoklar)
 * "healthy" der — ama gateway WebSocket'i ölüdür. Sonuç: Discord'da butonlar
 * görünür ama HİÇBİR interactionCreate olayı ulaşmaz; kullanıcı "Uygulama
 * zamanında yanıt vermedi" görür ve sunucu loglarında HİÇBİR iz kalmaz (bkz.
 * bu dosyadaki shardDisconnect/shardError logları — onlar da tetiklenmeyebilir
 * çünkü olay gerçek bir "disconnect" olarak algılanmamış olabilir).
 *
 * Bu fonksiyon `client.ws.status`'u (gerçek WebSocketManager durumu,
 * `isReady()`'den daha güvenilir bir sinyal) periyodik olarak kontrol eder.
 * Art arda iki kontrolde (yaklaşık 2 dakika) READY (0) değilse, bağlantıyı
 * tamamen kapatıp yeniden kurar — kullanıcı hiçbir şey yapmadan kendi kendine
 * toparlanır.
 */
let watchdogUnhealthyStreak = 0;
let watchdogRunning = false;

function startConnectionWatchdog() {
  setInterval(() => {
    watchdogTick().catch((error) => {
      log.error('Watchdog kontrolü sırasında beklenmeyen hata', error);
    });
  }, 60_000).unref();
}

async function watchdogTick() {
  if (watchdogRunning || !isConfigured()) return;

  // Bağlantı zaten kuruluyor/yeniden kuruluyorsa araya girme.
  if (loginPromise) return;

  // client.ws.status === 0 -> READY. Herhangi bir başka değer (CONNECTING,
  // RECONNECTING, DISCONNECTED, IDENTIFYING, RESUMING...) sağlıksız sayılır.
  const wsStatus = client?.ws?.status;
  const healthy = client != null && wsStatus === 0;

  if (healthy) {
    watchdogUnhealthyStreak = 0;
    return;
  }

  watchdogUnhealthyStreak += 1;
  log.warn(`Watchdog: bağlantı sağlıksız görünüyor (ws.status=${wsStatus}, ardışık=${watchdogUnhealthyStreak}).`);

  if (watchdogUnhealthyStreak < 2) return; // Geçici bir yeniden bağlanma denemesine karışma.

  watchdogUnhealthyStreak = 0;
  watchdogRunning = true;
  log.error('Watchdog: bağlantı ~2 dakikadır sağlıksız, zorla yeniden bağlanılıyor.');
  try {
    await reconnect();
  } catch (error) {
    log.error('Watchdog: yeniden bağlanma başarısız', error);
  } finally {
    watchdogRunning = false;
  }
}

module.exports = {
  initialize,
  connect,
  disconnect,
  reconnect,
  sendDirectMessage,
  sendInteractiveDirect,
  sendInteractive,
  editInteractive,
  testConnection,
  getStatus,
  isConfigured,
  getDiagnostics,
  logDiagnostics,
  // Test edilebilirlik için dışa açılır (bkz. scripts/discord-teshis.js).
  resolveGuild,
  resolveChannel,
  buildGuildNotFoundMessage,
};
