# -*- coding: utf-8 -*-
"""
config.py — ការកំណត់ទាំងអស់សម្រាប់ Kairozen Game Topup Bot
កំណត់តម្លៃពិតតាមរយៈ Environment Variables (Render → Environment)
ឬតាមរយៈ Termux export មុនពេល run
"""
import os

# ===== Telegram =====
BOT_TOKEN = os.environ.get("BOT_TOKEN", "PUT_YOUR_BOT_TOKEN_HERE")
ADMIN_IDS = [8266854899]

# ===== CamRapidPay KHQR =====
CAMRAPIDPAY_API_URL = "https://pay.camrapidpay.com/api/v1/khqr/create-payments"
CAMRAPIDPAY_CHECK_URL = "https://pay.camrapidpay.com/check-transaction-api"
CAMRAPIDPAY_API_KEY = os.environ.get(
    "CAMRAPIDPAY_API_KEY",
    "d9f5828e6913f9fccb3b9b2368aee92312f2a17a2c091947f4beb7ea579a60f4",
)
CAMRAPIDPAY_WEBHOOK_URL = os.environ.get(
    "CAMRAPIDPAY_WEBHOOK_URL", "https://pvhtopup.onrender.com/wh/khqr"
)
SHOP_NAME = "Kairozen Store"

# ===== Bay2Game (fulfillment provider) =====
BAY2GAME_API_KEY = os.environ.get("BAY2GAME_API_KEY", "FBAC949DD2E7D7ECEF4C19B4")
BAY2GAME_BASE_URL = "https://api.bay2game.com"
BAY2GAME_CREATE_ORDER_URL = f"{BAY2GAME_BASE_URL}/create_orders"
BAY2GAME_CALLBACK_URL = os.environ.get("BAY2GAME_CALLBACK_URL", "")

# ===== Files =====
ORDERS_FILE = os.environ.get("ORDERS_FILE", "orders.json")
PRODUCTS_FILE = os.environ.get("PRODUCTS_FILE", "products.json")

# ===== Payment polling =====
PAYMENT_CHECK_INTERVAL_SEC = 5
PAYMENT_TIMEOUT_SEC = 300
