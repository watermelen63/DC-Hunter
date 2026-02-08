# chat.py
import os
import asyncio
import logging
import json

import discord
from dotenv import load_dotenv
import ollama

def setup(bot: discord.Bot):
    load_dotenv()
    model_id = "gemma3:4b"

    # 防止多次 setup
    if getattr(bot, "_chat_setup_done", False):
        return
    bot._chat_setup_done = True

    SYSTEM_PROMPT = """
你是一個擅長使用話術讓他人放下防備，並且對你坦露心聲的人，你可以用10句話。
透過聊天對話的方式，並且回覆時不能少於兩句話。
如果要問問題，每次最多只能提出一個問題。你的目的要試圖讓對方暴露出它的真實性格。
如果知道了對方的個性，單單打出一個end並結束。
"""

    memory = [{"role": "system", "content": SYSTEM_PROMPT}]

    CHAT_RUN_FILE = "data/chat_run.json"
    CHAT_RECORDS_FILE = "data/chat_records.json"
    os.makedirs("data", exist_ok=True)

    # 初始化 JSON 檔案
    if not os.path.exists(CHAT_RUN_FILE) or os.stat(CHAT_RUN_FILE).st_size == 0:
        with open(CHAT_RUN_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "user_id": "",
                "welcomed_users": [],
                "user_count": {}
            }, f, ensure_ascii=False, indent=2)

    if not os.path.exists(CHAT_RECORDS_FILE) or os.stat(CHAT_RECORDS_FILE).st_size == 0:
        with open(CHAT_RECORDS_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "all_messages": []
            }, f, ensure_ascii=False, indent=2)

    # ----------------------------
    # AI 回覆生成
    # ----------------------------
    async def generate_reply(prompt: str, timesf: int) -> str:
        memory.append({"role": "user", "content": prompt})
        try:
            response = await asyncio.to_thread(
                ollama.chat,
                model=model_id,
                messages=memory,
            )
            reply = response.message.content
            memory.append({"role": "assistant", "content": reply})
            return f"{reply}\n\nby {model_id} \n剩:{timesf}題"
        except Exception as e:
            logging.error(f"Ollama模型回覆失敗: {e}")
            return f"AI 回覆失敗\nby {model_id}"

    # ----------------------------
    # 將對話寫入 chat_records.json
    # ----------------------------
    async def enter_json(ai_text: str, user_text: str):
        try:
            with open(CHAT_RECORDS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            data = {"all_messages": []}

        data["all_messages"].append({"ai": ai_text, "user": user_text})

        with open(CHAT_RECORDS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    # ----------------------------
    # 新人加入事件
    # ----------------------------
    @bot.event
    async def on_member_join(member):
        DISCORD_AI_CHAT_CHANNEL_ID = 1469663806870524127
        ai_chat = bot.get_channel(DISCORD_AI_CHAT_CHANNEL_ID)
        if not ai_chat:
            return

        try:
            with open(CHAT_RUN_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            data = {"user_id": "", "welcomed_users": [], "user_count": {}}

        data.setdefault("welcomed_users", [])
        data.setdefault("user_count", {})

        # 已歡迎過就不再送訊息
        if str(member.id) in data["welcomed_users"]:
            return

        welcome_msg = f"{member.mention} WELCOME JOIN👋\n請你描述一下你自己吧~~~"
        await ai_chat.send(welcome_msg)

        # 設定目前對話使用者
        data["user_id"] = str(member.id)
        data["welcomed_users"].append(str(member.id))
        data["user_count"].setdefault(str(member.id), 0)

        with open(CHAT_RUN_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"新使用者加入: {member.id}")

    # ----------------------------
    # 使用者訊息事件
    # ----------------------------
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

        # 只處理目前設定的使用者
        if user_id != data.get("user_id"):
            return

        # 檢查是否已達 10 次
        if data["user_count"].get(user_id, 0) >= 10:
            await message.reply("你已經回答了 10 次問題，對話結束囉！")
            return

        prompt = message.content.replace(f'<@{bot.user.id}>', '').strip()
        if not prompt:
            await message.reply("請輸入訊息喔！")
            return

        # AI 生成回覆
        thinking_msg = await message.reply("Thinking~~~")
        try:
            timesf = 10 - data["user_count"].get(user_id, 0)  # 剩餘次數
            answer = await asyncio.wait_for(generate_reply(prompt, timesf=timesf), timeout=30.0)
        except Exception as e:
            logging.error(f"AI 回覆失敗: {e}")
            answer = "Something wrong."

        # 寫入對話紀錄
        await enter_json(answer, prompt)

        # 更新對話次數
        data["user_count"][user_id] = data["user_count"].get(user_id, 0) + 1
        with open(CHAT_RUN_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        # 編輯訊息顯示 AI 回覆
        await thinking_msg.edit(content=answer)
