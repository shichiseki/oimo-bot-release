from oimo_bot_release import COGS, MyBot
from my_ui import MainView
import discord
from discord.ext import commands
from discord import app_commands
import sys
import os
from dotenv import load_dotenv
from importlib import reload


import logging
import logging.handlers

sys.path.append("../")

load_dotenv(verbose=True)
load_dotenv("../.env")

logger = logging.getLogger(__name__)


def reload_modules():
    import my_ui
    import modules

    reload(my_ui)
    reload(modules)


# コグとして用いるクラスを定義。
class TestCog(commands.Cog):
    # TestCogクラスのコンストラクタ。Botを受取り、インスタンス変数として保持。
    def __init__(self, bot: MyBot):
        self.bot = bot

    @app_commands.command(name="reload_cog", description="cogをリロードします")
    @app_commands.guilds(discord.Object(id=int(os.environ["SHICHI_GUILD_ID"])))  # debug
    async def reload_cog(self, interaction: discord.Interaction):
        message = ""
        for cog in COGS:
            message += f"{cog}\n"
            await self.bot.reload_extension(name=cog)

        reload_modules()

        await interaction.response.send_message(f"{message}\ncog loaded")

    @app_commands.command(name="test-command", description="テスト")
    @app_commands.guilds(discord.Object(id=int(os.environ["SHICHI_GUILD_ID"])))  # debug
    async def test(self, interaction: discord.Interaction):
        await interaction.response.send_message("こんにちは！こちら、おいもbotです。\n[マニュアル](https://github.com/shichiseki/oimo-bot-release)を必ずお読みください。\n\nこのbotはボイスチャンネルのログおよびチーム決めボタンを自動的に送信します。\n以下のボタンから送信先を設定してください。")

    @app_commands.checks.cooldown(1, 60 * 5, key=lambda i: i.guild_id)
    @app_commands.command(name="decide-team", description="チーム決めviewを送信します。")
    async def send_main_view(self, interaction: discord.Interaction):
        await interaction.response.send_message(view=MainView(self.bot))

    @send_main_view.error
    async def on_test_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(str(error), ephemeral=True)


async def setup(bot: MyBot):
    await bot.add_cog(TestCog(bot))
