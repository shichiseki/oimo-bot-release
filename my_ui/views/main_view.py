import discord
from discord.ext import commands

from typing import Optional
from decimal import Decimal, ROUND_HALF_UP
import logging
import logging.handlers
import random
from collections import deque
import sys
import os
import traceback

from my_ui import Dropdown, DeleteButton
from discordbot import MyBot

import asyncpg

logger = logging.getLogger(__name__)

# 再帰回数制限設定
sys.setrecursionlimit(300000)


def judge_rate(rate: int):
    """レート（数字）からレート（記号）に変更する関数"""

    if rate >= 2700:
        rating = "S-"
    elif rate >= 2400:
        rating = "A+"
    elif rate >= 2100:
        rating = "A"
    elif rate >= 1950:
        rating = "A-"
    else:
        rating = "A-未満"

    return rating


def list_subtraction(subtrahend_list, minuend_list):
    return list(set(subtrahend_list) - set(minuend_list))

    # result_list = []
    # result_dict = {}
    # subtrahend_dict = Counter(subtrahend_list)
    # minuend_dict = Counter(minuend_list)

    # for ele in subtrahend_list:
    #     result_dict[ele] = subtrahend_dict[ele] - minuend_dict[ele]

    # for key, value in result_dict.items():
    #     for i in range(value):
    #         result_list.append(key)

    # return result_list


def rec(r_dp, a, i, j, route, ans):
    if i == 0:
        if j == 0:
            ans.append(list(route))

        return ans

    if r_dp[i - 1][j] != float("inf"):
        rec(r_dp, a, i - 1, j, route, ans)

    if j - a[i - 1] >= 0 and r_dp[i - 1][j - a[i - 1]] != float("inf"):
        route.append(a[i - 1])
        rec(r_dp, a, i - 1, j - a[i - 1], route, ans)
        route.popleft()


def Partial_sum_dp(N, total_sum, target_list):
    dp = [[float("inf") for _ in range(total_sum + 1)] for _ in range(N + 1)]
    dp[0][0] = 0

    for i in range(N):
        for j in range(total_sum):
            dp[i + 1][j] = min(dp[i + 1][j], dp[i][j])
            if j >= target_list[i]:
                dp[i + 1][j] = min(dp[i + 1][j], dp[i][j - target_list[i]] + 1)

    return dp


