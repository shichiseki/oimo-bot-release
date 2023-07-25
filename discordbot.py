import os
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv
import psycopg2

if os.path.exists("./.env"):
    load_dotenv(verbose=True)
    load_dotenv("./.env")

# 読み込むコグの名前
COGS = ["cogs.maincog", "cogs.eventcog"]


# クラスの定義。ClientのサブクラスであるBotクラスを継承。
class MyBot(commands.Bot):
    # MyBotのコンストラクタ。
    def __init__(self, command_prefix, intents: discord.Intents, debug_mode=False):
        self.debug_mode = debug_mode
        self.db_connector = psycopg2.connect(os.environ["DATABASE_URL"])
        self.guild_config_dic = {}
        self.main_view_message_id_dic = {}

        intents.members = True
        intents.message_content = True
        intents.guilds = True

        if debug_mode:
            super().__init__(command_prefix, intents=intents, application_id=int(os.environ["DEBUG_BOT_ID"]))

        else:
            super().__init__(command_prefix, intents=intents, application_id=int(os.environ["OIMO_BOT_ID"]))

    async def setup_hook(self) -> None:
        await self.tree.sync()


async def main():
    debug_mode = False

    bot = MyBot(command_prefix="?", intents=discord.Intents.default(), debug_mode=debug_mode)

    for cog in COGS:
        await bot.load_extension(cog)

    if debug_mode:
        await bot.start(token=os.environ["DEBUG_BOT_TOKEN"])
    else:
        await bot.start(token=os.environ["OIMO_BOT_TOKEN"])


if __name__ == "__main__":
    discord.utils.setup_logging()
    asyncio.run(main())
