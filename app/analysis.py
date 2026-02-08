import json
import discord
import os
import ollama
from dotenv import load_dotenv

load_dotenv()
DISCORD_TOKEN = os.getenv("DC_HUNTER_TOKEN")

USER_TRAITS = "data/user_traits.json"
RECORDS_FILE = "data/chat_records.json" # 檔案放在 data/ 底下
DEFINE_FILE = "data/define_traits.json"

TRAITS = ["perfectionist", "helper", "achiever", "individualist", "investigator", "loyalist", "enthusiast", "challenger", "peacemaker"]
MODEL_ID = "deepseek-v3.1:671b-cloud"

memory = [{"role": "system", "content": "你是一位專業的人格分析師。請根據九型人格分析對話。"}]

# --- 核心分析邏輯 ---

async def run_analysis(user_id):
    if not os.path.exists(RECORDS_FILE): 
        print(f"❌ 找不到檔案: {RECORDS_FILE}")
        return False

    with open(RECORDS_FILE, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except Exception as e:
            print(f"❌ JSON 解析失敗: {e}")
            return False
    
    # 【偵錯印出】看看讀到了什麼
    messages_list = data.get("all_messages", [])
    print(f"🔍 [Debug] 從 JSON 讀取到的訊息筆數: {len(messages_list)}")

    if not messages_list:
        print("ℹ️ [Info] JSON 內容判定為空。")
        return False

    # 整合文字
    combined_text = ""
    for pair in messages_list:
        combined_text += f"AI: {pair.get('ai', '')}\nUser: {pair.get('user', '')}\n\n"

    # 請求 AI
    current_context = memory.copy()
    prompt = f"分析以下對話並從標籤中選一個：{', '.join(TRAITS)}\n\n{combined_text}"
    current_context.append({"role": "user", "content": prompt})

    try:
        response = ollama.chat(model=MODEL_ID, messages=current_context)
        predicted_label = response['message']['content'].strip().lower()
        
        # 簡單過濾標籤
        final_trait = "error"
        for t in TRAITS:
            if t in predicted_label:
                final_trait = t
                break
        
        # 寫入結果（若檔案不存在則先建立初始結構）
        if final_trait != "error":
            if not os.path.exists(USER_TRAITS):
                with open(USER_TRAITS, "w", encoding="utf-8") as f:
                    json.dump({t: [] for t in TRAITS}, f, ensure_ascii=False, indent=4)

            with open(USER_TRAITS, "r", encoding="utf-8") as f:
                traits_data = json.load(f)

            if final_trait not in traits_data:
                traits_data[final_trait] = []

            if not any(item.get("user_id") == user_id for item in traits_data.get(final_trait, [])):
                traits_data[final_trait].append({"user_id": user_id})
                with open(USER_TRAITS, "w", encoding="utf-8") as f:
                    json.dump(traits_data, f, ensure_ascii=False, indent=4)

        # 【關鍵】重置紀錄（清空對話並將 user_id 值重置為空字串）
        data["all_messages"] = []
        data["user_id"] = ""
        with open(RECORDS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        print(f"✨ 分析完畢！歸類為: {final_trait}")
        return True

    except Exception as e:
        print(f"❌ 分析過程出錯: {e}")
        return False

# --- 事件觸發 ---

intents = discord.Intents.default()
bot = discord.Bot(intents=intents)

@bot.event
async def on_ready():
    print(f"✅ {bot.user} 已上線！")
    
    # 讀取並檢查
    if os.path.exists(RECORDS_FILE):
        with open(RECORDS_FILE, "r", encoding="utf-8") as f:
            d = json.load(f)
            msg_len = len(d.get("all_messages", []))
            uid = d.get("user_id", "Unknown")
            
            print(f"🚀 [Auto] 目前 JSON 內有 {msg_len} 組對話。")
            
            if msg_len > 0:
                print("🏁 啟動分析中...")
                await run_analysis(uid)
            else:
                print("💤 內容為空，不執行分析。")

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)