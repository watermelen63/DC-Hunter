import discord
from discord.ext import commands
import google.genai as genai
import json
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))
print("目前工作目錄：", os.getcwd())

def load_json_folder(folder_path: str) -> dict:
    data = {}

    if not os.path.exists(folder_path):
        print(f"資料夾不存在：{folder_path}")
        return data

    for filename in os.listdir(folder_path):
        if filename.endswith('.json'):
            name = filename.replace('.json', '')

            with open(f"{folder_path}/{filename}", 'r', encoding='utf-8') as f:
                data[name] = json.load(f)
    return data

def load_memory() -> dict:
    MEMORY_FILE = "memory.json"
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_memory(memory: dict):
    MEMORY_FILE = "memory.json"

    with open(MEMORY_FILE, "w", encoding="utf-8") as f:

        json.dump(memory, f, ensure_ascii=False, indent=2)

def split_message(text: str, limit: int = 2000) -> list:
    return [text[i:i+limit] for i in range(0, len(text), limit)]

bot = discord.Bot(intents = discord.Intents.all())
json_data = load_json_folder("json")
bot.json_data = json_data

memory = load_memory()

client = genai.Client(api_key=json_data.get("ks125", {}).get("openai_api_key"))
chat = client.chats.create(model="gemini-2.0-flash")

@bot.event
async def on_message(message: discord.Message):

    if message.author == bot.user:
        return
    
    if bot.user.mentioned_in(message):
        text = message.content.replace(f'<@{bot.user.id}>', '').strip()
        if text:
            user_id = str(message.author.id)
            user_specific_raw_history = memory.get(user_id, [])

            genai_history = []
            for exchange in user_specific_raw_history:
                if "user" in exchange and exchange["user"]:
                    genai_history.append({'role': 'user', 'parts': [{'text': exchange["user"]}]})
                if "bot" in exchange and exchange["bot"]:
                    genai_history.append({'role': 'model', 'parts': [{'text': exchange["bot"]}]})
            
            try:
                user_chat_session = client.chats.create(
                    model="gemini-2.0-flash",
                    history=genai_history
                )

                response = user_chat_session.send_message(text)
                bot_response_text = response.text
            except Exception as e:
                print(f"與 Genmini 互動時發生錯誤: {e}")
                await message.channel.send("抱歉，我現在無法回應。")
                return

            user_specific_raw_history.append({
                "user": text,
                "bot": bot_response_text
            })
            memory[user_id] = user_specific_raw_history
            save_memory(memory)
            
            print(f"User({bot.user.id}): {text}\nBot: {bot_response_text}")
            
            for part in split_message(bot_response_text):
                await message.channel.send(part)
        else:
            await message.channel.send("同學你好，你ㄊㄟˋ到我了🗣️")

@bot.slash_command(description="用 AI 回應使用者的輸入")
async def echo(ctx, *, text: str):
    """一個斜線指令，會將輸入的文字傳給 AI 並回應。"""
    user_name = ctx.author.name
    response = chat.send_message(text)

    await ctx.send(f'{user_name}:{text}\n \n{bot.user}:{response.text}')
    
    for message in chat.get_history():
        print(f'role - {message.role}', end=": ")
        print(message.parts[0].text)

@bot.event
async def on_member_join(member: discord.Member):

    welcome_channel_id = json_data.get("ks125", {}).get("welcome_channel_id")
    if welcome_channel_id:
        welcome_channel = bot.get_channel(int(welcome_channel_id))
    else:
        welcome_channel = discord.utils.get(member.guild.text_channels, name="general")
    
    if welcome_channel:
        try:
            prompt = f"請用繁體中文，以活潑、親切但不要太輕浮的語氣，歡迎一位名叫 {member.name} 的新成員加入我們的 Discord 伺服器。"
            response = chat.send_message(prompt)
            welcome_message = response.text
            await welcome_channel.send(f"{welcome_message}")
        except Exception as e:
            print(f"生成歡迎訊息時發生錯誤: {e}")
            await welcome_channel.send(f"歡迎 {member.mention} 加入我們的伺服器！")
    else:
        print(f"找不到名為 'general' 或 ID 為 {welcome_channel_id} 的頻道。")

# --------------------- Bot 啟動 ---------------------
@bot.event
async def on_ready(): 
    """當 Bot 成功登入並準備好時觸發。"""
    print(f'{bot.user} IS ONLINE')

    activity = discord.Activity(type=discord.ActivityType.watching, name="大家聊天") # 我幫你加了點文字
    await bot.change_presence(status=discord.Status.online, activity=activity)

cogs_list = [
    'knowledge',
    "user_singin"
]

for cog in cogs_list:
    try:
        bot.load_extension(f'cogs.{cog}')
        print(f"成功載入 Cog: {cog}")
    except Exception as e:
        print(f"Failed to load cog {cog}: {e}")

token = bot.json_data.get("ks125", {}).get("DISCORD_TOKEN")

if token:
    bot.run(token)
else:
    print("錯誤：在 ks125.json 中找不到 DISCORD_TOKEN。")