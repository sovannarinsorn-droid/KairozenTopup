# -*- coding: utf-8 -*-
"""
=====================================================================
 Kairozen Diamond Topup Bot — Single File Version (Auto Payment + Auto Topup)
 ហ្គេម៖ Mobile Legends, Free Fire, PUBG Mobile
 ទូទាត់ប្រាក់៖ CamRapidPay / CamRapidX (Bakong KHQR) — ត្រូវបានពិនិត្យស្វ័យប្រវត្តិ
 តម្លៃ Diamond៖ ទាញពី Bay2Game.com API + Admin Price Override
 Topup៖ បញ្ជូនទៅ Bay2Game.com ដោយស្វ័យប្រវត្តិពេលទូទាត់ប្រាក់ជោគជ័យ
=====================================================================

តម្រូវការ (requirements.txt):
    python-telegram-bot[job-queue]==21.4
    requests

Run:
    export BOT_TOKEN="xxxx"
    python bot.py
"""

import os
import json
import time
import uuid
import logging
import threading

import requests
from flask import Flask
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup, KeyboardButton, MessageEntity,
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, ConversationHandler, filters,
)

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
log = logging.getLogger("topup_bot")

# ============================================================
# 1) CONFIG — កែត្រង់នេះឲ្យត្រូវនឹងគណនីអ្នក
# ============================================================

BOT_TOKEN = os.getenv("BOT_TOKEN", "PUT_YOUR_TELEGRAM_BOT_TOKEN_HERE")

ADMIN_IDS = [
    8266854899,  # <-- ដូរជា Telegram user id របស់ Admin
]

# --- Bay2Game.com (ប្រភពតម្លៃ Diamond + ការបញ្ជូន Topup) ---
BAY2GAME_BASE_URL = os.getenv("BAY2GAME_BASE_URL", "https://bay2game.com/api")
BAY2GAME_API_KEY = os.getenv("BAY2GAME_API_KEY", "PUT_BAY2GAME_API_KEY_HERE")
BAY2GAME_CATALOG_ENDPOINT = "/products"
BAY2GAME_ORDER_ENDPOINT = "/order"          # ដាក់ Order Topup ពិតប្រាកដ
BAY2GAME_STATUS_ENDPOINT = "/order/status"  # ពិនិត្យស្ថានភាព Topup (delivered/failed)

# --- CamRapidPay / CamRapidX (KHQR) ---
CAMRAPID_BASE_URL = os.getenv("CAMRAPID_BASE_URL", "https://api.camrapidpay.com")
CAMRAPID_API_KEY = os.getenv("CAMRAPID_API_KEY", "PUT_CAMRAPIDPAY_API_KEY_HERE")
CAMRAPID_MERCHANT_ID = os.getenv("CAMRAPID_MERCHANT_ID", "PUT_MERCHANT_ID_HERE")
CAMRAPID_CREATE_QR_ENDPOINT = "/khqr/create"
CAMRAPID_CHECK_PAYMENT_ENDPOINT = "/khqr/check"

# --- Auto-payment polling ---
PAYMENT_POLL_INTERVAL_SECONDS = 5       # ថេរវេលារវាងការពិនិត្យនីមួយៗ
PAYMENT_POLL_TIMEOUT_SECONDS = 10 * 60  # បោះបង់ការរង់ចាំបន្ទាប់ពី 10 នាទី

# --- Render deployment ---
PORT = int(os.getenv("PORT", "10000"))
# Render provides this automatically on Web Services (e.g. https://your-app.onrender.com)
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL", "")
SELF_PING_INTERVAL_SECONDS = 10 * 60  # ping ខ្លួនឯងរាល់ 10 នាទី កុំឲ្យ Render free tier គេង

# --- ហ្គេមដែលគាំទ្រ ---
GAMES = {
    "mlbb":  {"name": "Mobile Legends: Bang Bang", "emoji": "🎮", "fields": ["User ID", "Zone ID"]},
    "ff":    {"name": "Free Fire",                 "emoji": "🔥", "fields": ["Player ID"]},
    "pubgm": {"name": "PUBG Mobile",               "emoji": "🪖", "fields": ["Player ID"]},
}

# ============================================================
# PREMIUM EMOJI — តម្រូវការ Telegram Premium នៅលើគណនីម្ចាស់ Bot
# ============================================================
# ⚠️ សំខាន់៖ Custom/Premium emoji នៅលើ button (icon_custom_emoji_id) និងក្នុង text (entities)
# ដំណើរការបានលុះត្រាតែ "ម្ចាស់ Bot" (គណនីដែលបង្កើត bot តាម @BotFather) មាន Telegram Premium
# សកម្មភាព ឬបានទិញ username បន្ថែមតាម Fragment។ បើគ្មាន Premium ទេ Telegram នឹងមិនបង្ហាញ
# custom emoji នោះទេ (fallback ទៅ regular emoji វិញ ឬមិនបង្ហាញអ្វីសោះ)។
#
# របៀបយក custom_emoji_id៖
#   1. បើក Telegram (គណនីណាក៏បាន) → រកឃើញ Premium emoji ណាមួយ (ក្នុង emoji panel មាន 🔒/⭐)
#   2. ផ្ញើ emoji នោះទៅ bot ជំនួយ ដូចជា @idcustomemojibot ឬសរសេរ bot តូចមួយ
#      ប្រើ MessageHandler ចាប់ entities ប្រភេទ "custom_emoji" ដើម្បីទាញ custom_emoji_id
#   3. ចម្លង ID (លេខវែងៗ ដូចជា "5368324170671202286") មកដាក់ខាងក្រោម
#
# USE_PREMIUM_EMOJI = False → Bot ប្រើ regular emoji ធម្មតា (សុវត្ថិភាព មិនចាំបាច់ Premium)
USE_PREMIUM_EMOJI = os.getenv("USE_PREMIUM_EMOJI", "false").lower() == "true"

