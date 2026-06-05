import json
import os
import streamlit as st
from datetime import datetime

def _get_history_file():
    """Each user gets their own history file based on session ID."""
    session_id = st.runtime.scriptrunner.get_script_run_ctx().session_id
    safe_id    = session_id.replace("-", "")[:16]
    path       = f"/tmp/sitescore_history_{safe_id}.json"
    return path

def load_history():
    try:
        path = _get_history_file()
        if os.path.exists(path):
            with open(path, "r") as f:
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
        "mode":        result.get("mode", "single"),
    }
    # Remove duplicate address if exists
    history = [h for h in history
               if h["address"] != result["address"]]
    history.insert(0, entry)
    history = history[:50]
    try:
        path = _get_history_file()
        with open(path, "w") as f:
            json.dump(history, f)
    except:
        pass
    return entry

def clear_history():
    try:
        path = _get_history_file()
        if os.path.exists(path):
            os.remove(path)
    except:
        pass