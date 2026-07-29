#!/usr/bin/env node
'use strict';

/**
 * Discord bağlantı teşhis aracı.
 *
 *     npm run discord:teshis
 *
 * Kayıtlı token ile Discord'a bağlanır ve şunları raporlar:
 *   - Bot kimliği (tag / id)
 *   - Ayarlardaki Guild ID ve Kanal ID
 *   - Botun GERÇEKTE üye olduğu tüm sunucular (id + ad)
 *   - Girilen ID'lerin bunlarla eşleşip eşleşmediği
 *   - Hedef kanalın bulunup bulunmadığı ve yazma izni
 *
 * "Unknown Guild" hatası alıyorsanız yanıt buradadır: aşağıdaki sunucu listesinde
 * Ayarlar'a girdiğiniz ID yoksa, ya ID yanlıştır ya da bot o sunucuya davet
 * edilmemiştir. `guilds.fetch()` yalnızca botun ÜYE OLDUĞU sunucuları getirebilir.
 *
 * Bu araç hiçbir mesaj göndermez ve hiçbir veriyi değiştirmez.
 */

const { initializeDatabase } = require('../src/database/schema');
const settings = require('../src/services/settings.service');
const bot = require('../src/discord/bot');

/** Kanalda yazma izni var mı? (kanal özelse en sık sorun budur) */
function describePermissions(channel, botId) {
  try {
    const perms = channel.permissionsFor?.(botId);
    if (!perms) return 'izinler okunamadı';
    const canView = perms.has('ViewChannel');
    const canSend = perms.has('SendMessages');
    return `ViewChannel=${canView ? '✓' : '✗'}  SendMessages=${canSend ? '✓' : '✗'}`;
  } catch {
    return 'izinler okunamadı';
  }
}