PREMIUM_EMOJI_IDS = {
    "diamond":  "PUT_CUSTOM_EMOJI_ID_HERE",   # ឧ. package Diamond premium icon
    "success":  "PUT_CUSTOM_EMOJI_ID_HERE",   # ✅ premium checkmark
    "fire":     "PUT_CUSTOM_EMOJI_ID_HERE",   # 🔥 premium fire (Free Fire)
    "game":     "PUT_CUSTOM_EMOJI_ID_HERE",   # 🎮 premium controller (MLBB)
    "helmet":   "PUT_CUSTOM_EMOJI_ID_HERE",   # 🪖 premium helmet (PUBGM)
    "money":    "PUT_CUSTOM_EMOJI_ID_HERE",   # 💰 premium coin/money
    "warning":  "PUT_CUSTOM_EMOJI_ID_HERE",   # ⚠️ premium warning
    "admin":    "PUT_CUSTOM_EMOJI_ID_HERE",   # 🛠 premium tools
}

# Button colors (Bot API 9.4+, PTB v22.7+) — មិនតម្រូវ Premium ទេ សុវត្ថិភាព 100%
BTN_STYLE_SUCCESS = "success"  # បៃតង — សម្រាប់សកម្មភាពវិជ្ជមាន (បញ្ជាក់ ការទូទាត់)
BTN_STYLE_DANGER = "danger"    # ក្រហម — សម្រាប់សកម្មភាពបោះបង់/លុប
BTN_STYLE_PRIMARY = "primary"  # ខៀវ — សម្រាប់សកម្មភាពសំខាន់

# --- Files (JSON persistence) ---
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
CATALOG_FILE = os.path.join(DATA_DIR, "catalog.json")
PRICES_FILE = os.path.join(DATA_DIR, "prices.json")
ORDERS_FILE = os.path.join(DATA_DIR, "orders.json")
USERS_FILE = os.path.join(DATA_DIR, "users.json")

CATALOG_REFRESH_SECONDS = 15 * 60

# Conversation states
ASK_FIELD, CONFIRM_ORDER, ADMIN_SET_PRICE = range(3)

_lock = threading.Lock()

# --- Reply Keyboards (persistent bottom menu) ---
BTN_BUY = "🎮 ទិញ Diamond"
BTN_MY_ORDERS = "📦 ការបញ្ជាទិញរបស់ខ្ញុំ"
BTN_HELP = "❓ ជំនួយ"
BTN_ADMIN = "🛠 Admin Panel"

def emoji_id(key: str):
    """ត្រឡប់ custom_emoji_id បើបានបើក + បានកំណត់ ID ពិត បើអត់ ត្រឡប់ None (fallback ធម្មតា)"""
    if not USE_PREMIUM_EMOJI:
        return None
    val = PREMIUM_EMOJI_IDS.get(key)
    if not val or val.startswith("PUT_"):
        return None
    return val


def build_keyboard_button(text: str, icon_key: str = None):
    """KeyboardButton ជាមួយ icon_custom_emoji_id ជម្រើស (តម្រូវ Telegram Premium)"""
    icon = emoji_id(icon_key)
    if icon:
        return KeyboardButton(text, icon_custom_emoji_id=icon)
    return KeyboardButton(text)


MAIN_REPLY_KEYBOARD = ReplyKeyboardMarkup(
    [[build_keyboard_button(BTN_BUY, "diamond"), build_keyboard_button(BTN_MY_ORDERS)],
     [build_keyboard_button(BTN_HELP)]],
    resize_keyboard=True,
)

ADMIN_REPLY_KEYBOARD = ReplyKeyboardMarkup(
    [[build_keyboard_button(BTN_BUY, "diamond"), build_keyboard_button(BTN_MY_ORDERS)],
     [build_keyboard_button(BTN_HELP), build_keyboard_button(BTN_ADMIN, "admin")]],
    resize_keyboard=True,
)


def reply_keyboard_for(user_id: int):
    return ADMIN_REPLY_KEYBOARD if user_id in ADMIN_IDS else MAIN_REPLY_KEYBOARD


# ============================================================
# PREMIUM EMOJI HELPERS (continued)
# ============================================================


def styled_button(text: str, callback_data: str, style: str = None, icon_key: str = None):
    """
    បង្កើត InlineKeyboardButton ដែលអាចមាន style ពណ៌ (danger/success/primary — មិនតម្រូវ Premium)
    និង icon_custom_emoji_id (តម្រូវ Telegram Premium នៅលើគណនីម្ចាស់ Bot)
    """
    kwargs = {}
    if style:
        kwargs["style"] = style
    icon = emoji_id(icon_key) if icon_key else None
    if icon:
        kwargs["icon_custom_emoji_id"] = icon
    return InlineKeyboardButton(text, callback_data=callback_data, **kwargs)


