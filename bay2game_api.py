# -*- coding: utf-8 -*-
"""
bay2game_api.py — Wrapper សម្រាប់ហៅ Bay2Game fulfillment API

⚠️ សំខាន់៖ ខ្ញុំបានឃើញតែ landing page នៃ Bay2Game (bay2game.xyz/developer_docs)
ដែល render ដោយ JavaScript ទើប field ដូចខាងក្រោមជា "best guess" ផ្អែកលើ
example ដែលបង្ហាញនៅលើគេហទំព័រ:

    POST https://api.bay2game.com/create_orders
    {
      "userid": "sample_game",
      "server_id": "",
      "product_code": "sample_item",
      "callback_url": "https://sampledomain.com/callback"
    }

ជំហានបន្ទាប់ត្រូវធ្វើ (Phanna)៖
 1. ចូល Telegram @Bay2GameBot វាយ /profile ដើម្បីទទួល API key
 2. សុំ/មើល full docs (product list endpoint, order status endpoint, auth header format)
 3. កែ BAY2GAME_API_KEY ក្នុង config.py + កែមុខងារខាងក្រោមប្រសិនបើ field name មិនត្រូវ
"""
import requests
import config


def create_order(userid: str, product_code: str, server_id: str = "", trx_ref: str = None):
    """
    ដាក់ order ទៅ Bay2Game ។ សម្រេចត្រឡប់ dict ស្រាប់ (success/raw) ។
    trx_ref ប្រើសម្រាប់ idempotency (ជៀសវាង order ដដែលៗ) — ដាក់ក្នុង callback_url query
    ឬកែតាម field ពិតដែល Bay2Game ត្រូវការ (ឧ. "ref_id") នៅពេលបានឯកសារពេញលេញ។
    """
    payload = {
        "userid": userid,
        "server_id": server_id or "",
        "product_code": product_code,
        "callback_url": config.BAY2GAME_CALLBACK_URL or "",
    }
    headers = {
        "Authorization": f"Bearer {config.BAY2GAME_API_KEY}",
        "Content-Type": "application/json",
    }
    try:
        resp = requests.post(
            config.BAY2GAME_CREATE_ORDER_URL,
            json=payload,
            headers=headers,
            timeout=20,
        )
        data = resp.json() if resp.content else {}
        return {
            "success": resp.status_code == 200 and data.get("status", True),
            "http_status": resp.status_code,
            "raw": data,
        }
    except requests.RequestException as e:
        return {"success": False, "http_status": None, "raw": {}, "error": str(e)}


def check_order_status(order_id: str):
    """
    TODO: កែ URL ពិតនៅពេលបានឯកសារ Bay2Game ពេញលេញ។
    សន្មតថាមាន endpoint ប្រហាក់ប្រហែល /order_status ។
    """
    headers = {"Authorization": f"Bearer {config.BAY2GAME_API_KEY}"}
    try:
        resp = requests.get(
            f"{config.BAY2GAME_BASE_URL}/order_status",
            params={"order_id": order_id},
            headers=headers,
            timeout=15,
        )
        data = resp.json() if resp.content else {}
        return {"success": resp.status_code == 200, "raw": data}
    except requests.RequestException as e:
        return {"success": False, "raw": {}, "error": str(e)}
