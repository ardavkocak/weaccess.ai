"""
Kullanıcıların kendi bildirim tercihlerini ve kişisel Google Sheet kaynaklarını
yönettiği, yöneticilerin de sunucu genelindeki varsayılanları ayarladığı slash komutları.
"""
import re
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

import storage
import sheets_client
import config

EVENT_CHOICES = [
    app_commands.Choice(name="Hepsi", value="hepsi"),
    app_commands.Choice(name="Yeni fırsat eklendiğinde", value="yeni_kayit"),
    app_commands.Choice(name="Durum/aşama değiştiğinde", value="durum_degisti"),
    app_commands.Choice(name="Fırsat kaybedildiğinde", value="kaybedildi"),
    app_commands.Choice(name="Uzun süre güncellenmediğinde", value="guncelleme_yok"),
]

_SHEET_URL_RE = re.compile(r"/d/([a-zA-Z0-9-_]+)")


def _extract_spreadsheet_id(value: str) -> str:
    """Hem tam sheet URL'sini hem de direkt ID'yi kabul eder."""
    value = value.strip()
    match = _SHEET_URL_RE.search(value)
    return match.group(1) if match else value


class Settings(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ---------------- Kullanıcı komutları ----------------

    async def _kaynak_autocomplete(self, interaction: discord.Interaction, current: str):
        if interaction.guild_id is None:
            return []
        sources = storage.list_sheet_sources_for_user(
            str(interaction.guild_id), str(interaction.user.id)
        )
        current = (current or "").lower()
        return [
            app_commands.Choice(name=s["label"], value=s["label"])
            for s in sources if current in s["label"].lower()
        ][:25]

    @app_commands.command(name="bildirim-ekle", description="Belirli bir olay için bildirim aboneliği oluştur.")
    @app_commands.describe(
        tur="Hangi olayda bildirim almak istiyorsun?",
        firma="Sadece belirli bir firma için mi? (boş bırakılırsa tüm firmalar)",
        kanal="Bildirim bu kanala mı gelsin? (boş bırakılırsa sana DM atılır)",
        kaynak="Hangi sheet için? (boş bırakılırsa sunucunun ana sheet'i; kendi eklediğin "
               "bir sheet'in bildirimlerini başka yere yönlendirmek için etiketini seç)",
    )
    @app_commands.choices(tur=EVENT_CHOICES)
    @app_commands.autocomplete(kaynak=_kaynak_autocomplete)
    async def bildirim_ekle(
        self,
        interaction: discord.Interaction,
        tur: app_commands.Choice[str],
        firma: Optional[str] = None,
        kanal: Optional[discord.TextChannel] = None,
        kaynak: Optional[str] = None,
    ):
        source_id = None
        kaynak_metni = "sunucunun ana sheet'i"
        if kaynak:
            source = storage.get_sheet_source_by_label(
                str(interaction.guild_id), str(interaction.user.id), kaynak
            )
            if source is None:
                await interaction.response.send_message(
                    f"'{kaynak}' etiketli bir sheet'in yok. `/sheet-listele` ile "
                    f"kendi kaynaklarını görebilirsin.",
                    ephemeral=True,
                )
                return
            source_id = source["id"]
            kaynak_metni = f"'{kaynak}' sheet'in"

        watch_id = storage.add_watch(
            guild_id=str(interaction.guild_id),
            user_id=str(interaction.user.id),
            firma=firma,
            event_type=tur.value,
            deliver_channel_id=str(kanal.id) if kanal else None,
            source_id=source_id,
        )
        hedef = kanal.mention if kanal else "DM (özel mesaj)"
        firma_metni = f"**{firma}**" if firma else "**tüm firmalar**"
        await interaction.response.send_message(
            f"✅ Abonelik oluşturuldu (#{watch_id}): {kaynak_metni} için, {firma_metni} "
            f"kapsamında **{tur.name}** olayında {hedef} üzerinden bildirim alacaksın.",
            ephemeral=True,
        )

    @app_commands.command(name="bildirim-listele", description="Mevcut bildirim aboneliklerini listele.")
    async def bildirim_listele(self, interaction: discord.Interaction):
        watches = storage.list_watches_for_user(str(interaction.guild_id), str(interaction.user.id))
        if not watches:
            await interaction.response.send_message("Henüz bir aboneliğin yok.", ephemeral=True)
            return
        lines = []
        for w in watches:
            hedef = f"<#{w['deliver_channel_id']}>" if w["deliver_channel_id"] else "DM"
            firma = w["firma"] or "Tüm firmalar"
            kaynak = "Ana sheet"
            if w["source_id"]:
                source = storage.get_sheet_source(w["source_id"])
                kaynak = source["label"] if source else "(silinmiş sheet)"
            lines.append(f"`#{w['id']}` — {kaynak} — {firma} — {w['event_type']} — {hedef}")
        await interaction.response.send_message("\n".join(lines), ephemeral=True)

    @app_commands.command(name="bildirim-sil", description="Bir bildirim aboneliğini sil.")
    @app_commands.describe(id="Silinecek aboneliğin numarası (bildirim-listele ile görebilirsin)")
    async def bildirim_sil(self, interaction: discord.Interaction, id: int):
        ok = storage.remove_watch(id, str(interaction.user.id))
        if ok:
            await interaction.response.send_message(f"🗑️ #{id} numaralı abonelik silindi.", ephemeral=True)
        else:
            await interaction.response.send_message(
                "Böyle bir abonelik bulunamadı (ya da sana ait değil).", ephemeral=True
            )

    @app_commands.command(name="sheet-ekle", description="Kendi kişisel Google Sheet kaynağını ekle (ya da güncelle).")
    @app_commands.describe(
        etiket="Bu sheet'i ayırt etmek için kısa bir isim (örn. musteri-a)",
        spreadsheet_id="Sheet URL'sindeki /d/ ile /edit arasındaki kısım (tam URL de yapıştırabilirsin)",
        sekme_adi="Sekme (worksheet) adı, örn. Sales Pipeline",
        dakika="Kaç dakikada bir kontrol edilsin? (boş bırakılırsa sunucunun varsayılanı kullanılır)",
        eskime_gun="Kaç gün güncellenmeyen fırsat 'eski' sayılsın? (boş bırakılırsa sunucunun varsayılanı kullanılır)",
    )
    async def sheet_ekle(
        self,
        interaction: discord.Interaction,
        etiket: str,
        spreadsheet_id: str,
        sekme_adi: str,
        dakika: Optional[app_commands.Range[int, 1, 1440]] = None,
        eskime_gun: Optional[app_commands.Range[int, 1, 365]] = None,
    ):
        gerçek_id = _extract_spreadsheet_id(spreadsheet_id)
        source_id = storage.add_sheet_source(
            guild_id=str(interaction.guild_id),
            owner_user_id=str(interaction.user.id),
            label=etiket,
            spreadsheet_id=gerçek_id,
            worksheet_name=sekme_adi,
            poll_minutes=dakika,
            stale_days=eskime_gun,
        )
        notif_cog = self.bot.get_cog("Notifications")
        if notif_cog:
            notif_cog.restart_source_loop(source_id)
        await interaction.response.send_message(
            f"✅ '{etiket}' sheet'in kaydedildi (sheet `{gerçek_id}`, sekme `{sekme_adi}`).\n"
            f"Olayları varsayılan olarak sana DM olarak gelecek; başka bir kanala/kişiye "
            f"yönlendirmek istersen `/bildirim-ekle kaynak:{etiket}` kullanabilirsin.",
            ephemeral=True,
        )

    @app_commands.command(name="sheet-listele", description="Kendi eklediğin sheet kaynaklarını listele.")
    async def sheet_listele(self, interaction: discord.Interaction):
        sources = storage.list_sheet_sources_for_user(
            str(interaction.guild_id), str(interaction.user.id)
        )
        if not sources:
            await interaction.response.send_message(
                "Henüz kendi eklediğin bir sheet yok. `/sheet-ekle` ile ekleyebilirsin.",
                ephemeral=True,
            )
            return
        lines = []
        for s in sources:
            dakika = s["poll_minutes"] or "(varsayılan)"
            gun = s["stale_days"] or "(varsayılan)"
            lines.append(
                f"`{s['label']}` — sheet `{s['spreadsheet_id']}`, sekme `{s['worksheet_name']}` "
                f"— {dakika} dk / {gun} gün eskime eşiği"
            )
        await interaction.response.send_message("\n".join(lines), ephemeral=True)

    @app_commands.command(name="sheet-sil", description="Kendi eklediğin bir sheet kaynağını sil.")
    @app_commands.describe(etiket="Silinecek sheet'in etiketi (sheet-listele ile görebilirsin)")
    @app_commands.autocomplete(etiket=_kaynak_autocomplete)
    async def sheet_sil(self, interaction: discord.Interaction, etiket: str):
        source = storage.get_sheet_source_by_label(
            str(interaction.guild_id), str(interaction.user.id), etiket
        )
        if source is None:
            await interaction.response.send_message(
                f"'{etiket}' etiketli bir sheet'in yok.", ephemeral=True
            )
            return

        ok = storage.delete_sheet_source(source["id"], str(interaction.user.id))
        if ok:
            notif_cog = self.bot.get_cog("Notifications")
            if notif_cog:
                notif_cog.stop_source_loop(source["id"])
            await interaction.response.send_message(
                f"🗑️ '{etiket}' sheet'in silindi (ilişkili bildirim abonelikleri de temizlendi).",
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                "Böyle bir sheet bulunamadı (ya da sana ait değil).", ephemeral=True
            )

    @app_commands.command(name="rapor", description="Satış pipeline'ının anlık özetini gönder.")
    async def rapor(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        gsettings = storage.get_guild_settings(str(interaction.guild_id))
        try:
            rows = sheets_client.fetch_rows(
                spreadsheet_id=gsettings.get("spreadsheet_id"),
                worksheet_name=gsettings.get("worksheet_name"),
            )
        except Exception as e:
            await interaction.followup.send(f"Tablo okunamadı: {e}", ephemeral=True)
            return

        devam = [r for r in rows.values() if r[config.COL_FIRSAT_DURUMU].lower() == "devam ediyor"]
        kaybedildi = [r for r in rows.values() if r[config.COL_FIRSAT_DURUMU].lower() == "kaybedildi"]

        embed = discord.Embed(title="📊 Satış Pipeline Özeti", color=discord.Color.blurple())
        embed.add_field(name="Devam Eden Fırsatlar", value=str(len(devam)), inline=True)
        embed.add_field(name="Kaybedilen Fırsatlar", value=str(len(kaybedildi)), inline=True)
        embed.add_field(name="Toplam Kayıt", value=str(len(rows)), inline=True)
        if devam:
            en_eski = sorted(devam, key=lambda r: r[config.COL_SON_GUNCELLEME])[:5]
            ozet = "\n".join(f"• {r[config.COL_FIRMA]} — {r[config.COL_SON_GUNCELLEME]}" for r in en_eski)
            embed.add_field(name="En eski güncellenenler (ilk 5)", value=ozet, inline=False)

        await interaction.followup.send(embed=embed, ephemeral=True)

    # ---------------- Yönetici komutları ----------------

    admin_group = app_commands.Group(name="ayar", description="Sunucu genelindeki bildirim ayarları (yönetici)")

    @admin_group.command(name="kanal", description="Sahipsiz bildirimlerin düşeceği varsayılan kanalı ayarla.")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def ayar_kanal(self, interaction: discord.Interaction, kanal: discord.TextChannel):
        storage.set_default_channel(str(interaction.guild_id), str(kanal.id))
        await interaction.response.send_message(f"✅ Varsayılan bildirim kanalı {kanal.mention} olarak ayarlandı.")

    @admin_group.command(name="siklik", description="Tablonun kaç dakikada bir kontrol edileceğini ayarla.")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def ayar_siklik(self, interaction: discord.Interaction, dakika: app_commands.Range[int, 1, 1440]):
        storage.set_poll_minutes(str(interaction.guild_id), dakika)
        notif_cog = self.bot.get_cog("Notifications")
        if notif_cog:
            notif_cog.restart_guild_loop_with_new_interval(interaction.guild_id, dakika)
        await interaction.response.send_message(f"✅ Kontrol sıklığı {dakika} dakika olarak ayarlandı.")

    @admin_group.command(name="eskime-esigi", description="Kaç gün güncellenmeyen fırsat 'eski' sayılsın?")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def ayar_eskime(self, interaction: discord.Interaction, gun: app_commands.Range[int, 1, 365]):
        storage.set_stale_days(str(interaction.guild_id), gun)
        await interaction.response.send_message(f"✅ Eskime eşiği {gun} gün olarak ayarlandı.")

    @admin_group.command(name="olay-kanal", description="Belirli bir olay türü için sunucu geneli varsayılan kanal ata.")
    @app_commands.describe(
        tur="Hangi olay türü bu kanala düşsün?",
        kanal="Bu olay türü için hedef kanal",
    )
    @app_commands.choices(tur=EVENT_CHOICES)
    @app_commands.checks.has_permissions(manage_guild=True)
    async def ayar_olay_kanal(
        self,
        interaction: discord.Interaction,
        tur: app_commands.Choice[str],
        kanal: discord.TextChannel,
    ):
        storage.set_event_channel(str(interaction.guild_id), tur.value, str(kanal.id))
        await interaction.response.send_message(
            f"✅ **{tur.name}** olayları (kişisel aboneliği olmayanlar için) artık {kanal.mention} kanalına düşecek."
        )

    @admin_group.command(name="sheet", description="Hangi Google Sheet / sekmenin izleneceğini değiştir.")
    @app_commands.describe(
        spreadsheet_id="Sheet URL'sindeki /d/ ile /edit arasındaki kısım",
        sekme_adi="Sekme (worksheet) adı, örn. Sales Pipeline",
    )
    @app_commands.checks.has_permissions(manage_guild=True)
    async def ayar_sheet(self, interaction: discord.Interaction, spreadsheet_id: str, sekme_adi: str):
        storage.set_sheet_source(str(interaction.guild_id), spreadsheet_id, sekme_adi)
        await interaction.response.send_message(
            f"✅ İzlenen kaynak güncellendi: sheet `{spreadsheet_id}`, sekme `{sekme_adi}`.\n"
            f"Herhangi bir dosya düzenlemene veya botu yeniden başlatmana gerek yok, "
            f"bir sonraki kontrolde bu ayar kullanılacak."
        )


async def setup(bot: commands.Bot):
    # Not: `admin_group` bir app_commands.Group olarak sınıf özniteliği olduğundan
    # discord.py, add_cog çağrısı sırasında onu otomatik olarak komut ağacına ekler.
    # Burada tekrar bot.tree.add_command çağırmak "zaten kayıtlı" hatasına yol açar.
    await bot.add_cog(Settings(bot))
