# -*- coding: utf-8 -*-
"""
camrapidpay.py — KHQR payment via CamRapidPay (ដូចគម្រោង PVH TOPUP / Kairozen ចាស់)
"""
import requests
import config


def create_khqr_payment(amount_usd: float, description: str, ref_id: str):
    payload = {
        "amount": amount_usd,
        "currency": "USD",
        "description": description,
        "reference_id": ref_id,
        "shop_name": config.SHOP_NAME,
        "account": config.BAKONG_ACCOUNT,
    }
    headers = {
        "Authorization": f"Bearer {config.CAMRAPIDPAY_API_KEY}",
        "Content-Type": "application/json",
    }
    try:
        resp = requests.post(config.CAMRAPIDPAY_API_URL, json=payload, headers=headers, timeout=20)
        data = resp.json() if resp.content else {}
        return {"success": resp.status_code == 200, "raw": data}
    except requests.RequestException as e:
        return {"success": False, "raw": {}, "error": str(e)}


def check_transaction(ref_id: str):
    headers = {"Authorization": f"Bearer {config.CAMRAPIDPAY_API_KEY}"}
    try:
        resp = requests.get(
            config.CAMRAPIDPAY_CHECK_URL,
            params={"reference_id": ref_id},
            headers=headers,
            timeout=15,
        )
        data = resp.json() if resp.content else {}
        # ស្តង់ដារពីគម្រោងចាស់: data.get("status") == "PAID" / "SUCCESS"
        paid = str(data.get("status", "")).upper() in ("PAID", "SUCCESS", "COMPLETED")
        return {"success": resp.status_code == 200, "paid": paid, "raw": data}
    except requests.RequestException as e:
        return {"success": False, "paid": False, "raw": {}, "error": str(e)}
