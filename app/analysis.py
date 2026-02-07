import json
import os
import asyncio

# 假設你使用 OpenAI 或 Gemini
# from your_ai_library import get_ai_response 

USER_TRAITS = "user_traits.json"
RECORDS_FILE = "chat_records.json"

async def run_analysis(user_id):
    """
    執行分析的核心函式
    """
    try:
        # 1. 讀取聊天紀錄
        with open(RECORDS_FILE, "r", encoding="utf-8") as f:
            all_records = json.load(f)
        
        if user_id not in all_records or not all_records[user_id]:
            return False

        user_chats = all_records[user_id] # 取得該用戶的聊天陣列
        combined_text = "\n".join(user_chats)

        # 2. AI 分析邏輯 (這部分是你需要微調的 Prompt)
        # 這裡模擬 AI 判斷後回傳了其中一個標籤
        # predicted_label = await get_ai_response(combined_text)
        predicted_label = "技術型" # 範例結果

        # 3. 讀取並更新分類檔案
        with open(USER_TRAITS, "r", encoding="utf-8") as f:
            user_traits = json.load(f)

        if predicted_label in user_traits:
            # 檢查是否已存在，不存在才加入
            if not any(item["user_id"] == user_id for item in user_traits[predicted_label]):
                user_traits[predicted_label].append({"user_id": user_id})
                
                with open(USER_TRAITS, "w", encoding="utf-8") as f:
                    json.dump(user_traits, f, ensure_ascii=False, indent=4)

        # 4. 分析完後刪除該用戶在 chat_records.json 的資料
        del all_records[user_id]
        with open(RECORDS_FILE, "w", encoding="utf-8") as f:
            json.dump(all_records, f, ensure_ascii=False, indent=4)
        
        return predicted_label

    except Exception as e:
        print(f"分析失敗: {e}")
        return None