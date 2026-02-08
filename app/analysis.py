import json
import os

import os

import ollama

USER_TRAITS = "data/user_traits.json"
RECORDS_FILE = "data/chat_records.json"
DEFINE_TRAITS_FILE = "data/define_traits.json"
TRAITS = [
    "perfectionist",
    "helper",
    "achiever",
    "individualist",
    "investigator",
    "loyalist",
    "enthusiast",
    "challenger",
    "peacemaker",
]
MODEL_ID = os.getenv("ANALYSIS_MODEL_ID", "gemma3:4b")

memory = [
    {
        "role": "system",
        "content": "你是性格分析助手，請根據對話內容判斷最符合的九型人格類型。",
    }
]


def _load_define_traits():
    if not os.path.exists(DEFINE_TRAITS_FILE):
        return {}
    try:
        with open(DEFINE_TRAITS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


async def run_analysis(user_id: str):
    """Analyze chat_records.json and write result into user_traits.json."""
    if not os.path.exists(RECORDS_FILE):
        print(f"Missing records file: {RECORDS_FILE}")
        return False

    with open(RECORDS_FILE, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except Exception as e:
            print(f"JSON load error: {e}")
            return False

    messages_list = data.get("all_messages", [])
    user_name = data.get("user_name", "")
    if not messages_list:
        print("No messages to analyze.")
        return False

    combined_text = ""
    for pair in messages_list:
        combined_text += f"AI: {pair.get('ai','')}\nUser: {pair.get('user','')}\n\n"

    current_context = memory.copy()
    define_traits = _load_define_traits()
    define_text = ""
    for key, value in define_traits.items():
        define_text += f"{key}: {value}\n"

    prompt = (
        "請根據特質定義與對話內容判斷最符合的類型（只能回傳一個標籤）。\n"
        f"可用標籤: {', '.join(TRAITS)}\n\n"
        f"特質定義:\n{define_text}\n"
        f"對話內容:\n{combined_text}"
    )
    current_context.append({"role": "user", "content": prompt})

    try:
        response = ollama.chat(model=MODEL_ID, messages=current_context)
        predicted_label = response["message"]["content"].strip().lower()

        final_trait = "error"
        for t in TRAITS:
            if t in predicted_label:
                final_trait = t
                break

        if final_trait != "error":
            if not os.path.exists(USER_TRAITS) or os.stat(USER_TRAITS).st_size == 0:
                with open(USER_TRAITS, "w", encoding="utf-8") as f:
                    json.dump({t: [] for t in TRAITS}, f, ensure_ascii=False, indent=4)

            with open(USER_TRAITS, "r", encoding="utf-8") as f:
                traits_data = json.load(f)

            if final_trait not in traits_data:
                traits_data[final_trait] = []

            if not any(item.get("user_id") == user_id for item in traits_data.get(final_trait, [])):
                traits_data[final_trait].append({"user_id": user_id, "user_name": user_name})
                with open(USER_TRAITS, "w", encoding="utf-8") as f:
                    json.dump(traits_data, f, ensure_ascii=False, indent=4)

        data["all_messages"] = []
        data["user_id"] = ""
        data["user_name"] = ""
        data["analysis_status"] = "done"
        with open(RECORDS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"Analysis complete. Trait: {final_trait}")
        return True

    except Exception as e:
        print(f"Analysis failed: {e}")
        try:
            data["analysis_status"] = "failed"
            with open(RECORDS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
        return False
