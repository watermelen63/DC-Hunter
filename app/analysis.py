import json
import discord
import os
import ollama
import logging
import asyncio
from dotenv import load_dotenv

# --- 設定與路徑 ---
load_dotenv()
DISCORD_TOKEN = os.getenv("DC_HUNTER_TOKEN")

USER_TRAITS = "user_traits.json"
RECORDS_FILE = "chat_records.json"
DEFINE_FILE = "define.json"

# 九型人格標籤 (與 define.json 的 Key 對應)
TRAITS = [
    "perfectionist", "helper", "achiever", "individualist", 
    "investigator", "loyalist", "enthusiast", "challenger", "peacemaker"
]

# AI 模型設定
MODEL_ID = "deepseek-v3.1:671b-cloud"

# --- 1. AI 記憶體初始化 (System Message) ---
memory = [
    {
        "role": "system", 
        "content": "你是一位專業的人格分析師。你的工作是根據『九型人格』定義分析用戶對話，並回傳最符合的類別標籤。"
    }
]

def initialize_ai_knowledge():
    """從 define.json 載入人格定義到 AI 的長期記憶中"""
    if os.path.exists(DEFINE_FILE):
        try:
            with open(DEFINE_FILE, "r", encoding="utf-8") as f:
                definitions = json.load(f)
                def_text = "以下是各人格的詳細定義與關鍵字，請作為你分析的唯一基準：\n" + json.dumps(definitions, ensure_ascii=False)
                memory.append({"role": "system", "content": def_text})
                print("💡 [System] 成功載入人格定義至 AI 記憶體。")
        except Exception as e:
            print(f"❌ [Error] 讀取定義檔失敗: {e}")
    else:
        print("⚠️ [Warning] 找不到 define.json，分析精確度可能會受影響。")

# 執行初始化
initialize_ai_knowledge()

# --- 2. Discord Bot 設定 ---
intents = discord.Intents.default()
intents.message_content = True # 必須開啟才能讀取聊天內容
bot = discord.Bot(intents=intents)

@bot.event
async def on_ready():
    # 初始化必要的 JSON 檔案格式
    if not os.path.exists(USER_TRAITS):
        with open(USER_TRAITS, "w", encoding="utf-8") as f:
            json.dump({t: [] for t in TRAITS}, f, ensure_ascii=False, indent=4)
    
    if not os.path.exists(RECORDS_FILE):
        with open(RECORDS_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)

    print(f"✅ {bot.user} 已上線，分析系統就緒！")

# --- 3. 核心分析邏輯 ---

async def get_ai_response_local(combined_text):
    """
    呼叫 Ollama 並利用 memory 副本進行單次分析
    """
    # 複製一份 memory 避免不同用戶的對話互相污染 (Context Isolation)
    current_context = memory.copy()
    
    prompt = f"""
請分析以下 Discord 成員的對話內容，並從這九個標籤中選出一個最符合的：{", ".join(TRAITS)}。

【待分析對話】：
---
{combined_text}
---

【規則】：
1. 僅回傳一個標籤名稱（英文 Key），不要解釋原因。
2. 不要包含任何標點符號。
3. 若資訊極度不足無法判斷，請回傳 'error'。
"""
    
    current_context.append({"role": "user", "content": prompt})

    try:
        # 呼叫本地 Ollama
        response = ollama.chat(model=MODEL_ID, messages=current_context)
        result = response['message']['content'].strip().lower()
        
        # 進行結果檢查，確保回傳值合法
        for trait in TRAITS:
            if trait in result:
                return trait
        return "error"

    except Exception as e:
        print(f"❌ [AI Error] 呼叫 Ollama 失敗: {e}")
        return "error"

async def run_analysis(user_id):
    """
    分析流程：
    1. 讀取 chat_records.json 中的 all_messages (約略 10 個 message 的量)
    2. 分析並寫入 user_traits.json
    3. 清空 all_messages
    """
    if not os.path.exists(RECORDS_FILE): return False

    # 1. 讀取待分析紀錄
    with open(RECORDS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    messages_list = data.get("all_messages", [])
    
    if not messages_list:
        return False

    # 2. 整合文字並請求 AI
    combined_text = "\n".join(messages_list)
    predicted_label = await get_ai_response_local(combined_text)

    # 3. 寫入永久分類檔 (user_traits.json)
    try:
        with open(USER_TRAITS, "r", encoding="utf-8") as f:
            traits_data = json.load(f)

        if predicted_label in traits_data:
            # 檢查該 ID 是否已存在於該分類中
            if not any(item["user_id"] == user_id for item in traits_data[predicted_label]):
                traits_data[predicted_label].append({"user_id": user_id})
                
                with open(USER_TRAITS, "w", encoding="utf-8") as f:
                    json.dump(traits_data, f, ensure_ascii=False, indent=4)
        
        # 4. 關鍵刪除：清空 all_messages 以供下一位使用
        data["all_messages"] = []
        with open(RECORDS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
            
        print(f"✨ 用戶 {user_id} 分析完畢，歸類為 {predicted_label}，紀錄已清空。")
        return predicted_label

    except Exception as e:
        print(f"❌ 檔案處理失敗: {e}")
        return None

# --- 4. 啟動區 ---
if __name__ == "__main__":
    if DISCORD_TOKEN:
        bot.run(DISCORD_TOKEN)
    else:
        print("❌ 找不到 Discord Token，請檢查 .env 檔案。")