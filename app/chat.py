# chat.py
import asyncio
import json
import logging
import os

import discord
from dotenv import load_dotenv
import ollama


def setup(bot: discord.Bot):
    load_dotenv()
    model_id = "gemma3:4b"

    # Avoid duplicate setup
    if getattr(bot, "_chat_setup_done", False):
        return
    bot._chat_setup_done = True

    SYSTEM_PROMPT = """
你是友善且自然的聊天助手。請和新加入的使用者對話，最多 10 次。
你需要詢問對方的興趣與特質，並鼓勵他描述自己。
"""

    memory = [{"role": "system", "content": SYSTEM_PROMPT}]

    CHAT_RUN_FILE = "data/chat_run.json"
    CHAT_RECORDS_FILE = "data/chat_records.json"
    os.makedirs("data", exist_ok=True)

    # Ensure JSON files exist
    if not os.path.exists(CHAT_RUN_FILE) or os.stat(CHAT_RUN_FILE).st_size == 0:
        with open(CHAT_RUN_FILE, "w", encoding="utf-8") as f:
            json.dump(
                {"user_id": "", "welcomed_users": [], "user_count": {}},
                f,
                ensure_ascii=False,
                indent=2,
            )

    if not os.path.exists(CHAT_RECORDS_FILE) or os.stat(CHAT_RECORDS_FILE).st_size == 0:
        with open(CHAT_RECORDS_FILE, "w", encoding="utf-8") as f:
            json.dump(
                {"all_messages": [], "user_id": "", "user_name": "", "analysis_status": "pending"},
                f,
                ensure_ascii=False,
                indent=2,
            )

    async def generate_reply(prompt: str, remaining: int) -> str:
        memory.append({"role": "user", "content": prompt})
        try:
            response = await asyncio.to_thread(
                ollama.chat,
                model=model_id,
                messages=memory,
            )
            reply = response.message.content
            memory.append({"role": "assistant", "content": reply})
            return f"{reply}\n\nby {model_id}\n剩餘 {remaining} 次"
        except Exception as e:
            logging.error(f"Ollama chat error: {e}")
            return f"AI 回覆失敗\nby {model_id}"

    async def enter_json(ai_text: str, user_text: str, user_id: str, user_name: str):
        try:
            with open(CHAT_RECORDS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            data = {"all_messages": [], "user_id": "", "user_name": "", "analysis_status": "pending"}

        data.setdefault("all_messages", [])
        data["all_messages"].append({"ai": ai_text, "user": user_text})
        data["user_id"] = user_id
        data["user_name"] = user_name
        data["analysis_status"] = "pending"

        with open(CHAT_RECORDS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @bot.event
    async def on_member_join(member):
        WELCOME_CHANNEL_ID = 1469663806870524127
        ai_chat = bot.get_channel(WELCOME_CHANNEL_ID)
        if not ai_chat:
            return

        try:
            with open(CHAT_RUN_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            data = {"user_id": "", "welcomed_users": [], "user_count": {}}

        data.setdefault("welcomed_users", [])
        data.setdefault("user_count", {})

        if str(member.id) in data["welcomed_users"]:
            return

        welcome_msg = (
            f"{member.mention} 歡迎加入！\n"
            "請在此頻道和我聊天 10 次喔～\n"
            "先告訴我你的興趣與你覺得自己的特質是什麼？"
        )
        await ai_chat.send(welcome_msg)

        data["user_id"] = str(member.id)
        data["welcomed_users"].append(str(member.id))
        data["user_count"].setdefault(str(member.id), 0)

        with open(CHAT_RUN_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"Welcomed user {member.id}")

    @bot.event
    async def on_message(message):
        if message.author == bot.user:
            return

        try:
            with open(CHAT_RUN_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            data = {"user_id": "", "welcomed_users": [], "user_count": {}}

        data.setdefault("welcomed_users", [])
        data.setdefault("user_id", "")
        data.setdefault("user_count", {})

        user_id = str(message.author.id)

        # Only respond to the current new user
        if user_id != data.get("user_id"):
            return

        if data["user_count"].get(user_id, 0) >= 10:
            await message.reply("你已完成 10 次對話，之後將進行分析。")
            return

        prompt = message.content.replace(f"<@{bot.user.id}>", "").strip()
        if not prompt:
            await message.reply("請輸入內容再試一次。")
            return

        thinking_msg = await message.reply("Thinking~~~")
        try:
            remaining = 10 - data["user_count"].get(user_id, 0)
            answer = await asyncio.wait_for(generate_reply(prompt, remaining=remaining), timeout=30.0)
        except Exception as e:
            logging.error(f"AI reply error: {e}")
            answer = "Something went wrong."

        await enter_json(answer, prompt, user_id=user_id, user_name=str(message.author))

        data["user_count"][user_id] = data["user_count"].get(user_id, 0) + 1
        with open(CHAT_RUN_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        await thinking_msg.edit(content=answer)