async function main() {
  initializeDatabase();

  console.log('\n════════════════════════════════════════════════════════');
  console.log('  Discord Bağlantı Teşhisi');
  console.log('════════════════════════════════════════════════════════\n');

  const token = settings.get('discord_bot_token');
  const guildId = settings.get('discord_guild_id');

  // Görev ve yemek kanalları ayrı ayrı okunur; ikisi de kontrol edilir.
  const channels = Object.entries(settings.CHANNEL_KEYS).map(([key, meta]) => ({
    key,
    label: meta.label,
    id: settings.get(meta.settingKey),
  }));

  console.log('Kayıtlı ayarlar:');
  console.log(`  Bot Token  : ${token ? `${'•'.repeat(12)}${token.slice(-4)}  (uzunluk: ${token.length})` : '(BOŞ)'}`);
  console.log(`  Guild ID   : ${guildId || '(boş)'}`);
  for (const channel of channels) {
    console.log(`  ${channel.label.padEnd(11)}: ${channel.id || '(boş)'}`);
  }
  console.log('');

  if (!token) {
    console.log('✗ Token tanımlı değil. Ayarlar sayfasından girin.\n');
    process.exit(1);
  }

  // --- Girdi biçimi kontrolleri (bağlanmadan önce ucuz kontroller) ---
  const problems = [];
  if (guildId && !/^\d{17,20}$/.test(guildId)) {
    problems.push(`Guild ID biçimi geçersiz: "${guildId}" (17-20 haneli sayı olmalı)`);
  }
  for (const channel of channels) {
    if (channel.id && !/^\d{17,20}$/.test(channel.id)) {
      problems.push(`${channel.label} ID biçimi geçersiz: "${channel.id}" (17-20 haneli sayı olmalı)`);
    }
    if (guildId && guildId === channel.id) {
      problems.push(`Guild ID ile ${channel.label} ID aynı — bunlar farklı ID'lerdir.`);
    }
  }
  if (problems.length > 0) {
    console.log('Girdi uyarıları:');
    for (const p of problems) console.log(`  ⚠ ${p}`);
    console.log('');
  }

  // --- Bağlan ---
  console.log('Discord\'a bağlanılıyor...\n');
  let client;
  try {
    client = await bot.connect();
  } catch (error) {
    console.log(`✗ Bağlanılamadı: ${error.message}\n`);
    process.exit(1);
  }

  const info = bot.getDiagnostics(client);

  console.log('────────────────────────────────────────────────────────');
  console.log(`  Bot            : ${info.botTag}  (id: ${info.botId})`);
  console.log(`  Hazır (ready)  : ${info.isReady}`);
  console.log(`  guilds.cache   : ${info.guildCacheSize} sunucu`);
  console.log('────────────────────────────────────────────────────────\n');

  // --- Botun bulunduğu sunucular: sorunun cevabı burada ---
  console.log('Botun ÜYE OLDUĞU sunucular:');
  if (info.guilds.length === 0) {
    console.log('  (hiçbiri)\n');
    console.log('  ✗ SORUN BULUNDU: Bot hiçbir sunucuda değil.');
    console.log('    Bu yüzden guilds.fetch() her ID için "Unknown Guild" döner.');
    console.log('');
    console.log('    Çözüm:');
    console.log('      1. https://discord.com/developers/applications → uygulamanız');
    console.log('      2. OAuth2 → URL Generator');
    console.log('      3. Scopes: "bot"   |   Bot Permissions: "Send Messages"');
    console.log('      4. Üretilen bağlantıyı tarayıcıda açıp sunucunuzu seçin.\n');
    await bot.disconnect();
    process.exit(1);
  }

  for (const guild of info.guilds) {
    const mark = guild.id === guildId ? '  ←  Ayarlardaki Guild ID ile EŞLEŞİYOR ✓' : '';
    console.log(`  • ${guild.name}`);
    console.log(`      id: ${guild.id}${mark}`);
  }
  console.log('');

  // --- Guild ID doğrulaması ---
  if (!guildId) {
    console.log('  ℹ Guild ID boş. Kanal doğrudan ID ile çözülecek (bu da çalışır).');
    console.log(`    İsterseniz yukarıdaki ID'lerden birini Ayarlar'a girebilirsiniz.\n`);
  } else if (!info.guildIdMatches) {
    console.log('  ✗ SORUN BULUNDU: Ayarlardaki Guild ID botun bulunduğu sunucular arasında YOK.');
    console.log(`    Girdiğiniz : ${guildId}`);
    console.log(`    Olması gereken (botun bulunduğu): ${info.guilds.map((g) => g.id).join(', ')}`);
    console.log('');
    console.log('    Çözüm (biri):');
    console.log(`      a) Ayarlar → Guild ID alanına "${info.guilds[0].id}" yazın ("${info.guilds[0].name}")`);
    console.log('      b) Guild ID alanını BOŞ bırakın (kanal doğrudan ID ile çözülür)');
    console.log('      c) Botu istediğiniz sunucuya OAuth2 bağlantısıyla ekleyin\n');
    await bot.disconnect();
    process.exit(1);
  } else {
    console.log('  ✓ Guild ID doğru.\n');
  }

  // --- Kanal doğrulaması (her kanal ayrı ayrı) ---
  console.log('Kanallar kontrol ediliyor...');
  let failures = 0;

  for (const channel of channels) {
    if (!channel.id) {
      console.log(`  ✗ ${channel.label}: ID boş. Ayarlar sayfasından girin.`);
      failures += 1;
      continue;
    }

    try {
      const resolved = await bot.resolveChannel(client, channel.key);
      console.log(`  ✓ ${channel.label}: #${resolved.name}  (id: ${resolved.id})`);
      if (resolved.guild) {
        console.log(`      Sunucu     : ${resolved.guild.name}  (${resolved.guild.id})`);
      }
      console.log(`      Bot izinleri: ${describePermissions(resolved, info.botId)}`);
    } catch (error) {
      console.log(`  ✗ ${channel.label}: ${error.message}`);
      failures += 1;
    }
  }

  console.log('');
  console.log('════════════════════════════════════════════════════════');
  if (failures === 0) {
    console.log('  ✓ Her şey yolunda. Görev ve yemek mesajları kendi kanallarına gidecek.');
  } else {
    console.log(`  ✗ ${failures} kanal kullanılamıyor (yukarıya bakın).`);
  }
  console.log('════════════════════════════════════════════════════════\n');

  await bot.disconnect();
  process.exit(failures === 0 ? 0 : 1);
}

main().catch((error) => {
  console.error('\nBeklenmeyen hata:', error);
  process.exit(1);
});
