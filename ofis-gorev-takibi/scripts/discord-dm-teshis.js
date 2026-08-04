#!/usr/bin/env node
'use strict';

/**
 * DM (özel mesaj) gönderim teşhis aracı.
 *
 *     node scripts/discord-dm-teshis.js <hedef_user_id>
 *
 * "Cannot send messages to this user due to having no mutual guilds" (403)
 * hatasının GERÇEK nedenini kanıtlamak için, canlı/çalışan bot bağlantısı
 * üzerinden adım adım şunları loglar (tahmin YOK, yalnızca gerçek runtime
 * verisi):
 *
 *   1. Bot ID
 *   2. Bot adı (tag)
 *   3. Guild ID (ayarlardan)
 *   4. Guild adı
 *   5. Guild'deki toplam üye sayısı
 *   6. Hedef User ID
 *   7. guild.members.fetch(userId) sonucu
 *   8. Botun bulunduğu TÜM sunucularda bu kullanıcı var mı? (mutual guild kontrolü)
 *   9. client.guilds.cache içeriği (tam liste)
 *  10. client.user.id ve client.application.id
 *
 * Sonra: Guild bulundu mu? / Kullanıcı guild içinde mi? / Discord etiketi ne? —
 * bu üç soru yanıtlanmadan DM denemez; hangi adımda durduğu net görülür.
 *
 * Bu araç GERÇEK bot bağlantısını kullanır (aynı token, aynı bot.js kodu);
 * mevcut sunucu süreciyle AYNI ANDA ayrı bir Gateway oturumu açar, işi
 * bitince kapatır — üretim sürecine dokunmaz.
 */

const { initializeDatabase } = require('../src/database/schema');
const settings = require('../src/services/settings.service');
const bot = require('../src/discord/bot');

function line() {
  console.log('────────────────────────────────────────────────────────');
}

async function main() {
  const targetUserId = process.argv[2];
  if (!targetUserId) {
    console.log('\nKullanım: node scripts/discord-dm-teshis.js <hedef_discord_user_id>\n');
    process.exit(1);
  }

  initializeDatabase();

  console.log('\n════════════════════════════════════════════════════════');
  console.log('  DM Gönderim Teşhisi');
  console.log('════════════════════════════════════════════════════════\n');

  const guildIdSetting = settings.get('discord_guild_id');

  console.log('Discord\'a bağlanılıyor (canlı bot, aynı token)...\n');
  const client = await bot.connect();

  // 1, 2, 10) Bot kimliği ve application id
  console.log('1) Bot ID              :', client.user.id);
  console.log('2) Bot adı (tag)       :', client.user.tag);
  console.log('10) client.user.id     :', client.user.id);
  console.log('    client.application.id:', client.application?.id ?? '(client.application henüz yok)');
  line();

  // 9) guilds.cache tam listesi
  console.log('9) client.guilds.cache içeriği:');
  const allGuilds = [...client.guilds.cache.values()];
  if (allGuilds.length === 0) {
    console.log('   (BOŞ — bot hiçbir sunucuda değil)');
  } else {
    for (const g of allGuilds) {
      console.log(`   • ${g.name}  (id: ${g.id}, memberCount: ${g.memberCount})`);
    }
  }
  line();

  // 3, 4, 5) Ayarlardaki guild
  console.log('3) Ayarlardaki Guild ID:', guildIdSetting || '(boş)');
  let targetGuild = null;
  if (guildIdSetting) {
    targetGuild = client.guilds.cache.get(guildIdSetting) ?? await client.guilds.fetch(guildIdSetting).catch(() => null);
  }
  console.log('4) Guild adı           :', targetGuild ? targetGuild.name : '(BULUNAMADI)');
  console.log('5) Guild toplam üye    :', targetGuild ? targetGuild.memberCount : '(bilinmiyor — guild bulunamadı)');
  line();

  // 6) Hedef kullanıcı
  console.log('6) Gönderilmeye çalışılan User ID:', targetUserId);
  line();

  // 7) guild.members.fetch
  let memberInTargetGuild = null;
  if (targetGuild) {
    console.log(`7) targetGuild.members.fetch("${targetUserId}") deneniyor...`);
    try {
      memberInTargetGuild = await targetGuild.members.fetch(targetUserId);
      console.log(`   ✓ Bulundu: ${memberInTargetGuild.user.tag}  (nickname: ${memberInTargetGuild.nickname ?? '(yok)'})`);
    } catch (error) {
      console.log(`   ✗ Bulunamadı: ${error.message} (kod: ${error.code ?? '?'})`);
    }
  } else {
    console.log('7) targetGuild.members.fetch(...) ÇALIŞTIRILAMADI: guild bulunamadığı için atlandı.');
  }
  line();

  // 8) Botun bulunduğu TÜM guild'lerde mutual üyelik taraması
  console.log('8) Botun bulunduğu TÜM sunucularda bu kullanıcı aranıyor (ortak guild kontrolü):');
  let mutualGuild = null;
  for (const g of allGuilds) {
    try {
      const member = await g.members.fetch(targetUserId);
      console.log(`   ✓ "${g.name}" (${g.id}) sunucusunda ÜYE: ${member.user.tag}`);
      if (!mutualGuild) mutualGuild = { guild: g, member };
    } catch (error) {
      console.log(`   ✗ "${g.name}" (${g.id}) sunucusunda ÜYE DEĞİL (${error.code ?? error.message})`);
    }
  }
  line();

  // ── DM göndermeden önceki üç soru ──
  console.log('DM göndermeden önceki kontrol:');
  console.log(`  • Guild bulundu mu?              : ${targetGuild ? 'EVET (' + targetGuild.name + ')' : 'HAYIR'}`);
  console.log(`  • Kullanıcı guild içinde bulundu mu?: ${memberInTargetGuild ? 'EVET' : 'HAYIR'}`);
  console.log(`  • Kullanıcının Discord etiketi     : ${memberInTargetGuild?.user?.tag ?? mutualGuild?.member?.user?.tag ?? '(bilinmiyor — hiçbir ortak sunucuda bulunamadı)'}`);
  console.log(`  • Botla ortak sunucusu var mı (herhangi bir guild)?: ${mutualGuild ? 'EVET (' + mutualGuild.guild.name + ')' : 'HAYIR — hiçbir ortak sunucu yok'}`);
  line();

  if (!mutualGuild) {
    console.log('SONUÇ: Bu kullanıcı, botun üye olduğu HİÇBİR sunucuda bulunamadı.');
    console.log('Discord, botların yalnızca ORTAK SUNUCUSU olan kullanıcılara DM atmasına izin verir.');
    console.log('Bu, koddan kaynaklı bir hata DEĞİL — Discord platformunun anti-spam kuralıdır.');
    console.log('DM denemesi yine de aşağıda yapılacak (gerçek Discord yanıtını göstermek için).\n');
  } else {
    console.log('SONUÇ: Kullanıcı botla ortak bir sunucuda. DM gönderimi normalde başarılı olmalı.\n');
  }

  // ── Gerçek DM denemesi (üretimin kullandığı AYNI kod yolu) ──
  console.log('DM gönderimi deneniyor (bot.sendDirectMessage — üretimle aynı kod yolu)...');
  const result = await bot.sendDirectMessage(targetUserId, '🧪 DM teşhis aracından gönderilen deneme mesajı.');
  console.log('SONUÇ:', JSON.stringify(result, null, 2));

  console.log('\n════════════════════════════════════════════════════════\n');

  await bot.disconnect();
  process.exit(0);
}

main().catch((error) => {
  console.error('\nBeklenmeyen hata:', error);
  process.exit(1);
});
