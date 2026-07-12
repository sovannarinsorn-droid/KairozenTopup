# -*- coding: utf-8 -*-
"""
camrapidpay.py — KHQR payment via CamRapidPay
Format នេះចម្លងចេញពី phanna_premium_bot_V6_premium.py ដែលដំណើរការពិតប្រាកដ
(api_key ក្នុង JSON body, success field ក្នុង response body — មិនមែន Bearer header
ឬ HTTP status code ទេ)
"""
import logging
import requests
import config

logger = logging.getLogger("camrapidpay")
logging.basicConfig(level=logging.INFO)

_http = requests.Session()
_http.mount("https://", requests.adapters.HTTPAdapter(
    max_retries=requests.adapters.Retry(total=2, backoff_factor=0.5)
))


def create_khqr_payment(amount_usd: float, description: str, ref_id: str):
    payload = {
        "api_key": config.CAMRAPIDPAY_API_KEY,
        "amount": round(float(amount_usd), 2),
        "reference": ref_id,
        "webhook_url": config.CAMRAPIDPAY_WEBHOOK_URL,
    }
    try:
        resp = _http.post(
            config.CAMRAPIDPAY_API_URL,
            json=payload,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            timeout=15,
        )
        data = resp.json() if resp.content else {}
        ok = bool(data.get("success"))
        if not ok:
            logger.error(
                "CamRapidPay create_khqr_payment FAILED | ref=%s | desc=%s | status=%s | response=%s",
                ref_id, description, resp.status_code, data or resp.text,
            )
        else:
            logger.info("CamRapidPay create_khqr_payment OK | ref_id=%s", ref_id)
        return {
            "success": ok,
            "raw": data,
            "status_code": resp.status_code,
            "qr_code": data.get("qr_code", ""),
            "error": None if ok else (data.get("message") or data.get("error") or "Unknown API error"),
        }
    except requests.RequestException as e:
        logger.error("CamRapidPay create_khqr_payment EXCEPTION | ref=%s | %s", ref_id, e)
        return {"success": False, "raw": {}, "status_code": None, "qr_code": "", "error": str(e)}


def check_transaction(ref_id: str):
    try:
        resp = _http.get(
            config.CAMRAPIDPAY_CHECK_URL,
            params={"api_key": config.CAMRAPIDPAY_API_KEY, "reference": ref_id},
            headers={"Accept": "application/json"},
            timeout=10,
        )
        data = resp.json() if resp.content else {}
        paid = bool(data.get("success")) and str(data.get("status", "")).lower() in ("success", "paid")
        return {"success": bool(data.get("success")), "paid": paid, "raw": data}
    except requests.RequestException as e:
        logger.error("CamRapidPay check_transaction EXCEPTION | ref=%s | %s", ref_id, e)
        return {"success": False, "paid": False, "raw": {}, "error": str(e)}
