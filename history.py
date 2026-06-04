import json
import os
from datetime import datetime

HISTORY_FILE = "/tmp/sitescore_history.json"

def load_history():
    try:
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, "r") as f:
                return json.load(f)
    except:
        pass
    return []

def save_to_history(result):
    history = load_history()
    entry = {
        "timestamp":   datetime.now().strftime("%d %b %Y, %I:%M %p"),
        "address":     result["address"],
        "brand_type":  result.get("brand_type", "restaurant"),
        "total_score": result["total_score"],
        "verdict":     result["verdict"],
        "scores":      result["scores"],
        "lat":         result["lat"],
        "lng":         result["lng"],
    }
    # Avoid duplicates — remove if same address exists
    history = [h for h in history
               if h["address"] != result["address"]]
    history.insert(0, entry)  # newest first
    history = history[:50]    # keep last 50 only
    try:
        with open(HISTORY_FILE, "w") as f:
            json.dump(history, f)
    except:
        pass
    return entry

def clear_history():
    try:
        if os.path.exists(HISTORY_FILE):
            os.remove(HISTORY_FILE)
    except:
        pass