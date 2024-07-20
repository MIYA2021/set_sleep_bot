import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime, timedelta
import pytz
import os
from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = os.getenv('GUILD_ID')
ADMIN_ROLE_ID = int(os.getenv('ADMIN_ROLE_ID'))

# Botの設定
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='/', intents=intents)

# データを保存するための辞書
sleep_timers = {}
user_sleep_times = {}

# 日本時間でのタイムゾーン設定
tokyo_tz = pytz.timezone('Asia/Tokyo')

@bot.event
async def on_ready():
    print(f'ログインしました: {bot.user.name}')
    guild = discord.Object(id=int(GUILD_ID))
    try:
        bot.tree.copy_global_to(guild=guild)
        await bot.tree.sync(guild=guild)
        print("コマンドをギルドに同期したよ。")
    except Exception as e:
        print(f"コマンドの同期中にエラーが発生したらしい...: {e}")

    check_sleeptimers.start()

@bot.tree.command(name='set_sleep', description='スリープタイマーを設定するよ。')
@app_commands.describe(time='スリープタイマーを設定する時間（HH:MM形式）', user='タイマーを設定する人')
async def set_sleep(interaction: discord.Interaction, time: str, user: discord.User = None):
    """/set_sleep [時間] コマンドでタイマーを設定できるよ。"""
    author_id = interaction.user.id
    if user is None:
        user = interaction.user

    # 管理者ロールのチェック
    has_admin_role = any(role.id == ADMIN_ROLE_ID for role in interaction.user.roles)
    if not has_admin_role and user.id != author_id:
        await interaction.response.send_message('他のユーザーにスリープタイマーを設定するには管理者ロールが必要だよ。')
        return

    if user.id in sleep_timers:
        await interaction.response.send_message(f'{user.name}さんにはすでにスリープタイマーが設定されてるみたいだよ。/not_set_time コマンドでキャンセルできるよ!!。')
        return
    
    try:
        sleep_datetime = datetime.strptime(time, '%H:%M')
        now = datetime.now(tokyo_tz)
        sleep_datetime = tokyo_tz.localize(datetime.combine(now.date(), sleep_datetime.time()))

        if sleep_datetime < now:
            sleep_datetime += timedelta(days=1)  # 次の日に設定

        sleep_timers[user.id] = (interaction.channel.id, sleep_datetime)
        user_sleep_times[user.id] = sleep_datetime
        await interaction.response.send_message(f'{user.name}さんのスリープタイマーが {sleep_datetime.strftime("%H:%M:%S")} 日本時間に設定したよ!!')

    except ValueError:
        await interaction.response.send_message('無効な時間形式だよ。HH:MM形式で入力して欲しいな!!')

@bot.tree.command(name='good_morning', description='おはよ起きたよ（ミュート解除）')
async def good_morning(interaction: discord.Interaction):
    user_id = interaction.user.id
    guild = bot.get_guild(int(GUILD_ID))
    if guild:
        member = guild.get_member(user_id)
        if member and member.voice:
            await member.edit(mute=False)
            await interaction.response.send_message('おはよう!!起きたよ！！')
        else:
            await interaction.response.send_message('ボイスチャンネルにいないから、ミュート解除できないよ')
    else:
        await interaction.response.send_message('ギルドが見つからないみたいだよ!!')

@bot.tree.command(name='not_set_time', description='設定したスリープタイマーをキャンセルするよ？')
@app_commands.describe(user='キャンセルするユーザー')
async def not_set_time(interaction: discord.Interaction, user: discord.User = None):
    if user is None:
        user = interaction.user

    author_id = interaction.user.id
    has_admin_role = any(role.id == ADMIN_ROLE_ID for role in interaction.user.roles)
    
    if not has_admin_role and user.id != author_id:
        await interaction.response.send_message('他のユーザーのスリープタイマーをキャンセルするには管理者ロールが必要だよ。')
        return

    if user.id in sleep_timers:
        del sleep_timers[user.id]
        del user_sleep_times[user.id]
        await interaction.response.send_message(f'{user.name}さんのスリープタイマーがキャンセルしたよ!!。')
    else:
        await interaction.response.send_message(f'{user.name}さんにはスリープタイマーは設定されていないみたいだよ!!')

@bot.tree.command(name='set_time_now', description='現在設定されているスリープタイマーの時間を確認するよ？')
async def set_time_now(interaction: discord.Interaction):
    user_id = interaction.user.id
    if user_id in user_sleep_times:
        sleep_time = user_sleep_times[user_id]
        await interaction.response.send_message(f'現在のスリープタイマーは {sleep_time.strftime("%H:%M:%S")} 日本時間に設定されているみたいだ!!')
    else:
        await interaction.response.send_message('スリープタイマーは設定されていないみたい....')

@bot.tree.command(name='set_time_past', description='過去に設定したスリープタイマーの時間を確認するよ!!')
async def set_time_past(interaction: discord.Interaction):
    user_id = interaction.user.id
    if user_id in user_sleep_times:
        sleep_time = user_sleep_times[user_id]
        await interaction.response.send_message(f'過去に設定されたスリープタイマーは {sleep_time.strftime("%H:%M:%S")} 日本時間みたいだね')
    else:
        await interaction.response.send_message('スリープタイマーは設定されていないみたい...')

@bot.tree.command(name='help', description='僕の使い方を教えるよ!!')
async def help_command(interaction: discord.Interaction):
    help_text = (
        "**/set_sleep [時間] [ユーザー]**: スリープタイマーを設定!!時間はHH:MM形式で入力してね!!その時間にミュートして君のプライバシーを守よ!!\n"
        "**/good_morning**: おはよう!!これでミュートを解除するよ!!みんなとまたお話ができる!!やったね!!\n"
        "**/not_set_time [ユーザー]**: 設定したスリープタイマーをキャンセルできるよ!!間違えても大丈夫だね!!\n"
        "**/set_time_now**: 現在設定されているスリープタイマーの時間を確認できるよ!!不安になったらいつでも教えてあげるからね!!\n"
        "**/set_time_past**: 過去に設定したスリープタイマーの時間も教えてあげるよ!!\n"
    )
    await interaction.response.send_message(help_text)

@tasks.loop(seconds=60)
async def check_sleeptimers():
    """毎分、タイマーが設定された時間と現在の時間をチェックします。"""
    now = datetime.now(tokyo_tz)
    for user_id, (channel_id, sleep_time) in list(sleep_timers.items()):
        if now >= sleep_time:
            guild = bot.get_guild(int(GUILD_ID))
            if guild:
                member = guild.get_member(user_id)
                if member and member.voice:
                    await member.edit(mute=True)  # ユーザーをミュート
            del sleep_timers[user_id]
            del user_sleep_times[user_id]

bot.run(TOKEN)