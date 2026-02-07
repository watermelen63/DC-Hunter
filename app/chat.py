import os
import asyncio
import logging

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
做為一個心理諮商師
和人聊天
設法探出這個人的個性
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

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    if bot.user.mentioned_in(message):
        prompt = message.content.replace(f'<@{bot.user.id}>', '').strip()

        print (prompt)

        if not prompt:
            await message.reply("Anything help?")
            return
        
        thinking_msg = await message.reply("Thinking~~~")

        try:
            answer = await asyncio.wait_for(generate_reply(prompt), timeout = 30.0)
        except Exception as e:
            answer = "Something worng."
            logging.error(f"error: {e}")
        
        await thinking_msg.edit(content = answer)

@bot.event
async def on_ready():
    print(f"✅{bot.user} IS ONLINE.")


if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)