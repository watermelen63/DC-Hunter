import asyncio
import json
import os

import discord
from dotenv import load_dotenv

import analysis
import chat
import employ

app = discord.Bot(intents=discord.Intents.all())

# Ensure data directory exists
os.makedirs("data", exist_ok=True)

# Reset data on every startup
chat_run_file = "data/chat_run.json"
with open(chat_run_file, "w", encoding="utf-8") as f:
    json.dump({"welcomed_users": [], "user_id": "", "user_count": {}}, f, ensure_ascii=False, indent=2)

chat_records_file = "data/chat_records.json"
with open(chat_records_file, "w", encoding="utf-8") as f:
    json.dump(
        {"all_messages": [], "user_id": "", "user_name": "", "analysis_status": "pending"},
        f,
        ensure_ascii=False,
        indent=2,
    )

user_traits_file = "data/user_traits.json"
if os.path.exists(user_traits_file):
    with open(user_traits_file, "w", encoding="utf-8") as f:
        json.dump({trait: [] for trait in analysis.TRAITS}, f, ensure_ascii=False, indent=4)

# Register chat + employ commands
chat.setup(app)
employ.setup(app)

# Load env and token
load_dotenv()
DC_HUNTER_TOKEN = os.getenv("DC_HUNTER_TOKEN")


async def monitor_and_analyze():
    """Poll chat_records.json and run analysis after 10 messages."""
    while True:
        await asyncio.sleep(5)
        if not os.path.exists(chat_records_file):
            continue

        with open(chat_records_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            user_id = data.get("user_id", "")
            all_messages = data.get("all_messages", [])
            analysis_status = data.get("analysis_status", "pending")

        if user_id and len(all_messages) >= 10 and analysis_status == "pending":
            print(f"Running analysis for user_id={user_id} ...")
            await analysis.run_analysis(user_id)


@app.event
async def on_ready():
    print(f"{app.user} is now running!")
    app.loop.create_task(monitor_and_analyze())


if __name__ == "__main__":
    app.run(DC_HUNTER_TOKEN)
