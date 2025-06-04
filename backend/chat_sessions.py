# Minimal chat session management
import json
from pathlib import Path
from datetime import datetime

def create_session(user_id: str, name: str = None):
    path = Path("data") / "chat_sessions.json"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            all_sessions = json.load(f)
    else:
        all_sessions = {}
    if user_id not in all_sessions:
        all_sessions[user_id] = []
    session_id = f"sess_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"
    session = {"id": session_id, "name": name or session_id, "created_at": datetime.utcnow().isoformat()}
    all_sessions[user_id].append(session)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(all_sessions, f, ensure_ascii=False, indent=2)
    return session

def list_sessions(user_id: str):
    path = Path("data") / "chat_sessions.json"
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        all_sessions = json.load(f)
    return all_sessions.get(user_id, [])
