"""
Arka planda periyodik olarak Google Sheets'i okuyup önceki durumla karşılaştırır.
Tespit edilen olaylar:

  - yeni_kayit      : row_key daha önce görülmemiş (yeni fırsat eklenmiş)
  - kaybedildi      : Fırsat Durumu "Kaybedildi" olmuş (öncesinde değildi)
  - durum_degisti   : Satış Aşaması veya Fırsat Durumu değişmiş (kaybedildi hariç)
  - guncelleme_yok  : "Devam Ediyor" durumundaki bir fırsatın Son Güncelleme
                       tarihi, sunucunun stale_days eşiğinden daha eski

Her guild kendi poll_minutes / stale_days ayarına göre çalışır; bu yüzden
tek bir global döngü yerine, her guild için ayrı bir tasks.Loop örneği tutulur.

Buna ek olarak, kullanıcılar `/sheet-ekle` ile kendi kişisel Google Sheet
kaynaklarını ekleyebilir (storage.sheet_sources). Her kişisel kaynak da kendi
tasks.Loop'una sahiptir ve state'i guild'in ana sheet'inden tamamen izole
(storage.get_source_row_states vb.) tutulur. Bir kaynağın olayları, o kaynağa
özel bir watch (source_id eşleşen) yoksa varsayılan olarak sahibine DM olarak gider.
"""
from datetime import datetime, timezone

import discord
from discord.ext import commands, tasks

import config
import storage
import sheets_client