def premium_text_entities(text: str, emoji_char: str, icon_key: str):
    """
    បង្កើត MessageEntity(CUSTOM_EMOJI) ដើម្បីប្តូររូប emoji ធម្មតា (មួយក្នុង text)
    ទៅជា Premium custom emoji។ emoji_char ត្រូវតែជា emoji ដែលមាននៅក្នុង text ជាក់ស្តែង
    (Telegram តម្រូវឲ្យ entity រុំគ្រប exactly regular emoji មួយ)។
    ត្រឡប់ [] បើ premium emoji មិនបានបើក/កំណត់ (Telegram នឹងបង្ហាញ text ធម្មតា)
    """
    icon = emoji_id(icon_key)
    if not icon:
        return []
    idx = text.find(emoji_char)
    if idx == -1:
        return []
    # គណនា UTF-16 length (Telegram entities គិតជា UTF-16 code units)
    length = len(emoji_char.encode("utf-16-le")) // 2
    offset = len(text[:idx].encode("utf-16-le")) // 2
    return [MessageEntity(type=MessageEntity.CUSTOM_EMOJI, offset=offset, length=length, custom_emoji_id=icon)]


# ============================================================
# 2) STORAGE HELPERS
# ============================================================


def load_json(path, default):
    with _lock:
        if not os.path.exists(path):
            return default
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return default


def save_json(path, data):
    with _lock:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, path)


# ============================================================
# 3) CATALOG — Bay2Game.com API + Admin Price Override
# ============================================================

_last_fetch_time = 0


def fetch_catalog_from_api():
    """
    TODO: កែ mapping ខាងក្រោមឲ្យត្រូវនឹង response ពិតរបស់ Bay2Game.com
    សន្មតថា response = {"data": [{"game": "mlbb", "code": "...", "name": "...", "price": 2500}, ...]}
    """
    url = f"{BAY2GAME_BASE_URL}{BAY2GAME_CATALOG_ENDPOINT}"
    headers = {"Authorization": f"Bearer {BAY2GAME_API_KEY}"}
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        raw = resp.json()
    except Exception as e:
        log.warning(f"Bay2Game API fetch failed: {e}. Using cached catalog.json")
        return load_json(CATALOG_FILE, default={})

    catalog = {}
    for item in raw.get("data", []):
        game = item.get("game")
        if game not in GAMES:
            continue
        catalog.setdefault(game, []).append({
            "code": item.get("code"),
            "label": item.get("name"),
            "cost": float(item.get("price", 0)),
        })

    if catalog:
        save_json(CATALOG_FILE, catalog)
    return catalog or load_json(CATALOG_FILE, default={})


def get_catalog(force_refresh=False):
    global _last_fetch_time
    now = time.time()
    if force_refresh or (now - _last_fetch_time) > CATALOG_REFRESH_SECONDS:
        catalog = fetch_catalog_from_api()
        _last_fetch_time = now
        return catalog
    return load_json(CATALOG_FILE, default={})


def get_packages_for_game(game_key):
    catalog = get_catalog()
    packages = catalog.get(game_key, [])
    overrides = load_json(PRICES_FILE, default={}).get(game_key, {})
    result = []
    for pkg in packages:
        price = overrides.get(pkg["code"], pkg["cost"])
        result.append({**pkg, "price": price})
    return result


def find_package(game_key, package_code):
    for pkg in get_packages_for_game(game_key):
        if pkg["code"] == package_code:
            return pkg
    return None


def set_price_override(game_key, package_code, new_price):
    overrides = load_json(PRICES_FILE, default={})
    overrides.setdefault(game_key, {})[package_code] = new_price
    save_json(PRICES_FILE, overrides)


# ============================================================
# 4) PAYMENT — CamRapidPay / CamRapidX (KHQR)
# ============================================================


def create_khqr(order_id, amount, currency="KHR"):
    """TODO: កែតាម API spec ពិតរបស់ CamRapidPay/CamRapidX"""
    url = f"{CAMRAPID_BASE_URL}{CAMRAPID_CREATE_QR_ENDPOINT}"
    headers = {"Authorization": f"Bearer {CAMRAPID_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "merchant_id": CAMRAPID_MERCHANT_ID,
        "order_id": order_id,
        "amount": amount,
        "currency": currency,
    }
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        return {
            "success": True,
            "qr_string": data.get("qr_string", ""),
            "qr_image_url": data.get("qr_image_url", ""),
            "md5": data.get("md5", ""),
        }
    except Exception as e:
        log.error(f"create_khqr failed: {e}")
        return {"success": False, "error": str(e)}


def check_payment(order_id, md5=""):
    url = f"{CAMRAPID_BASE_URL}{CAMRAPID_CHECK_PAYMENT_ENDPOINT}"
    headers = {"Authorization": f"Bearer {CAMRAPID_API_KEY}"}
    params = {"order_id": order_id, "md5": md5}
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        resp.raise_for_status()
        status = resp.json().get("status", "pending")
        return {"paid": status.lower() in ("paid", "success", "completed"), "status": status}
    except Exception as e:
        log.error(f"check_payment failed: {e}")
        return {"paid": False, "status": "error"}


# ============================================================
# 5) BAY2GAME AUTO-TOPUP DELIVERY
# ============================================================