def team_divider(rates: dict, number_of_teams: int):
    """DPを用いたレートの平均の差が最小になるようなチームを決定する関数"""
    N = len(rates)

    rate_list = list(rates.values())

    rate_all_sum = sum(rate_list)

    target_rate_list = rate_list.copy()

    rate_member_dict = {}
    member_rate_dict = {}

    for member, rate in rates.items():
        rate_member_dict.setdefault(rate, []).append(member)
        member_rate_dict[member] = rate

    member_num = N // number_of_teams
    member_mod = N % number_of_teams

    divide_member_result: list[list[discord.Member]] = []
    divide_rate_result: list[list[int]] = []

    route = deque()
    ans = []
    cnt = 0
    M = len(target_rate_list)
    mod = 1 if member_mod > 0 else 0

    dp = Partial_sum_dp(N, rate_all_sum, target_rate_list)

    while len(divide_rate_result) < number_of_teams:
        rate_sum = sum(target_rate_list)
        rec(dp, target_rate_list, M, rate_sum // M * (member_num + mod) + cnt, route, ans)

        if ans:
            divide_rate_result.append(ans[0])
            M -= len(ans[0])
            target_rate_list = list_subtraction(target_rate_list, [rate for rate in ans[0]])

            team = []
            for rate in ans[0]:
                team.append(rate_member_dict[rate].pop())

            divide_member_result.append(team)

            dp = Partial_sum_dp(M, rate_sum, target_rate_list)

            route = deque()
            ans = []
            cnt = 0

            member_mod -= 1
            member_mod = max(member_mod, 0)
            if member_mod == 0:
                mod = 0

        else:
            cnt = cnt + 1

    return divide_member_result, divide_rate_result


def random_group_divider(input_list, divide_num):
    result_list = []
    q, mod = divmod(len(input_list), divide_num)
    if q < 1:
        return None

    else:
        for i in range(divide_num):
            if i < mod:
                sample_list = random.sample(input_list, q + 1)

            else:
                sample_list = random.sample(input_list, q)

            result_list.append(sample_list)
            input_list = list_subtraction(input_list, sample_list)

        return result_list


async def get_valid_members(interaction: discord.Interaction):
    """インタラクションしたユーザーのボイスチャンネルにいるmemberのリストを返す関数
    (ボットおよびミュートのmemberは除く)
    """
    author_voice_channel = interaction.user.voice.channel.name
    voice_chat_members: list[discord.Member] = []
    if author_voice_channel is not None:
        async for member in interaction.user.guild.fetch_members(limit=150):
            # ボイスチャンネルに入っているひと
            if member.voice:
                # インタラクションした人と同じチャンネルにいるかつミュートしていない人
                if author_voice_channel == member.voice.channel.name and (not member.voice.self_mute) and (not member.bot):
                    voice_chat_members.append(member)

    return voice_chat_members


def change_item_disabled(children: list, custom_id: str, disabled: bool):
    for child in children:
        if child.custom_id == custom_id:
            child.disabled = disabled


class MainView(discord.ui.View):
    def __init__(self, bot: MyBot):
        super().__init__(timeout=None)
        self.bot: MyBot = bot
        self.decide_team_view = None

    @discord.ui.button(label="チーム決め", style=discord.ButtonStyle.blurple, custom_id="MainView:DecideTeam")
    async def send_decide_team_view(self, interaction: discord.Interaction, button: discord.ui.Button):
        # チーム決めメッセージを送信
        self.decide_team_view = DecideTeamView()

        # ボタン無効化
        button.disabled = True
        await interaction.response.edit_message(view=self)

        # view送信
        await interaction.followup.send(embed=DecideTeamView.RATE_REGISTER_INIT_EMBED, view=self.decide_team_view)

    @discord.ui.button(label="設定", style=discord.ButtonStyle.blurple, custom_id="MainView:Settings")
    async def setting(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await interaction.response.send_message(view=SettingView(bot=self.bot, guild=interaction.guild), embed=SettingView.SETTINGVIEW_INIT_EMBED, ephemeral=True)

        except Exception as e:
            logger.error(f"failed sending setting view: {e}")

        else:
            button.disabled = True
            await interaction.message.edit(view=self)


class DecideTeamView(discord.ui.View):
    """レート登録メッセージ内View"""

    # レート登録初期メッセージのEmbed
    RATE_REGISTER_INIT_EMBED = discord.Embed(title="チーム決め", description="", colour=discord.Colour.blue())
    RATE_REGISTER_INIT_EMBED.add_field(name="「登録」", value="レーティングを登録するウインドウを開きます。\nすでに登録している場合は再登録できます。", inline=False)
    RATE_REGISTER_INIT_EMBED.add_field(name="「チーム分け」", value="チーム分けを行うメッセージを送信します。\nレートに基づいたチーム分けを行うには\n「登録」ボタンから事前にレートの登録が必要です。", inline=False)

    def __init__(self, timeout: Optional[float] = None):
        super().__init__(timeout=timeout)
        self.rates = {}
        self.modals = {}

    @discord.ui.button(label="登録", style=discord.ButtonStyle.primary, custom_id="DecideTeamView:register")
    async def register(self, interaction: discord.Interaction, button: discord.ui.Button):
        """登録ボタン押下時関数"""

        # Modalインスタンスをユーザーごとに保持
        self.modals[interaction.user.id] = RateRegisterModal(self.rates)

        # Modal送信
        await interaction.response.send_modal(self.modals[interaction.user.id])

    @discord.ui.button(label="チーム分け", style=discord.ButtonStyle.blurple, custom_id="MainView:team_divide")
    async def team_divide(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.team_decide_dropdown_view = TeamDivideDropdownView(self.rates)
        await interaction.response.send_message("チーム数とチーム分けの方法を選んでください", embed=TeamDivideDropdownView.TEAM_DIVIDE_INIT_EMBED, view=self.team_decide_dropdown_view)


class RateRegisterModal(discord.ui.Modal, title="レーティング登録"):
    """レーティングを登録する際のModal"""

    # テキスト
    rate_input = discord.ui.TextInput(
        label="レートを半角数字4桁で入力してください",
        style=discord.TextStyle.short,
        placeholder="例: 2650",
        required=True,
        max_length=4,
    )

    def __init__(self, rates: dict[discord.User, int]):
        super().__init__()
        self.rates = rates

    async def on_submit(self, interaction: discord.Interaction):
        # 入力されたレートを判定
        try:
            rate_value = int(self.rate_input.value)

            if not 1450 <= rate_value <= 2999:
                raise Exception("rate out of range")

        except Exception as e:
            logger.error(e, exc_info=True)
            await interaction.response.send_message(content=f"不正なレートです！\n1450 〜 2999の数字を入力してください！\nあなたの入力: {self.rate_input.value}", ephemeral=True)
            return

        # 再登録時処理
        if interaction.user in self.rates:
            register_comp_message = f"レーティング{rate_value}で再登録完了したよ!"

        # 通常登録処理
        else:
            register_comp_message = f"レーティング{rate_value}で登録完了したよ!"

        self.rates[interaction.user] = rate_value

        # レート登録者、未登録者リスト
        register_name_list = [user.display_name for user in self.rates.keys()]
        not_register_name_list = [member.display_name for member in interaction.user.guild.voice_channels[0].members if not member.bot and member not in self.rates.keys()]

        # プログレスバー
        register_ratio = len(register_name_list) / (len(not_register_name_list) + len(register_name_list))
        register_ratio_10 = int(10 * register_ratio)
        progress_bar = "".join(["■"] * register_ratio_10 + ["□"] * (10 - register_ratio_10))

        # embed定義
        embed = discord.Embed(title=f"レート登録状況\n {register_ratio:.0%}\n{progress_bar}", description="", colour=discord.Colour.green())
        embed.add_field(name=f"登録者 {len(register_name_list)}人", value="\n".join(register_name_list))

        # 未登録者field
        if not_register_name_list:
            embed.add_field(name="未登録者", value="\n".join(not_register_name_list))

        else:
            embed.add_field(name="未登録者", value="なし")

        # 登録状況表示
        await interaction.response.edit_message(embeds=[DecideTeamView.RATE_REGISTER_INIT_EMBED, embed])

        # 登録内容送信
        await interaction.followup.send(content=register_comp_message, ephemeral=True)

        logger.info(f"{interaction.user.display_name} register rate value {rate_value}")

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        embed = discord.Embed(title="エラー", description="エラーが発生しました。", colour=discord.Colour.red())
        embed.add_field(name="エラー内容", value=error)
        await interaction.channel.send(embed=embed)


# チーム分けを行うView
class TeamDivideDropdownView(discord.ui.View):
    TEAM_DIVIDE_INIT_EMBED = discord.Embed(title="チーム決め", description="", colour=discord.Colour.blue())
    TEAM_DIVIDE_INIT_EMBED.add_field(name="チーム分けの方法", value="「ランダム」ではレーティング登録は必要ありません。", inline=False)
    TEAM_DIVIDE_INIT_EMBED.add_field(name="ボイスチャット移動", value="決定されたチームにボイスチャットを移動させます", inline=False)
    TEAM_NAME = ["A", "B", "C", "D", "E"]

    def __init__(self, rates: dict):
        super().__init__(timeout=None)
        self.divided_team_list = []
        self.rates = rates

        self.add_item(DeleteButton("チーム決めメッセージ", row=2))

        # チーム数選択用ドロップダウンメニュー
        self.TEAM_NUM_DEFAULT = "2"
        team_num_dropdown_options = [
            discord.SelectOption(label=f"{self.TEAM_NUM_DEFAULT}チーム", value=self.TEAM_NUM_DEFAULT, description="レーティングを登録した人達を2チームに分けます", emoji="2️⃣", default=True),
            discord.SelectOption(label="3チーム", value="3", description="レーティングを登録した人達を3チームに分けます", emoji="3️⃣"),
        ]

        # チーム分けの方法選択用ドロップダウンメニュー
        self.METHOD_DEFAULT = "レーティング平均"
        divide_method_dropdown_options = [
            discord.SelectOption(
                label=self.METHOD_DEFAULT,
                description="各チームのレーティングの平均が同じになるようにチームを分けます(要レーティング登録)",
                emoji="⚖",
                default=True,
            ),
            discord.SelectOption(label="レーティング上下", description="レーティングが高いほうからチームを分けます(要レーティング登録)", emoji="📶"),
            discord.SelectOption(label="ランダム", description="レーティング関係なくボイスチャンネルにいる人をランダムにチームを分けます", emoji="❓"),
        ]

        # Dropdown配置
        self.team_num_dropdown = Dropdown(team_num_dropdown_options, row=0)
        self.divide_method_dropdown = Dropdown(divide_method_dropdown_options, row=1)

        setattr(self.team_num_dropdown, "_values", [self.TEAM_NUM_DEFAULT])
        setattr(self.divide_method_dropdown, "_values", [self.METHOD_DEFAULT])

        self.add_item(self.team_num_dropdown)
        self.add_item(self.divide_method_dropdown)

    def rate_average_divide(self, embed: discord.Embed, team_num: int):
        """レートの平均差が最も小さいチームに分ける処理"""
        embed.title = "チーム分け結果 (レート平均)"
        self.divided_team_list.clear()
        divided_member_list, divided_rate_list = team_divider(self.rates, team_num)
        self.divided_team_list = divided_member_list

        # 各チームの平均レーティング計算
        for i in range(team_num):
            team_rating = int(Decimal(float(sum(divided_rate_list[i]) / len(divided_rate_list[i]))).quantize(Decimal("0"), rounding=ROUND_HALF_UP))
            team_members = [member.display_name for member in divided_member_list[i]]
            embed.add_field(name=f"チーム{self.TEAM_NAME[i]}【平均レート： {judge_rate(team_rating)} ({team_rating})】", value="\n".join(team_members), inline=False)

        return embed

    def rate_rank_divide(self, embed: discord.Embed, team_num: int):
        """レートの高い人から順にチームを分ける処理"""
        embed.title = "チーム分け結果 (レート上下)"
        member_rate_list = sorted(self.rates.items(), key=lambda x: x[1])
        q, mod = divmod(len(self.rates), team_num)
        self.divided_team_list.clear()

        cnt = 0

        for i in range(0, len(member_rate_list), q):
            div_list = member_rate_list[i : i + q]

            if i + q > len(member_rate_list):
                break

            if cnt < mod:
                div_list.append(member_rate_list.pop(i + q))

            cnt += 1

            div_member_list = [member for member, rate in div_list]

            team_rating = int(Decimal(float(sum([rate for member, rate in div_list]) / len([rate for member, rate in div_list]))).quantize(Decimal("0"), rounding=ROUND_HALF_UP))
            team_members = [member.display_name for member in div_member_list]
            embed.add_field(name=f"チーム{self.TEAM_NAME[i // q]}【平均レート： {judge_rate(team_rating)} ({team_rating})】", value="\n".join(team_members), inline=False)

            self.divided_team_list.append(div_member_list)

        return embed

    def random_divide(self, embed: discord.Embed, voice_chat_members: list[discord.Member], team_num: int):
        self.divided_team_list = random_group_divider(voice_chat_members, team_num)

        embed.title = "チーム分け結果 (ランダム)"
        for i in range(team_num):
            team_members = [member.display_name for member in self.divided_team_list[i]]
            embed.add_field(name=f"チーム{self.TEAM_NAME[i]}", value="\n".join(team_members), inline=False)

        return embed

    def default_option(self, team_num, divide_method):
        for option in self.team_num_dropdown.options:
            if option.label == f"{team_num}チーム":
                option.default = True

            else:
                option.default = False

        for option in self.divide_method_dropdown.options:
            if option.label == divide_method:
                option.default = True

            else:
                option.default = False

    # 決定ボタン
    @discord.ui.button(label="決定", style=discord.ButtonStyle.green, custom_id="Dropdown:decide", row=2)
    async def decide(self, interaction: discord.Interaction, button: discord.ui.Button):
        # チーム数とチーム決め方法を取得
        team_num = int(self.team_num_dropdown.values[0])
        divide_method = self.divide_method_dropdown.values[0]

        # 埋め込みメッセージ生成
        embed = discord.Embed(title="", colour=discord.Colour.orange())

        # レートに関するメソッド
        if divide_method.startswith("レーティング"):
            if len(self.rates) >= team_num:
                if divide_method == "レーティング平均":
                    embed = self.rate_average_divide(embed, team_num)

                if divide_method == "レーティング上下":
                    embed = self.rate_rank_divide(embed, team_num)

                # ボイスチャット移動ボタン有効化
                change_item_disabled(self.children, custom_id="TeamDivideDropdownView:move_voice_channel", disabled=False)

            # 登録人数が足りないとき
            else:
                team_divide_desc = "レート登録人数が足りません！\n"
                team_divide_desc += f"レーティング登録人数: {len(self.rates)}人\n"
                embed = discord.Embed(title="エラー", description=team_divide_desc, colour=discord.Colour.red())

                # ボイスチャット移動ボタン無効化
                change_item_disabled(self.children, custom_id="TeamDivideDropdownView:move_voice_channel", disabled=True)

        # ランダム
        if divide_method == "ランダム":
            # ボタンを押した人がボイスチャンネルにいれば
            if interaction.user.voice:
                # ボイスチャンネルにいるメンバーを取得
                voice_chat_members = await get_valid_members(interaction)

            else:
                await interaction.response.send_message("ボイスチャンネルに参加した状態でボタンをクリックしてください。", ephemeral=True)
                return

            # ボイスチャンネル内に人がいれば
            if len(voice_chat_members) >= team_num:
                embed = self.random_divide(embed, voice_chat_members, team_num)
                # ボイスチャット移動ボタン有効化
                change_item_disabled(self.children, custom_id="TeamDivideDropdownView:move_voice_channel", disabled=False)

            else:
                team_divide_desc = "ボイスチャンネルに参加している人数が少なすぎます。\n"
                team_divide_desc += f"ボイスチャンネル参加人数(ミュートを除く): {len(voice_chat_members)}人\n"
                embed = discord.Embed(title="エラー", description=team_divide_desc, colour=discord.Colour.red())

                # ボイスチャット移動ボタン無効化
                change_item_disabled(self.children, custom_id="TeamDivideDropdownView:move_voice_channel", disabled=True)

        # 現在の選択を保持する
        self.default_option(team_num, divide_method)

        await interaction.response.edit_message(view=self, embeds=[self.TEAM_DIVIDE_INIT_EMBED, embed])

    @discord.ui.button(label="ボイスチャット移動", style=discord.ButtonStyle.blurple, custom_id="TeamDivideDropdownView:move_voice_channel", row=3, disabled=True)
    async def move_voice_channel(self, interaction: discord.Interaction, button: discord.ui.Button):
        # 考え中メッセージ送信
        await interaction.response.defer(thinking=True)

        # メッセージが送られたギルド（サーバー）取得
        guild = interaction.user.guild
        # ボイスチャンネルの二番目以降を取得
        voice_channels = guild.voice_channels[1:]

        # チーム分け結果に基づいてメンバーを移動
        for i in range(len(self.divided_team_list)):
            for member in self.divided_team_list[i]:
                try:
                    await member.move_to(channel=voice_channels[i], reason="by move voice channel button")

                except Exception as e:
                    logger.error(e)

        # ボタン無効化
        button.disabled = True
        await interaction.message.edit(view=self)

        await interaction.followup.send("ボイスチャンネル移動を行いました！")


class SettingView(discord.ui.View):
    SETTINGVIEW_INIT_EMBED = discord.Embed(title="設定", description="", colour=discord.Colour.blue())
    SETTINGVIEW_INIT_EMBED.add_field(name="入退室ログ送信先", value="ボイスチャンネル入退室のログを送信するチャンネルを選択します。", inline=False)
    SETTINGVIEW_INIT_EMBED.add_field(name="チーム決めボタン送信先", value="チーム決めボタンを送信するチャンネルを選択します。", inline=False)

    def __init__(self, bot: MyBot, guild: discord.Guild):
        super().__init__(timeout=None)
        self.bot = bot
        self.cd_mapping = commands.CooldownMapping.from_cooldown(3, 60, commands.BucketType.guild)

        # テキストチャンネル選択肢リスト
        text_ch_options = [discord.SelectOption(label=txt_ch.name, value=txt_ch.id, emoji="#⃣") for txt_ch in guild.text_channels]

        # Dropdown
        self.voice_chat_log_ch_dropdown = Dropdown(text_ch_options, placeholder="入退室ログ送信先チャンネル", row=0)
        self.main_ch_dropdown = Dropdown(text_ch_options, placeholder="チーム決めボタン送信先チャンネル", row=1)

        # Dropdown配置
        self.add_item(self.voice_chat_log_ch_dropdown)
        self.add_item(self.main_ch_dropdown)

    async def upsert_txt_ch_id(self, guild_id: str, log_ch_id: str, main_ch_id: str):
        
        conn_pool = asyncpg.create_pool(os.environ["DATABASE_URL"])
                        
        async with conn_pool as pool:
            async with pool.acquire() as con:
                sql = """
                        INSERT INTO config_by_guild (guild_id, log_ch_id, main_ch_id)
                        VALUES ($1, $2, $3)
                        ON CONFLICT (guild_id)
                        DO UPDATE SET log_ch_id = $2 , main_ch_id = $3
                    """
                await con.execute(sql, guild_id, log_ch_id, main_ch_id)
        
        logger.info(f"UPSERT {guild_id} {log_ch_id} {main_ch_id}")

    @discord.ui.button(label="リスト更新", style=discord.ButtonStyle.blurple, custom_id="SettingView:UpdateList", row=2)
    async def update_ch_list(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            # テキストチャンネル選択肢リスト
            text_ch_options = [discord.SelectOption(label=txt_ch.name, value=txt_ch.id, emoji="#⃣") for txt_ch in interaction.guild.text_channels]
            self.voice_chat_log_ch_dropdown.options = text_ch_options
            self.main_ch_dropdown.options = text_ch_options

            await interaction.response.edit_message(view=self)

        except Exception as e:
            logger.error(e)
            await interaction.followup.send("チャンネルリスト更新に失敗しました。もう一度試してみてください。", ephemeral=True)

        else:
            await interaction.followup.send("チャンネルリストを更新しました。", ephemeral=True)

    @discord.ui.button(label="決定", style=discord.ButtonStyle.green, custom_id="SettingView:Decide", row=3)
    async def send_decide_team_view(self, interaction: discord.Interaction, button: discord.ui.Button):
        # ボタンcooldown処理
        bucket = self.cd_mapping.get_bucket(interaction.message)
        retry_after = bucket.update_rate_limit()
        if retry_after:
            return await interaction.response.send_message("このボタンは制限がかかっています。しばらくしてからもう一度押してください。", ephemeral=True)

        # チャンネルが選択されているとき
        if self.voice_chat_log_ch_dropdown.values and self.main_ch_dropdown.values:
            # 選択されたチャンネルidを取得
            log_ch_id = self.voice_chat_log_ch_dropdown.values[0]
            main_ch_id = self.main_ch_dropdown.values[0]

            # 存在しないチャンネルを選択しているとき
            if interaction.guild.get_channel(int(log_ch_id)) is None or interaction.guild.get_channel(int(main_ch_id)) is None:
                return await interaction.response.send_message("現在は存在しないチャンネルを選択しています！", ephemeral=True)

            try:
                # DB処理
                await self.upsert_txt_ch_id(str(interaction.guild_id), log_ch_id, main_ch_id)

                # botのギルド別辞書に格納
                self.bot.guild_config_dic[interaction.guild_id] = {"log_ch_id": int(log_ch_id), "main_ch_id": int(main_ch_id)}

            except Exception:
                logger.error(traceback.format_exc())
                await interaction.response.send_message("エラーが発生しました。\nもう一度決定ボタンを押して設定するか、しばらく待ってから設定を行ってください。", ephemeral=True)

            else:
                # 正常処理
                # 設定完了メッセージ送信
                setting_embed = discord.Embed(title="設定内容", description="", colour=discord.Colour.blue())
                setting_embed.add_field(name="入退室ログ送信先", value=f"# {interaction.guild.get_channel(int(log_ch_id)).name}", inline=False)
                setting_embed.add_field(name="チーム決めボタン送信先", value=f"# {interaction.guild.get_channel(int(main_ch_id)).name}", inline=False)
                await interaction.response.send_message("以下の内容で設定が完了しました。", embed=setting_embed)

                # 設定チャンネル取得
                log_ch = self.bot.get_channel(int(log_ch_id))
                main_ch = self.bot.get_channel(int(main_ch_id))

                # 確認メッセージ送信
                await log_ch.send(f"ボットログは今後{log_ch.mention}に送信されます。")
                await main_ch.send(f"チーム分けボタンは今後{main_ch.mention}に送信されます。")

        # チャンネル未選択時処理
        else:
            await interaction.response.send_message("チャンネルを選択してください。", ephemeral=True)
