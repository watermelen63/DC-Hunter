import os
import asyncio
import logging
import json

import discord
from dotenv import load_dotenv
import ollama

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
model_id = "gemma3:4b"

bot = discord.Bot(intents = discord.Intents.all())

@bot.event
async def on_ready():
    logging.info(f"{bot.user} is online.")

SYSTEM_PROMT = """
你是一個擅長使用話術讓他人放下防備，並且對你坦露心聲的人，你可以用10句話左右，並且不超過20句話。
透過聊天對話的方式，並且回覆時不能少於兩句話。
如果要問問題，每次最多只能提出一個問題。你的目的要試圖讓對方暴露出它的真實性格。
如果知道了對方的個性，單單打出一個end並結束。
"""

memory = [{"role": "system", "content": SYSTEM_PROMT}]




async def generate_reply(prompt: str) -> str:
    memory.append({"role": "user", "content": prompt})

    try:
        response = await asyncio.to_thread(
            ollama.chat,
            model = model_id,
            messages = memory,
        )
        reply = response.message.content
        memory.append({"role": "assistant", "content": reply})
        return f"{reply}\n\nby {model_id}"
    
    except Exception as e:
            logging.error = "Ollama模型回覆失敗: {e}"
            return f"{reply}\n\nby {model_id}"


async def enter_json(prompt:str) -> str:
    with open("data/chat_records.json", "r", encoding="utf-8") as f:
        chat_records = json.load(f)

    chat_records["all_messages"].append(prompt)

    with open("data/chat_records.json", "w", encoding="utf-8") as f:
        json.dump(chat_records, f, ensure_ascii=False, indent=2)

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    with open("data/chat_run.json", "r") as f:
        data = json.load(f)

    timesf = int(data["times"])
    userf = int(data["user"])

    with open("data/chat_run.json", "w") as f:
        if timesf <= 0:
            data["times"] = 10
            data["user"] = ""
            json.dump(data, f, ensure_ascii=False, indent=2)
            return
        else:
            data["times"] = str(timesf - 1)
            json.dump(data, f, ensure_ascii=False, indent=2)

    print (timesf)
    
    if timesf != 0 and message.author.id == userf:
        prompt = message.content.replace(f'<@{bot.user.id}>', '').strip()

        if not prompt:
            await message.reply("Anything help?")
            return
        
        thinking_msg = await message.reply("Thinking~~~")
        await enter_json(prompt)

        try:
            answer = await asyncio.wait_for(generate_reply(prompt), timeout = 30.0)
            await enter_json(answer)
        except Exception as e:
            answer = "Something worng."
            logging.error(f"error: {e}")
        
        await thinking_msg.edit(content = answer)


@bot.event
async def on_member_join(member):
    DISCORD_AI_CHAT_CHANNEL_ID = 1469663806870524127
    ai_chat = bot.get_channel(DISCORD_AI_CHAT_CHANNEL_ID)

    uid = str(member.id)

    with open("data/chat_run.json", "r") as f:
        data = json.load(f)

    with open("data/chat_run.json", "w") as f:
        data["user"] = uid
        json.dump(data, f, ensure_ascii=False, indent=2)

    print (uid)

    await ai_chat.send(f"""
{member.mention} WELCOME JOIN👋
請你描述一下你自己吧~~~
                       """)


@bot.event
async def on_ready():
    print(f"✅{bot.user} IS ONLINE.")

    with open("data/chat_run.json", "w") as f:
        data = {"times": "10", "user": ""}
        json.dump(data, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)