import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
import asyncio
from gtts import gTTS
from psycopg2.extras import DictCursor

from discordbot import MyBot
from cogs.maincog import MainView
from my_ui import SettingView
from modules import FFmpegPCMAudio, create_text

from io import BytesIO
import os
import datetime
import traceback
import logging
import logging.handlers

logger = logging.getLogger(__name__)

if os.path.exists("../.env"):
    load_dotenv(verbose=True)
    load_dotenv("../.env")

# 初期化を行う時間を設定
schedule_time = datetime.time(hour=5, tzinfo=datetime.timezone(datetime.timedelta(hours=9)))


class EventCog(commands.Cog):
    def __init__(self, bot: MyBot):
        self.bot = bot
        self.voice_state_message = ""
        self.voice_client_dict: dict[int : discord.voice_client] = {}
        self.word_dict = {}
        self.initialize_by_day.start()

    @commands.Cog.listener()
    async def on_ready(self):
        """
        Botの準備完了時に呼び出されるイベント
        """
        logger.info(f"Logged in as {self.bot.user.name}")

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        first_channel = guild.text_channels[0]
        await first_channel.send("こんにちは！こちら、おいもbotです。\n[マニュアル](https://github.com/shichiseki/oimo-bot-release)を必ずお読みください。\n\nこのbotはボイスチャンネルのログおよびチーム決めボタンを自動的に送信します。\n以下のボタンから送信先を設定してください。", view=SettingView(self.bot, guild), embed=SettingView.SETTINGVIEW_INIT_EMBED)

    @tasks.loop(time=schedule_time)
    async def initialize_by_day(self):
        self.bot.main_view_message_id_dic.clear()
        logger.info("Complete daily task")

    async def text_to_speech(self, message: discord.Message):
        # messageが空でないとき
        if message.clean_content:
            logger.info(message.clean_content)
            # メッセージ加工
            text = create_text(message, word_dic=self.word_dict)

            # 音声生成
            mp3_fp = BytesIO()
            tts1 = gTTS(text=text, lang="ja")
            tts1.write_to_fp(mp3_fp)
            mp3_fp.seek(0)

            # discordで再生できる形式に変換
            source = FFmpegPCMAudio(mp3_fp.read(), pipe=True)
            try:
                # 音声再生
                message.guild.voice_client.play(source)

            except Exception:
                logger.error(traceback.format_exc())

                # エラーメッセージ送信
                if message.guild.id in self.bot.guild_config_dic:
                    log_ch_id = self.bot.guild_config_dic[message.guild.id]["log_ch_id"]
                    log_ch = self.bot.get_channel(log_ch_id)

                    emb = discord.Embed(title="音声再生エラー", description="音声が再生できませんでした")
                    emb.add_field(name="再生できなかったメッセージ", value=message.clean_content)
                    await log_ch.send(embed=emb)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # ephemeralがTrueのときNoneになる
        if message.guild is not None:
            # ボイスに接続されているとき
            if message.guild.voice_client is not None:
                if message.guild.voice_client.is_connected():
                    try:
                        # 他の音声を再生中なら待つ
                        while message.guild.voice_client.is_playing():
                            await asyncio.sleep(0.1)

                        # 音声再生
                        await self.text_to_speech(message)

                    except Exception:
                        logger.error(traceback.format_exc())

    async def enter_member(self, member: discord.Member):
        message = f"{member.display_name}さんが入室しました。"

        # botがボイスチャンネルに接続していないとき
        if member.guild.voice_client is None:
            # ボイスチャンネル接続
            await member.voice.channel.connect(timeout=3)
            # 今までmain_viewを送信していない場合
            if member.guild.id not in self.bot.main_view_message_id_dic:
                # 送信先が設定されているとき
                if member.guild.id in self.bot.guild_config_dic:
                    # main_view送信先取得
                    main_ch_id = self.bot.guild_config_dic[member.guild.id]["main_ch_id"]
                    main_ch = self.bot.get_channel(main_ch_id)

                    # main_view送信
                    main_view_message = await main_ch.send(content="ボタンを表示するよ！", view=MainView(self.bot))
                    self.bot.main_view_message_id_dic[member.guild.id] = main_view_message

        return message

    async def leaving_member(self, member: discord.Member):
        message = f"{member.display_name}さんが退室しました。"

        # voice取得
        voice_client = member.guild.voice_client

        # ボイスチャンネルにいるmemberの数
        member_num = 0
        # ギルド内のすべてのボイスチャンネルのmemberの数を数える
        for voice_ch in member.guild.voice_channels:
            member_num += len([None for member in voice_ch.members if not member.bot])

        # ボイスチャンネルに誰もいなければ切断
        if member_num == 0:
            voice_client.stop()
            await voice_client.disconnect(force=True)
            voice_client.cleanup()

        return message

    async def auto_voice_client_move(self, member: discord.Member):
        # voice取得
        voice_client = member.guild.voice_client

        if voice_client is not None:
            # bot以外のメンバー人数を計算
            member_cnt = len([None for ch_member in voice_client.channel.members if not ch_member.bot])
            # メンバーがいなかったら
            if member_cnt == 0:
                for v_channel in member.guild.voice_channels:
                    # bot以外の人数が1以上いるチャンネルに移動
                    if len([1 for member in v_channel.members if not member.bot]) > 0:
                        # 音声停止
                        voice_client.stop()
                        await voice_client.move_to(v_channel)
                        break

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        """音声状態が変更された際に呼び出される抽象メソッド"""
        # ボット以外
        if not member.bot:
            # 入退室したとき
            if bool(before.channel) ^ bool(after.channel):
                if member.guild.id not in self.bot.guild_config_dic:
                    # ボタンとログ送信先取得
                    try:
                        # DB処理
                        with self.bot.db_connector:
                            with self.bot.db_connector.cursor(cursor_factory=DictCursor) as cursor:
                                sql = f"SELECT log_ch_id, main_ch_id FROM config_by_guild WHERE guild_id = '{member.guild.id}'"
                                cursor.execute(sql)
                                row = cursor.fetchone()

                                # 存在すれば取得
                                if row is not None:
                                    self.bot.guild_config_dic[member.guild.id] = {key: int(value) for key, value in dict(row).items()}

                    except Exception:
                        logger.error(traceback.format_exc())

                # 入室処理
                if before.channel is None:
                    message = await self.enter_member(member)

                # 退室処理
                if after.channel is None:
                    message = await self.leaving_member(member)

                # 送信先が設定されていればログ送信
                if member.guild.id in self.bot.guild_config_dic:
                    # ログチャンネル取得
                    log_ch_id = self.bot.guild_config_dic[member.guild.id]["log_ch_id"]
                    log_ch = self.bot.get_channel(log_ch_id)

                    # ログ送信
                    await log_ch.send(content=message)

            # 人がいなくなったら自動的にvoice_clientを移動または切断する
            await self.auto_voice_client_move(member)


async def setup(bot):
    await bot.add_cog(EventCog(bot))
