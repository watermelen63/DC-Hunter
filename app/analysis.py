import json
import discord
import os
import ollama
import asyncio
from dotenv import load_dotenv

load_dotenv()
DISCORD_TOKEN = os.getenv("DC_HUNTER_TOKEN")

USER_TRAITS = "user_traits.json"
RECORDS_FILE = "chat_records.json"

SYSTEM_PROMPT = """
你是一個人類性格分析師，透過人類之間的對話，來去分析人類的性格，並分成完美主義者、助人者、成就者、個人主義者、觀察者、忠誠者、樂觀者、和平主義者、挑戰者。各類人的定義放在define.json中。你必須分析對話，去檢索其中的關鍵字，並給予一個最符合的答案。
"""
TRAITS = ["完美主義者","助人者","成就者","個人主義者","觀察者","忠誠者","樂觀者","和平主義者","挑戰者"]

model_id = "deepseek-v3.1:671b-cloud"

memory = [{"role": "system", "content": SYSTEM_PROMPT}]

intents = discord.Intents.default()
bot = discord.Bot(intents = intents)

@bot.event
async def on_ready():
	print(f"{bot.user} is now running!")


async def get_ai_response_local(combined_text):
    """
    透過 Ollama 本地模型進行分析
    """
    prompt = f"""
    你是一位人格分析專家。請分析以下 Discord 對話：
    ---
    {combined_text}
    ---
    請從以下標籤中選出一個最符合的：{", ".join(TRAITS)}
    
    規則：
    1. 只回傳標籤名稱，不要解釋。
    2. 不要輸出任何標點符號。
    3. 若無法判斷，回傳「社交型」。
    """

    try:
        # 呼叫本地 Ollama
        # model 參數請填寫你本地有的模型名稱，例如 'llama3' 或 'gemma'
        response = ollama.chat(model='llama3', messages=[
                {'role': 'user','content': prompt},
            ]
        )
        
        result = response['message']['content'].strip()
        
        # 檢查回傳值是否在清單內
        for trait in TRAITS:
            if trait in result: # 本地模型有時會多噴字，用關鍵字判定較穩
                return trait
        return "社交型"

    except Exception as e:
        print(f"本地 AI 呼叫失敗: {e}")
        return "社交型"

async def run_analysis(user_id):
    """
    分析流程：讀取 chat_records.json -> AI 分析 -> 寫入 categories.json -> 刪除紀錄
    """
    if not os.path.exists(RECORDS_FILE): return False

    # 1. 讀取紀錄
    with open(RECORDS_FILE, "r", encoding="utf-8") as f:
        all_records = json.load(f)

    if user_id not in all_records or not all_records[user_id]:
        return False

    # 2. 執行分析
    combined_text = "\n".join(all_records[user_id])
    predicted_label = await get_ai_response_local(combined_text)

    # 3. 寫入分類
    with open(USER_TRAITS, "r", encoding="utf-8") as f:
        categories = json.load(f)

    if predicted_label in categories:
        exists = any(item["user_id"] == user_id for item in categories[predicted_label])
        if not exists:
            categories[predicted_label].append({"user_id": user_id})
            with open(USER_TRAITS, "w", encoding="utf-8") as f:
                json.dump(categories, f, ensure_ascii=False, indent=4)

    # 4. 刪除該用戶已分析的對話
    del all_records[user_id]
    with open(RECORDS_FILE, "w", encoding="utf-8") as f:
        json.dump(all_records, f, ensure_ascii=False, indent=4)
    
    return predicted_label

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)