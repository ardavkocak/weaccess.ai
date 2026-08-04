import asyncio
import logging

import discord
from discord.ext import commands

import config
import storage

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("satis-bot")

INTENTS = discord.Intents.default()
# DM gönderebilmek ve guild üyelerini çözebilmek için:
INTENTS.members = True

EXTENSIONS = [
    "cogs.notifications",
    "cogs.settings",
]


class SatisBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=INTENTS)

    async def setup_hook(self):
        storage.init_db()
        for ext in EXTENSIONS:
            await self.load_extension(ext)

        if config.TEST_GUILD_ID:
            guild = discord.Object(id=int(config.TEST_GUILD_ID))
            self.tree.copy_global_to(guild=guild)
            synced = await self.tree.sync(guild=guild)
            log.info(f"{len(synced)} slash komutu TEST sunucusuna (anında) senkronize edildi.")
        else:
            synced = await self.tree.sync()
            log.info(f"{len(synced)} slash komutu global olarak senkronize edildi "
                     f"(tüm sunucularda görünmesi biraz zaman alabilir).")

    async def on_ready(self):
        log.info(f"Giriş yapıldı: {self.user} (id={self.user.id})")


async def main():
    if not config.DISCORD_TOKEN:
        raise SystemExit("DISCORD_TOKEN tanımlı değil (.env dosyasını kontrol et).")
    if not config.SPREADSHEET_ID:
        log.warning(
            "SPREADSHEET_ID tanımlı değil. Bot yine de açılacak (Discord bağlantısı ve "
            "slash komutları test edilebilir) ama /rapor ve tablo kontrolleri hata verecektir."
        )

    bot = SatisBot()
    async with bot:
        await bot.start(config.DISCORD_TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
