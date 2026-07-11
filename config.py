# -*- coding: utf-8 -*-
"""
config.py — ការកំណត់ទាំងអស់សម្រាប់ Kairozen Game Topup Bot
កំណត់តម្លៃពិតតាមរយៈ Environment Variables (Render → Environment)
ឬតាមរយៈ Termux export មុនពេល run
"""
import os

# ===== Telegram =====
BOT_TOKEN = os.environ.get("BOT_TOKEN", "PUT_YOUR_BOT_TOKEN_HERE")
ADMIN_IDS = [8266854899]  # Phanna admin id (បន្ថែម admin ផ្សេងទៀតបានក្នុង list នេះ)

# ===== CamRapidPay KHQR =====
CAMRAPIDPAY_API_URL = "https://pay.camrapidpay.com/api/v1/khqr/create-payments"
CAMRAPIDPAY_CHECK_URL = "https://pay.camrapidpay.com/api/v1/khqr/check-transaction-api"
CAMRAPIDPAY_API_KEY = os.environ.get(
    "CAMRAPIDPAY_API_KEY",
    "d9f5828e6913f9fccb3b9b2368aee92312f2a17a2c091947f4beb7ea579a60f4",
)
SHOP_NAME = "Kairozen Store"
BAKONG_ACCOUNT = "phanna_van@bkrt"

# ===== Bay2Game (fulfillment provider) =====
# ⚠️ Endpoint ខាងក្រោមផ្អែកលើអ្វីដែលឃើញលើ landing page របស់ Bay2Game
# (https://bay2game.xyz/developer_docs) ។ ត្រូវទៅយក API key ពិត និងផ្ទៀងផ្ទាត់
# parameter ត្រឹមត្រូវ ដោយវាយ /profile ក្នុង @Bay2GameBot សិន រួចកែក្នុងឯកសារនេះ
# និង bay2game_api.py បើឈ្មោះ param មិនត្រូវ។
BAY2GAME_API_KEY = os.environ.get("BAY2GAME_API_KEY", "FBAC949DD2E7D7ECEF4C19B4")
BAY2GAME_BASE_URL = "https://api.bay2game.com"
BAY2GAME_CREATE_ORDER_URL = f"{BAY2GAME_BASE_URL}/create_orders"
BAY2GAME_CALLBACK_URL = os.environ.get("BAY2GAME_CALLBACK_URL", "")  # webhook receiver (Flask) ប្រសិនបើ deploy លើ Render

# ===== Files =====
ORDERS_FILE = os.environ.get("ORDERS_FILE", "orders.json")
PRODUCTS_FILE = os.environ.get("PRODUCTS_FILE", "products.json")

# ===== Payment polling =====
PAYMENT_CHECK_INTERVAL_SEC = 5
PAYMENT_TIMEOUT_SEC = 300  # 5 នាទី
