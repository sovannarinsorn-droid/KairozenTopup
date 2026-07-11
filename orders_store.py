# -*- coding: utf-8 -*-
"""orders_store.py — កត់ត្រា order ទាំងអស់ (JSON file storage)"""
import json
import os
import threading
import uuid
from datetime import datetime
import config

_lock = threading.Lock()


def _load():
    if not os.path.exists(config.ORDERS_FILE):
        return {}
    try:
        with open(config.ORDERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}


def _save(data):
    tmp = config.ORDERS_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, config.ORDERS_FILE)


def new_order(user_id, username, game_key, game_name, package_label, price_usd,
              player_id, server_id, bay2game_product_code):
    order_id = uuid.uuid4().hex[:10]
    with _lock:
        data = _load()
        data[order_id] = {
            "order_id": order_id,
            "user_id": user_id,
            "username": username or "",
            "game_key": game_key,
            "game_name": game_name,
            "package_label": package_label,
            "price_usd": price_usd,
            "player_id": player_id,
            "server_id": server_id or "",
            "bay2game_product_code": bay2game_product_code,
            "status": "PENDING_PAYMENT",  # PENDING_PAYMENT -> PAID -> FULFILLED / FAILED
            "created_at": datetime.now().isoformat(),
            "paid_at": None,
            "fulfilled_at": None,
            "bay2game_response": None,
        }
        _save(data)
        return order_id


def update_status(order_id, status, **extra):
    with _lock:
        data = _load()
        if order_id not in data:
            return None
        data[order_id]["status"] = status
        if status == "PAID":
            data[order_id]["paid_at"] = datetime.now().isoformat()
        if status == "FULFILLED":
            data[order_id]["fulfilled_at"] = datetime.now().isoformat()
        for k, v in extra.items():
            data[order_id][k] = v
        _save(data)
        return data[order_id]


def get_order(order_id):
    data = _load()
    return data.get(order_id)


def get_user_orders(user_id, limit=10):
    data = _load()
    orders = [o for o in data.values() if str(o["user_id"]) == str(user_id)]
    orders.sort(key=lambda o: o["created_at"], reverse=True)
    return orders[:limit]


def get_all_orders(limit=50):
    data = _load()
    orders = list(data.values())
    orders.sort(key=lambda o: o["created_at"], reverse=True)
    return orders[:limit]