def _parse_tarih(value: str):
    """DD.MM.YYYY formatını datetime'a çevirir, olmazsa None döner."""
    value = (value or "").strip()
    for fmt in ("%d.%m.%Y", "%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


class Notifications(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._guild_loops: dict[int, tasks.Loop] = {}
        self._source_loops: dict[int, tasks.Loop] = {}

    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            self.start_guild_loop(guild.id)
        for source in storage.all_sheet_sources():
            self.start_source_loop(source["id"])

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        self.start_guild_loop(guild.id)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        """
        Kullanıcı sunucudan ayrılınca (kick/ban dahil) botu kullanmayı bıraktığı
        varsayılır: kendi eklediği tüm kişisel sheet kaynakları (ve bunlara bağlı
        poll döngüleri) ile tüm bildirim abonelikleri (ana sheet dahil) silinir.
        Aksi halde artık kimseye ulaşamayan bir DM hedefi için sonsuza kadar
        boşa Google Sheets taraması yapılmaya devam ederdi.
        """
        guild_id = str(member.guild.id)
        user_id = str(member.id)

        sources = storage.list_sheet_sources_for_user(guild_id, user_id)
        for source in sources:
            self.stop_source_loop(source["id"])
            storage.delete_sheet_source(source["id"], user_id)

        removed_watches = storage.delete_watches_for_user(guild_id, user_id)

        if sources or removed_watches:
            print(f"[notifications] {user_id} '{member.guild.name}' sunucusundan ayrıldı: "
                  f"{len(sources)} kişisel sheet ve {removed_watches} abonelik temizlendi.")

    def start_guild_loop(self, guild_id: int):
        if guild_id in self._guild_loops:
            return
        settings = storage.get_guild_settings(str(guild_id))
        minutes = max(1, int(settings["poll_minutes"]))

        loop = tasks.loop(minutes=minutes)(self._make_check_fn(guild_id))
        self._guild_loops[guild_id] = loop
        loop.start()

    def restart_guild_loop_with_new_interval(self, guild_id: int, minutes: int):
        """
        Süreyi değiştirir VE döngüyü hemen yeniden başlatır ki yeni ayar
        bir sonraki uzun bekleme süresini beklemeden anında etkili olsun
        (özellikle test sırasında kontrolü hızlandırmak için önemli).
        """
        old_loop = self._guild_loops.get(guild_id)
        if old_loop is not None:
            old_loop.cancel()

        new_loop = tasks.loop(minutes=max(1, minutes))(self._make_check_fn(guild_id))
        self._guild_loops[guild_id] = new_loop
        new_loop.start()  # start() ilk kontrolü hemen çalıştırır, sonra bekler

    def _make_check_fn(self, guild_id: int):
        async def _check():
            await self._check_guild(guild_id)
        return _check

    # ---------------- Kişisel sheet_sources döngüleri ----------------

    def start_source_loop(self, source_id: int):
        if source_id in self._source_loops:
            return
        source = storage.get_sheet_source(source_id)
        if source is None:
            return
        minutes = source.get("poll_minutes")
        if not minutes:
            guild_settings = storage.get_guild_settings(source["guild_id"])
            minutes = guild_settings["poll_minutes"]
        minutes = max(1, int(minutes))

        loop = tasks.loop(minutes=minutes)(self._make_source_check_fn(source_id))
        self._source_loops[source_id] = loop
        loop.start()

    def restart_source_loop(self, source_id: int):
        self.stop_source_loop(source_id)
        self.start_source_loop(source_id)

    def stop_source_loop(self, source_id: int):
        loop = self._source_loops.pop(source_id, None)
        if loop is not None:
            loop.cancel()

    def _make_source_check_fn(self, source_id: int):
        async def _check():
            await self._check_source(source_id)
        return _check

    # ---------------- Ortak fark tespiti ----------------

    def _diff_events(self, current_rows: dict, previous_rows: dict, stale_days: int,
                      now: datetime, get_last_notified, mark_notified) -> list:
        """
        current_rows / previous_rows karşılaştırılıp olay listesi üretir. Yan etki olarak
        eskime bildirimi tetiklenen satırlar için mark_notified(row_key) çağrılır.
        get_last_notified / mark_notified: guild ana sheet'i ile kişisel sheet_sources
        arasında farklı (izole) state'e yazması için caller tarafından enjekte edilir.
        """
        events = []  # (event_type, firma, mesaj_ozeti, row)

        for row_key, row in current_rows.items():
            prev = previous_rows.get(row_key)

            if prev is None:
                events.append(("yeni_kayit", row[config.COL_FIRMA],
                                "Yeni fırsat tabloya eklendi.", row))
            else:
                durum_simdi = row[config.COL_FIRSAT_DURUMU]
                durum_once = prev.get(config.COL_FIRSAT_DURUMU, "")
                asama_simdi = row[config.COL_SATIS_ASAMASI]
                asama_once = prev.get(config.COL_SATIS_ASAMASI, "")

                if durum_simdi.lower() == "kaybedildi" and durum_once.lower() != "kaybedildi":
                    events.append(("kaybedildi", row[config.COL_FIRMA],
                                    "Fırsat durumu 'Kaybedildi' olarak güncellendi.", row))
                elif durum_simdi != durum_once or asama_simdi != asama_once:
                    events.append(("durum_degisti", row[config.COL_FIRMA],
                                    f"'{asama_once or '-'} / {durum_once or '-'}' -> "
                                    f"'{asama_simdi} / {durum_simdi}'", row))

            # Eskime kontrolü (yalnızca hâlâ devam eden fırsatlar için)
            if row[config.COL_FIRSAT_DURUMU].lower() == "devam ediyor":
                son_guncelleme = _parse_tarih(row[config.COL_SON_GUNCELLEME])
                if son_guncelleme is not None:
                    gun_farki = (now.replace(tzinfo=None) - son_guncelleme).days
                    if gun_farki >= stale_days:
                        last_notified = get_last_notified(row_key)
                        should_notify = True
                        if last_notified:
                            last_dt = datetime.fromisoformat(last_notified)
                            if (now - last_dt).days < stale_days:
                                should_notify = False
                        if should_notify:
                            events.append(("guncelleme_yok", row[config.COL_FIRMA],
                                           f"{gun_farki} gündür güncellenmedi "
                                           f"(eşik: {stale_days} gün).", row))
                            mark_notified(row_key)

        return events

    async def _check_guild(self, guild_id: int):
        guild = self.bot.get_guild(guild_id)
        if guild is None:
            return

        settings = storage.get_guild_settings(str(guild_id))

        try:
            current_rows = sheets_client.fetch_rows(
                spreadsheet_id=settings.get("spreadsheet_id"),
                worksheet_name=settings.get("worksheet_name"),
            )
        except Exception as e:
            print(f"[notifications] Sheet okunamadı (guild={guild_id}): {e}")
            return

        previous_rows = storage.get_all_row_states()
        stale_days = int(settings["stale_days"])
        now = datetime.now(timezone.utc)

        events = self._diff_events(
            current_rows, previous_rows, stale_days, now,
            storage.get_stale_notified_at, storage.mark_stale_notified,
        )

        for row_key, row in current_rows.items():
            storage.upsert_row_state(row_key, row)

        storage.delete_row_states_not_in(list(current_rows.keys()))

        if events:
            await self._dispatch_events(guild_id, events)

    async def _check_source(self, source_id: int):
        source = storage.get_sheet_source(source_id)
        if source is None:
            # Kaynak silinmiş; döngü stop_source_loop çağrılmadan buraya düştüyse
            # (ör. beklenmedik bir yol) kendini durdursun.
            self.stop_source_loop(source_id)
            return

        guild_id = int(source["guild_id"])
        guild = self.bot.get_guild(guild_id)
        if guild is None:
            return

        try:
            current_rows = sheets_client.fetch_rows(
                spreadsheet_id=source["spreadsheet_id"],
                worksheet_name=source["worksheet_name"],
            )
        except Exception as e:
            print(f"[notifications] Kişisel sheet okunamadı (source={source_id}, "
                  f"etiket={source['label']!r}): {e}")
            return

        previous_rows = storage.get_source_row_states(source_id)
        stale_days = source.get("stale_days")
        if not stale_days:
            stale_days = storage.get_guild_settings(source["guild_id"])["stale_days"]
        stale_days = int(stale_days)
        now = datetime.now(timezone.utc)

        events = self._diff_events(
            current_rows, previous_rows, stale_days, now,
            lambda rk: storage.get_source_stale_notified_at(source_id, rk),
            lambda rk: storage.mark_source_stale_notified(source_id, rk),
        )

        for row_key, row in current_rows.items():
            storage.upsert_source_row_state(source_id, row_key, row)

        storage.delete_source_row_states_not_in(source_id, list(current_rows.keys()))

        if events:
            await self._dispatch_source_events(source_id, guild_id, source["owner_user_id"], events)

    async def _dispatch_events(self, guild_id: int, events: list):
        watches = storage.list_watches_for_guild(str(guild_id))
        settings = storage.get_guild_settings(str(guild_id))
        default_channel_id = settings.get("default_channel_id")
        event_channels = storage.get_event_channels(str(guild_id))

        for event_type, firma, ozet, row in events:
            embed = self._build_embed(event_type, firma, ozet, row)

            matched_any_watch = False
            for w in watches:
                if w["event_type"] not in (event_type, "hepsi"):
                    continue
                if w["firma"] and w["firma"].lower() != firma.lower():
                    continue
                matched_any_watch = True
                await self._send(guild_id, w["deliver_channel_id"], w["user_id"], embed)

            if matched_any_watch:
                continue

            # Kimse özel abone değilse: önce bu olay türüne atanmış kanala,
            # o da yoksa sunucunun genel varsayılan kanalına düş.
            target_channel_id = (
                event_channels.get(event_type) or event_channels.get("hepsi") or default_channel_id
            )
            if target_channel_id:
                channel = self.bot.get_channel(int(target_channel_id))
                if channel:
                    await channel.send(embed=embed)

    async def _dispatch_source_events(self, source_id: int, guild_id: int,
                                       owner_user_id: str, events: list):
        """
        Kişisel sheet_sources kaynağından gelen olaylar. Bu kaynağa özel bir watch
        (source_id eşleşen) varsa oraya gönderilir; yoksa varsayılan olarak
        kaynağın sahibine doğrudan DM atılır.
        """
        watches = storage.list_watches_for_source(source_id)

        for event_type, firma, ozet, row in events:
            embed = self._build_embed(event_type, firma, ozet, row)

            matched_any_watch = False
            for w in watches:
                if w["event_type"] not in (event_type, "hepsi"):
                    continue
                if w["firma"] and w["firma"].lower() != firma.lower():
                    continue
                matched_any_watch = True
                await self._send(guild_id, w["deliver_channel_id"], w["user_id"], embed)

            if not matched_any_watch:
                await self._send(guild_id, None, owner_user_id, embed)

    async def _send(self, guild_id: int, channel_id: str | None, user_id: str, embed: discord.Embed):
        try:
            if channel_id:
                channel = self.bot.get_channel(int(channel_id))
                if channel:
                    await channel.send(content=f"<@{user_id}>", embed=embed)
            else:
                user = await self.bot.fetch_user(int(user_id))
                await user.send(embed=embed)
        except discord.Forbidden:
            print(f"[notifications] Mesaj gönderilemedi (yetki yok): user={user_id}")
        except Exception as e:
            print(f"[notifications] Mesaj gönderilirken hata: {e}")

    @staticmethod
    def _build_embed(event_type: str, firma: str, ozet: str, row: dict) -> discord.Embed:
        renk_map = {
            "yeni_kayit": discord.Color.blue(),
            "kaybedildi": discord.Color.red(),
            "durum_degisti": discord.Color.gold(),
            "guncelleme_yok": discord.Color.orange(),
        }
        baslik_map = {
            "yeni_kayit": "🆕 Yeni Fırsat",
            "kaybedildi": "❌ Fırsat Kaybedildi",
            "durum_degisti": "🔄 Durum Değişti",
            "guncelleme_yok": "⏰ Güncelleme Bekleniyor",
        }
        embed = discord.Embed(
            title=f"{baslik_map.get(event_type, 'Bildirim')} — {firma}",
            description=ozet,
            color=renk_map.get(event_type, discord.Color.greyple()),
        )
        embed.add_field(name="Satış Aşaması", value=row[config.COL_SATIS_ASAMASI] or "-", inline=True)
        embed.add_field(name="Fırsat Durumu", value=row[config.COL_FIRSAT_DURUMU] or "-", inline=True)
        embed.add_field(name="Olasılık", value=row[config.COL_OLASILIK] or "-", inline=True)
        if row[config.COL_KAMERA]:
            embed.add_field(name="Kamera Sayısı", value=row[config.COL_KAMERA], inline=True)
        if row[config.COL_ARAC]:
            embed.add_field(name="Araç Sayısı", value=row[config.COL_ARAC], inline=True)
        embed.add_field(name="Son Güncelleme", value=row[config.COL_SON_GUNCELLEME] or "-", inline=True)
        if row[config.COL_NOT]:
            embed.add_field(name="Not", value=row[config.COL_NOT], inline=False)
        return embed


async def setup(bot: commands.Bot):
    await bot.add_cog(Notifications(bot))