def submit_topup_to_bay2game(order: dict) -> dict:
    """
    ហៅ Bay2Game.com API ដើម្បីធ្វើ Topup ពិតប្រាកដទៅគណនីហ្គេមរបស់អ្នកទិញ
    TODO: កែ payload/response mapping ខាងក្រោមឲ្យត្រូវនឹង API spec ពិត
    Return: {"success": bool, "reference": str, "error": str}
    """
    url = f"{BAY2GAME_BASE_URL}{BAY2GAME_ORDER_ENDPOINT}"
    headers = {"Authorization": f"Bearer {BAY2GAME_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "game": order["game"],
        "package_code": order["package_code"],
        "target": order["game_fields"],
        "reference_id": order["order_id"],
    }
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        ok = data.get("status", "").lower() in ("success", "ok", "delivered", "processing")
        return {"success": ok, "reference": data.get("reference", ""), "error": data.get("message", "")}
    except Exception as e:
        log.error(f"submit_topup_to_bay2game failed: {e}")
        return {"success": False, "reference": "", "error": str(e)}


# ============================================================
# 6) ORDERS
# ============================================================


def create_order(user_id, game_key, package_code, price, game_fields):
    orders = load_json(ORDERS_FILE, default={})
    order_id = uuid.uuid4().hex[:10].upper()
    order = {
        "order_id": order_id,
        "user_id": user_id,
        "game": game_key,
        "package_code": package_code,
        "price": price,
        "game_fields": game_fields,
        "status": "pending_payment",
        "created_at": time.time(),
        "paid_at": None,
        "delivered_at": None,
        "md5": "",
        "qr_message_id": None,
        "qr_chat_id": None,
    }
    orders[order_id] = order
    save_json(ORDERS_FILE, orders)
    return order


def get_order(order_id):
    return load_json(ORDERS_FILE, default={}).get(order_id)


def update_order(order_id, **kwargs):
    orders = load_json(ORDERS_FILE, default={})
    if order_id in orders:
        orders[order_id].update(kwargs)
        save_json(ORDERS_FILE, orders)
    return orders.get(order_id)


# ============================================================
# 7) USERS (for broadcast)
# ============================================================


def register_user(user_id, username="", full_name=""):
    users = load_json(USERS_FILE, default={})
    key = str(user_id)
    users[key] = {
        "user_id": user_id,
        "username": username or users.get(key, {}).get("username", ""),
        "full_name": full_name or users.get(key, {}).get("full_name", ""),
        "first_seen": users.get(key, {}).get("first_seen", time.time()),
    }
    save_json(USERS_FILE, users)


def get_all_user_ids():
    return [int(uid) for uid in load_json(USERS_FILE, default={}).keys()]


def is_admin(user_id):
    return user_id in ADMIN_IDS


# ============================================================
# 8) AUTO-PAYMENT + AUTO-TOPUP CORE LOGIC (shared by job + manual button)
# ============================================================


async def finalize_paid_order(order_id: str, context: ContextTypes.DEFAULT_TYPE):
    """ត្រូវហៅពេលដឹងច្បាស់ថា order បានទូទាត់ប្រាក់ -> ធ្វើ auto-topup -> notify"""
    order = get_order(order_id)
    if not order or order["status"] != "pending_payment":
        return

    update_order(order_id, status="paid", paid_at=time.time())
    user_id = order["user_id"]

    try:
        await context.bot.send_message(
            user_id,
            f"✅ ការទូទាត់ប្រាក់ជោគជ័យ! លេខការបញ្ជាទិញ `{order_id}`\n"
            "⏳ កំពុងបញ្ចូល Diamond ទៅគណនីរបស់អ្នកដោយស្វ័យប្រវត្តិ...",
            parse_mode=ParseMode.MARKDOWN,
        )
    except Exception:
        pass

    result = submit_topup_to_bay2game(order)
    if result["success"]:
        update_order(order_id, status="delivered", delivered_at=time.time())
        try:
            await context.bot.send_message(
                user_id,
                f"🎉 *Topup ជោគជ័យ!*\nលេខការបញ្ជាទិញ៖ `{order_id}`\n"
                f"Diamond ត្រូវបានបញ្ចូលទៅគណនីរបស់អ្នករួចរាល់។\nសូមអរគុណ! 🙏",
                parse_mode=ParseMode.MARKDOWN,
            )
        except Exception:
            pass
    else:
        update_order(order_id, status="failed")
        try:
            await context.bot.send_message(
                user_id,
                f"⚠️ ការទូទាត់ប្រាក់ជោគជ័យ ប៉ុន្តែ Topup ស្វ័យប្រវត្តិបរាជ័យ។\n"
                f"លេខការបញ្ជាទិញ៖ `{order_id}`\n"
                "Admin នឹងធ្វើការឲ្យអ្នកដោយដៃក្នុងពេលឆាប់ៗនេះ សូមអត់ធ្មត់។",
                parse_mode=ParseMode.MARKDOWN,
            )
        except Exception:
            pass

    status_txt = "✅ Delivered" if result["success"] else f"❌ Topup FAILED: {result.get('error')}"
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(
                admin_id,
                f"💰 Order paid: `{order_id}`\n"
                f"Game: {order['game']} | Price: {order['price']:,.0f} ៛\n"
                f"Fields: {order['game_fields']}\n"
                f"Topup status: {status_txt}",
                parse_mode=ParseMode.MARKDOWN,
            )
        except Exception:
            pass


