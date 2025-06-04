# Minimal chat history storage
import json
from pathlib import Path

def save_chat(user_id: str, question: str, answer: str):
    path = Path("data") / "chat_history.json"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            all_history = json.load(f)
    else:
        all_history = {}
    if user_id not in all_history:
        all_history[user_id] = []
    all_history[user_id].append({"question": question, "answer": answer})
    with open(path, "w", encoding="utf-8") as f:
        json.dump(all_history, f, ensure_ascii=False, indent=2)

def get_history(user_id: str):
    path = Path("data") / "chat_history.json"
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        all_history = json.load(f)
    return all_history.get(user_id, [])
