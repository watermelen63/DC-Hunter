import discord
import os
import json
import random
import chat
import analysis
import employ
from dotenv import load_dotenv
import chat

app = discord.Bot(intents=discord.Intents.all())

# 確保 data 資料夾存在
os.makedirs("data", exist_ok=True)

# 初始化 chat_run.json（保留 welcomed_users）
chat_run_file = "data/chat_run.json"
if not os.path.exists(chat_run_file):
    with open(chat_run_file, "w", encoding="utf-8") as f:
        json.dump({"welcomed_users": [], "user_id": ""}, f, ensure_ascii=False, indent=2)

# 初始化 chat_records.json（對話紀錄可以重置）
chat_records_file = "data/chat_records.json"
with open(chat_records_file, "w", encoding="utf-8") as f:
    json.dump({"all_messages": [], "user_id": ""}, f, ensure_ascii=False, indent=2)

# 設定 chat.py
chat.setup(app)

# 載入環境變數
load_dotenv()
DC_HUNTER_TOKEN = os.getenv("DC_HUNTER_TOKEN")

@app.event
async def on_ready():
    print(f"✅ {app.user} is now running!")

if __name__ == "__main__":
    app.run(DC_HUNTER_TOKEN)