async def poll_payment_job(context: ContextTypes.DEFAULT_TYPE):
    """JobQueue callback — ពិនិត្យស្ថានភាពទូទាត់ប្រាក់ដោយស្វ័យប្រវត្តិរៀងរាល់ N វិនាទី"""
    job = context.job
    order_id = job.data["order_id"]
    order = get_order(order_id)

    if not order or order["status"] != "pending_payment":
        job.schedule_removal()
        return

    if time.time() - order["created_at"] > PAYMENT_POLL_TIMEOUT_SECONDS:
        job.schedule_removal()
        try:
            await context.bot.send_message(
                order["user_id"],
                f"⌛ QR ទូទាត់ប្រាក់សម្រាប់ការបញ្ជាទិញ `{order_id}` បានផុតកំណត់ពេល។\n"
                "សូម /start ម្តងទៀត ដើម្បីទិញឡើងវិញ។",
                parse_mode=ParseMode.MARKDOWN,
            )
        except Exception:
            pass
        return

    result = check_payment(order_id, order.get("md5", ""))
    if result["paid"]:
        job.schedule_removal()
        await finalize_paid_order(order_id, context)


def schedule_payment_polling(context: ContextTypes.DEFAULT_TYPE, order_id: str):
    """ចាប់ផ្តើម auto-check ការទូទាត់ប្រាក់ភ្លាមៗបន្ទាប់ពីបង្កើត QR"""
    context.job_queue.run_repeating(
        poll_payment_job,
        interval=PAYMENT_POLL_INTERVAL_SECONDS,
        first=PAYMENT_POLL_INTERVAL_SECONDS,
        data={"order_id": order_id},
        name=f"poll_{order_id}",
    )


# ============================================================
# 9) USER HANDLERS (Khmer UI)
# ============================================================


async def send_game_menu(chat_id, context, edit_query=None):
    icon_map = {"mlbb": "game", "ff": "fire", "pubgm": "helmet"}
    keyboard = [
        [styled_button(f"{g['emoji']} {g['name']}", f"game:{key}", icon_key=icon_map.get(key))]
        for key, g in GAMES.items()
    ]
    text = "🎮 សូមជ្រើសរើសហ្គេមដែលអ្នកចង់បញ្ចូល Diamond ខាងក្រោម៖"
    if edit_query:
        await edit_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await context.bot.send_message(chat_id, text, reply_markup=InlineKeyboardMarkup(keyboard))


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    register_user(user.id, user.username or "", user.full_name or "")

    await update.message.reply_text(
        f"👋 សួស្តី {user.first_name}!\n\n"
        "🎮 សូមស្វាគមន៍មកកាន់ *Diamond Topup Bot*\n"
        "ការទូទាត់ប្រាក់ និង Topup ត្រូវបានធ្វើដោយស្វ័យប្រវត្តិ! ⚡️",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=reply_keyboard_for(user.id),
    )
    await send_game_menu(update.effective_chat.id, context)


