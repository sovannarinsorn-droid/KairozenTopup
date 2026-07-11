# -*- coding: utf-8 -*-
"""users_store.py — កត់ត្រា user ទាំងអស់ដែលធ្លាប់ចូល bot (សម្រាប់ admin panel: មើល users + broadcast)"""
import json
import os
import threading
from datetime import datetime
import config

USERS_FILE = os.environ.get("USERS_FILE", "users.json")
_lock = threading.Lock()


def _load():
    if not os.path.exists(USERS_FILE):
        return {}
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}


def _save(data):
    tmp = USERS_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, USERS_FILE)


def track_user(user_id, username=None, first_name=None):
    """ហៅរាល់ពេល user ធ្វើអ្វីមួយ (/start ។ល។) — កត់ត្រា first_seen/last_seen"""
    with _lock:
        data = _load()
        uid = str(user_id)
        now = datetime.now().isoformat()
        if uid not in data:
            data[uid] = {
                "user_id": user_id,
                "username": username or "",
                "first_name": first_name or "",
                "first_seen": now,
                "last_seen": now,
                "total_orders": 0,
                "total_spent_usd": 0,
                "is_blocked": False,
            }
        else:
            data[uid]["last_seen"] = now
            if username:
                data[uid]["username"] = username
            if first_name:
                data[uid]["first_name"] = first_name
        _save(data)


def track_purchase(user_id, amount_usd):
    with _lock:
        data = _load()
        uid = str(user_id)
        if uid not in data:
            data[uid] = {
                "user_id": user_id, "username": "", "first_name": "",
                "first_seen": datetime.now().isoformat(), "last_seen": datetime.now().isoformat(),
                "total_orders": 0, "total_spent_usd": 0, "is_blocked": False,
            }
        data[uid]["total_orders"] += 1
        data[uid]["total_spent_usd"] = round(data[uid]["total_spent_usd"] + amount_usd, 2)
        _save(data)


def get_user(user_id):
    data = _load()
    return data.get(str(user_id))


def get_all_users(limit=None):
    data = _load()
    users = list(data.values())
    users.sort(key=lambda u: u["last_seen"], reverse=True)
    return users[:limit] if limit else users


def count_users():
    return len(_load())


def search_users(query):
    """ស្វែងរកតាម user_id ឬ username (partial match)"""
    data = _load()
    q = query.strip().lstrip("@").lower()
    results = []
    for u in data.values():
        if q == str(u["user_id"]) or q in (u.get("username") or "").lower():
            results.append(u)
    return results
