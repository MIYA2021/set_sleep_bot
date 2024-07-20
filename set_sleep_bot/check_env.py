import os
from dotenv import load_dotenv

# .env ファイルを読み込む
load_dotenv()

# 環境変数の確認
print("DISCORD_TOKEN:", os.getenv('DISCORD_TOKEN'))
print("GUILD_ID:", os.getenv('GUILD_ID'))