async def game_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    game_key = query.data.split(":")[1]
    game = GAMES[game_key]
    context.user_data["game_key"] = game_key

    packages = get_packages_for_game(game_key)
    if not packages:
        await query.edit_message_text(
            "⚠️ បច្ចុប្បន្នមិនមានទិន្នន័យតម្លៃ Diamond សម្រាប់ហ្គេមនេះទេ។\n"
            "សូមព្យាយាមម្តងទៀតពេលក្រោយ ឬទាក់ទង Admin។"
        )
        return

    keyboard = [
        [styled_button(
            f"{p['label']} — {p['price']:,.0f} ៛",
            f"pkg:{p['code']}",
            icon_key="diamond",
        )]
        for p in packages
    ]
    keyboard.append([InlineKeyboardButton("⬅️ ត្រឡប់ក្រោយ", callback_data="back_to_games")])

    await query.edit_message_text(
        f"{game['emoji']} *{game['name']}*\n\nសូមជ្រើសរើសកញ្ចប់ Diamond៖",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def back_to_games(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await send_game_menu(update.effective_chat.id, context, edit_query=query)


async def package_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    package_code = query.data.split(":")[1]
    game_key = context.user_data.get("game_key")
    pkg = find_package(game_key, package_code)

    if not pkg:
        await query.edit_message_text("⚠️ រកមិនឃើញកញ្ចប់នេះទេ សូមចាប់ផ្តើមម្តងទៀត /start")
        return ConversationHandler.END

    context.user_data["package"] = pkg
    context.user_data["input_values"] = {}
    context.user_data["field_index"] = 0

    fields = GAMES[game_key]["fields"]
    await query.edit_message_text(
        f"✅ អ្នកបានជ្រើសរើស៖ *{pkg['label']}* — {pkg['price']:,.0f} ៛\n\n"
        f"សូមបញ្ចូល *{fields[0]}* របស់អ្នក៖",
        parse_mode=ParseMode.MARKDOWN,
    )
    return ASK_FIELD


async def field_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    game_key = context.user_data.get("game_key")
    fields = GAMES[game_key]["fields"]
    idx = context.user_data.get("field_index", 0)
    value = update.message.text.strip()

    context.user_data["input_values"][fields[idx]] = value
    idx += 1
    context.user_data["field_index"] = idx

    if idx < len(fields):
        await update.message.reply_text(f"សូមបញ្ចូល *{fields[idx]}*៖", parse_mode=ParseMode.MARKDOWN)
        return ASK_FIELD

    pkg = context.user_data["package"]
    values = context.user_data["input_values"]
    details = "\n".join([f"• {k}: `{v}`" for k, v in values.items()])

    keyboard = [
        [styled_button("✅ បញ្ជាក់ និងទូទាត់ប្រាក់", "confirm_order", style=BTN_STYLE_SUCCESS, icon_key="success")],
        [styled_button("❌ បោះបង់", "cancel_order", style=BTN_STYLE_DANGER)],
    ]
    await update.message.reply_text(
        f"🧾 *សូមពិនិត្យព័ត៌មានការបញ្ជាទិញ*\n\n"
        f"ហ្គេម៖ {GAMES[game_key]['name']}\n"
        f"កញ្ចប់៖ {pkg['label']}\n"
        f"តម្លៃ៖ *{pkg['price']:,.0f} ៛*\n"
        f"{details}\n\n"
        "តើត្រឹមត្រូវទេ?",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return CONFIRM_ORDER


async def confirm_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    game_key = context.user_data["game_key"]
    pkg = context.user_data["package"]
    values = context.user_data["input_values"]

    order = create_order(user_id, game_key, pkg["code"], pkg["price"], values)

    await query.edit_message_text("⏳ កំពុងបង្កើត KHQR សម្រាប់ទូទាត់ប្រាក់...")

    qr = create_khqr(order["order_id"], pkg["price"])
    if not qr.get("success"):
        await query.edit_message_text(
            "❌ មិនអាចបង្កើត QR ទូទាត់ប្រាក់បានទេ សូមព្យាយាមម្តងទៀត ឬទាក់ទង Admin។\n"
            f"លេខការបញ្ជាទិញ៖ `{order['order_id']}`",
            parse_mode=ParseMode.MARKDOWN,
        )
        return ConversationHandler.END

    update_order(order["order_id"], md5=qr.get("md5", ""))

    caption = (
        f"💳 *សូមស្កេន KHQR ខាងក្រោមដើម្បីទូទាត់ប្រាក់*\n\n"
        f"លេខការបញ្ជាទិញ៖ `{order['order_id']}`\n"
        f"ចំនួនទឹកប្រាក់៖ *{pkg['price']:,.0f} ៛*\n\n"
        "⚡️ ប្រព័ន្ធនឹងពិនិត្យ និង Topup ជូនអ្នកដោយស្វ័យប្រវត្តិភ្លាមៗ បន្ទាប់ពីទូទាត់ប្រាក់ចប់\n"
        "(មិនចាំបាច់ចុចអ្វីទៀតទេ គ្រាន់តែស្កេន ហើយរង់ចាំ)"
    )
    keyboard = [[styled_button("🔄 ពិនិត្យឥឡូវនេះ", f"check_pay:{order['order_id']}", style=BTN_STYLE_PRIMARY)]]

    if qr.get("qr_image_url"):
        msg = await context.bot.send_photo(
            chat_id=user_id, photo=qr["qr_image_url"], caption=caption,
            parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard),
        )
    else:
        msg = await context.bot.send_message(
            chat_id=user_id,
            text=f"{caption}\n\nKHQR string:\n`{qr.get('qr_string', 'N/A')}`",
            parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard),
        )

    update_order(order["order_id"], qr_message_id=msg.message_id, qr_chat_id=msg.chat_id)

    schedule_payment_polling(context, order["order_id"])

    context.user_data.clear()
    return ConversationHandler.END


async def check_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ប៊ូតុង Manual fallback — auto polling ជា job រត់ផ្ទាល់នៅផ្ទៃខាងក្រោយស្រាប់"""
    query = update.callback_query
    order_id = query.data.split(":")[1]
    order = get_order(order_id)
    if not order:
        await query.answer("⚠️ រកមិនឃើញការបញ្ជាទិញនេះទេ", show_alert=True)
        return

    if order["status"] != "pending_payment":
        await query.answer(f"ស្ថានភាពបច្ចុប្បន្ន៖ {order['status']}", show_alert=True)
        return

    await query.answer("កំពុងពិនិត្យ...")
    result = check_payment(order_id, order.get("md5", ""))
    if result["paid"]:
        await finalize_paid_order(order_id, context)
    else:
        await query.answer("⏳ មិនទាន់ទទួលបានការទូទាត់ប្រាក់នៅឡើយទេ ប្រព័ន្ធកំពុងពិនិត្យស្វ័យប្រវត្តិផងដែរ", show_alert=True)


async def my_orders_msg(chat_id, user_id, context):
    orders = [o for o in load_json(ORDERS_FILE, default={}).values() if o["user_id"] == user_id]
    if not orders:
        await context.bot.send_message(chat_id, "📭 អ្នកមិនទាន់មានការបញ្ជាទិញនៅឡើយទេ។")
        return
    lines = ["📦 *ការបញ្ជាទិញរបស់អ្នក*\n"]
    for o in orders[-10:]:
        lines.append(
            f"• `{o['order_id']}` — {GAMES.get(o['game'], {}).get('name', o['game'])} "
            f"— {o['price']:,.0f} ៛ — {o['status']}"
        )
    await context.bot.send_message(chat_id, "\n".join(lines), parse_mode=ParseMode.MARKDOWN)


async def my_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await my_orders_msg(query.message.chat_id, query.from_user.id, context)


async def cancel_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data.clear()
    await query.edit_message_text("❌ ការបញ្ជាទិញត្រូវបានបោះបង់។ វាយ /start ដើម្បីចាប់ផ្តើមម្តងទៀត។")
    return ConversationHandler.END


async def cancel_conv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("❌ បានបោះបង់។ វាយ /start ដើម្បីចាប់ផ្តើមម្តងទៀត។")
    return ConversationHandler.END


# ============================================================
# 10) ADMIN HANDLERS
# ============================================================


async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    keyboard = [
        [styled_button("🔄 Refresh Catalog", "admin:refresh_catalog", style=BTN_STYLE_PRIMARY)],
        [styled_button("💵 កំណត់តម្លៃ (Set Price)", "admin:set_price", icon_key="money")],
        [styled_button("📊 ស្ថិតិការបញ្ជាទិញ", "admin:stats")],
        [styled_button("📢 Broadcast", "admin:broadcast", style=BTN_STYLE_DANGER)],
    ]
    await update.message.reply_text(
        "🛠 *Admin Panel*", parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not is_admin(query.from_user.id):
        await query.answer("⛔ អ្នកមិនមែនជា Admin ទេ", show_alert=True)
        return
    await query.answer()
    action = query.data.split(":")[1]

    if action == "refresh_catalog":
        catalog = get_catalog(force_refresh=True)
        total = sum(len(v) for v in catalog.values())
        await query.edit_message_text(f"✅ បានទាញ Catalog ថ្មីពី Bay2Game.com — សរុប {total} packages")

    elif action == "stats":
        orders = list(load_json(ORDERS_FILE, default={}).values())
        paid = [o for o in orders if o["status"] in ("paid", "delivered")]
        delivered = [o for o in orders if o["status"] == "delivered"]
        failed = [o for o in orders if o["status"] == "failed"]
        revenue = sum(o["price"] for o in paid)
        users_count = len(get_all_user_ids())
        await query.edit_message_text(
            f"📊 *ស្ថិតិ*\n\n"
            f"👥 អ្នកប្រើប្រាស់៖ {users_count}\n"
            f"🧾 ការបញ្ជាទិញសរុប៖ {len(orders)}\n"
            f"✅ បានទូទាត់ប្រាក់៖ {len(paid)}\n"
            f"🎉 Topup ជោគជ័យ (Auto)៖ {len(delivered)}\n"
            f"❌ Topup បរាជ័យ៖ {len(failed)}\n"
            f"💰 ចំណូលសរុប៖ {revenue:,.0f} ៛",
            parse_mode=ParseMode.MARKDOWN,
        )

    elif action == "broadcast":
        context.user_data["awaiting_broadcast"] = True
        await query.edit_message_text("📢 សូមផ្ញើសារដែលអ្នកចង់ Broadcast ទៅអ្នកប្រើប្រាស់ទាំងអស់៖")

    elif action == "set_price":
        keyboard = [
            [InlineKeyboardButton(f"{g['emoji']} {g['name']}", callback_data=f"admin_setprice_game:{key}")]
            for key, g in GAMES.items()
        ]
        await query.edit_message_text("ជ្រើសរើសហ្គេមដើម្បីកំណត់តម្លៃ៖", reply_markup=InlineKeyboardMarkup(keyboard))


async def admin_setprice_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    game_key = query.data.split(":")[1]
    packages = get_packages_for_game(game_key)
    if not packages:
        await query.edit_message_text("⚠️ គ្មាន package សម្រាប់ហ្គេមនេះទេ។")
        return
    keyboard = [
        [InlineKeyboardButton(f"{p['label']} ({p['price']:,.0f}៛)", callback_data=f"admin_setprice_pkg:{game_key}:{p['code']}")]
        for p in packages
    ]
    await query.edit_message_text("ជ្រើសរើសកញ្ចប់ដែលចង់កំណត់តម្លៃ៖", reply_markup=InlineKeyboardMarkup(keyboard))


async def admin_setprice_pkg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    _, game_key, code = query.data.split(":")
    context.user_data["setprice_game"] = game_key
    context.user_data["setprice_code"] = code
    await query.edit_message_text("✍️ សូមវាយបញ្ចូលតម្លៃថ្មី (ជាលេខ) ឧ. 2500")
    return ADMIN_SET_PRICE


async def admin_setprice_receive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    try:
        price = float(text)
    except ValueError:
        await update.message.reply_text("⚠️ សូមវាយបញ្ចូលជាលេខ ឧ. 2500")
        return ADMIN_SET_PRICE

    game_key = context.user_data.get("setprice_game")
    code = context.user_data.get("setprice_code")
    set_price_override(game_key, code, price)
    await update.message.reply_text(f"✅ បានកំណត់តម្លៃថ្មី៖ {price:,.0f} ៛")
    context.user_data.clear()
    return ConversationHandler.END


# ============================================================
# 11) REPLY KEYBOARD (bottom persistent buttons) ROUTER
# ============================================================


async def text_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """គ្រប់គ្រង Reply Keyboard buttons + Broadcast text ពី Admin"""
    text = update.message.text
    user = update.effective_user

    if context.user_data.get("awaiting_broadcast") and is_admin(user.id):
        context.user_data["awaiting_broadcast"] = False
        user_ids = get_all_user_ids()
        sent, failed = 0, 0
        for uid in user_ids:
            try:
                await context.bot.send_message(uid, f"📢 {text}")
                sent += 1
            except Exception:
                failed += 1
        await update.message.reply_text(f"✅ Broadcast ចប់សព្វគ្រប់៖ ជោគជ័យ {sent}, បរាជ័យ {failed}")
        return

    if text == BTN_BUY:
        await send_game_menu(update.effective_chat.id, context)
    elif text == BTN_MY_ORDERS:
        await my_orders_msg(update.effective_chat.id, user.id, context)
    elif text == BTN_HELP:
        await update.message.reply_text(
            "❓ *របៀបប្រើប្រាស់*\n\n"
            "1️⃣ ចុច «🎮 ទិញ Diamond» ជ្រើសរើសហ្គេម និងកញ្ចប់\n"
            "2️⃣ បញ្ចូល User ID / Zone ID របស់អ្នក\n"
            "3️⃣ ស្កេន KHQR ទូទាត់ប្រាក់\n"
            "4️⃣ ប្រព័ន្ធនឹង Topup ជូនអ្នកដោយស្វ័យប្រវត្តិភ្លាមៗ ✅\n\n"
            "មានបញ្ហា? ទាក់ទង Admin បាន!",
            parse_mode=ParseMode.MARKDOWN,
        )
    elif text == BTN_ADMIN and is_admin(user.id):
        await admin_panel(update, context)


# ============================================================
# 12) RENDER: Flask health server + self-ping (Free tier keep-alive)
# ============================================================

flask_app = Flask(__name__)


@flask_app.route("/")
def health_check():
    return {"status": "ok", "service": "diamond-topup-bot", "time": time.time()}, 200


def run_flask():
    """Render Web Service ត្រូវការ port ចាំបើក — រត់ Flask ក្នុង thread ដាច់ដោយឡែក"""
    flask_app.run(host="0.0.0.0", port=PORT)


def self_ping_loop():
    """
    Render free tier នឹងធ្វើឲ្យ service គេង (sleep) បើគ្មាន traffic ក្នុងរយៈពេល ~15 នាទី
    Loop នេះ ping ខ្លួនឯងជាទៀងទាត់ ដើម្បីរក្សា service ឲ្យភ្ញាក់ជានិច្ច
    (មិនចាំបាច់ប្រសិនបើប្រើ paid plan / Background Worker)
    """
    if not RENDER_EXTERNAL_URL:
        log.info("RENDER_EXTERNAL_URL មិនត្រូវបានកំណត់ទេ — self-ping មិនដំណើរការ (ធម្មតាសម្រាប់ local/worker)")
        return
    while True:
        time.sleep(SELF_PING_INTERVAL_SECONDS)
        try:
            requests.get(RENDER_EXTERNAL_URL, timeout=10)
            log.info("🔁 Self-ping sent to keep service awake")
        except Exception as e:
            log.warning(f"Self-ping failed: {e}")


# ============================================================
# 13) MAIN
# ============================================================


def main():
    if BOT_TOKEN.startswith("PUT_YOUR"):
        log.warning("⚠️ BOT_TOKEN មិនទាន់ត្រូវបានកំណត់ទេ! សូមកំណត់ env var BOT_TOKEN ជាមុនសិន")

    # Start Flask health server (required for Render Web Service port binding)
    threading.Thread(target=run_flask, daemon=True).start()
    # Start self-ping loop (keeps free-tier service awake)
    threading.Thread(target=self_ping_loop, daemon=True).start()

    app = Application.builder().token(BOT_TOKEN).build()

    order_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(package_selected, pattern=r"^pkg:")],
        states={
            ASK_FIELD: [MessageHandler(filters.TEXT & ~filters.COMMAND, field_input)],
            CONFIRM_ORDER: [
                CallbackQueryHandler(confirm_order, pattern=r"^confirm_order$"),
                CallbackQueryHandler(cancel_order, pattern=r"^cancel_order$"),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_conv)],
        per_message=False,
    )

    price_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_setprice_pkg, pattern=r"^admin_setprice_pkg:")],
        states={
            ADMIN_SET_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_setprice_receive)],
        },
        fallbacks=[CommandHandler("cancel", cancel_conv)],
        per_message=False,
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(order_conv)
    app.add_handler(price_conv)
    app.add_handler(CallbackQueryHandler(game_selected, pattern=r"^game:"))
    app.add_handler(CallbackQueryHandler(back_to_games, pattern=r"^back_to_games$"))
    app.add_handler(CallbackQueryHandler(my_orders, pattern=r"^my_orders$"))
    app.add_handler(CallbackQueryHandler(check_payment_callback, pattern=r"^check_pay:"))
    app.add_handler(CallbackQueryHandler(admin_callback, pattern=r"^admin:"))
    app.add_handler(CallbackQueryHandler(admin_setprice_game, pattern=r"^admin_setprice_game:"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_router))

    log.info("🚀 Bot កំពុងដំណើរការ (Auto Payment + Auto Topup enabled)...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
