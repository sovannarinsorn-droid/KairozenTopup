# -*- coding: utf-8 -*-
"""
game_topup_bot.py — Kairozen Game Topup Bot
Free Fire / Mobile Legends / PUBG Mobile
Payment: CamRapidPay KHQR | Fulfillment: Bay2Game API
"""
import json
import time
import threading
import telebot
from telebot import types

import config
import orders_store
import camrapidpay
import bay2game_api
import premium_emoji as pe
import products_store
import users_store
import admin_panel

bot = telebot.TeleBot(config.BOT_TOKEN, parse_mode="HTML")

PRODUCTS = products_store.load()


def reload_products():
    global PRODUCTS
    PRODUCTS = products_store.load()


STATE = {}


def is_admin(user_id):
    return user_id in config.ADMIN_IDS


def main_reply_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(
        types.KeyboardButton(pe.label("topup", "ទិញ Topup"), **pe.button_kwargs("topup")),
        types.KeyboardButton(pe.label("myorders", "Order របស់ខ្ញុំ"), **pe.button_kwargs("myorders")),
    )
    kb.add(types.KeyboardButton(pe.label("help", "ជំនួយ"), **pe.button_kwargs("help")))
    return kb


def games_menu():
    kb = types.InlineKeyboardMarkup(row_width=1)
    for key, g in PRODUCTS.items():
        kb.add(types.InlineKeyboardButton(
            pe.label(key, g["name"]),
            callback_data=f"game:{key}",
            **pe.button_kwargs(key),
        ))
    return kb


def packages_menu(game_key):
    kb = types.InlineKeyboardMarkup(row_width=1)
    all_pkgs = PRODUCTS[game_key]["packages"]
    shown = [p for p in all_pkgs if p.get("featured", True)]
    for pkg in shown:
        kb.add(types.InlineKeyboardButton(
            f"{pkg['label']} — ${pkg['price_usd']:.2f}",
            callback_data=f"pkg:{game_key}:{pkg['code']}"
        ))
    kb.add(types.InlineKeyboardButton(
        pe.label("back", "ត្រឡប់ក្រោយ"), callback_data="back:games", **pe.button_kwargs("back")
    ))
    return kb


def confirm_menu():
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton(
        pe.label("confirm", "បញ្ជាក់ និងបង្កើត QR ទូទាត់"),
        callback_data="confirm_order", style="success", **pe.button_kwargs("confirm"),
    ))
    kb.add(types.InlineKeyboardButton(
        pe.label("cancel", "បោះបង់"),
        callback_data="cancel_order", style="danger", **pe.button_kwargs("cancel"),
    ))
    return kb


def get_package(game_key, pkg_code):
    for pkg in PRODUCTS[game_key]["packages"]:
        if pkg["code"] == pkg_code:
            return pkg
    return None


@bot.message_handler(commands=["start", "help"])
def cmd_start(message):
    STATE.pop(message.chat.id, None)
    users_store.track_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    bot.send_message(
        message.chat.id,
        "🎮 <b>សូមស្វាគមន៍មកកាន់ Kairozen Game Topup Bot!</b>\n"
        "ប្រើប៊ូតុងខាងក្រោមដើម្បីចាប់ផ្តើម 👇",
        reply_markup=main_reply_menu(),
    )
    _send_games_menu(message.chat.id)


def _send_games_menu(chat_id):
    text = (
        "🎮 <b>ជ្រើសរើសហ្គេម</b>\n\n"
        "• 🔥 Free Fire\n• ⚔️ Mobile Legends\n• 🎯 PUBG Mobile\n\n"
        "💳 ទូទាត់តាម KHQR (ស្កេនតែម្តង)\n"
        "⚡ ដឹកជញ្ជូនស្វ័យប្រវត្តិក្នុងប៉ុន្មានវិនាទី"
    )
    bot.send_message(chat_id, text, reply_markup=games_menu())


@bot.message_handler(func=lambda m: m.text == pe.label("topup", "ទិញ Topup"))
def txt_topup(message):
    STATE.pop(message.chat.id, None)
    _send_games_menu(message.chat.id)


@bot.message_handler(func=lambda m: m.text == pe.label("help", "ជំនួយ"))
def txt_help(message):
    bot.send_message(
        message.chat.id,
        "❓ <b>ជំនួយ</b>\n\n"
        "1️⃣ ចុច 🎮 ទិញ Topup → ជ្រើសហ្គេម → ជ្រើសកញ្ចប់\n"
        "2️⃣ វាយបញ្ចូល Player ID (និង Server ID បើត្រូវការ)\n"
        "3️⃣ ស្កេន KHQR ទូទាត់ → ចុច \"ខ្ញុំបានទូទាត់\"\n"
        "4️⃣ ទទួល Diamond/UC ស្វ័យប្រវត្តិក្នុងប៉ុន្មានវិនាទី\n\n"
        "មានបញ្ហា? ទាក់ទង admin ដោយផ្ទាល់។"
    )


@bot.message_handler(commands=["myorders"])
@bot.message_handler(func=lambda m: m.text == pe.label("myorders", "Order របស់ខ្ញុំ"))
def cmd_myorders(message):
    orders = orders_store.get_user_orders(message.from_user.id, limit=10)
    if not orders:
        bot.send_message(message.chat.id, "អ្នកមិនទាន់មាន order ណាមួយទេ។")
        return
    lines = ["🧾 <b>Order ថ្មីៗរបស់អ្នក</b>\n"]
    for o in orders:
        status_emoji = {"PENDING_PAYMENT": "⏳", "PAID": "💰", "FULFILLED": "✅", "FAILED": "❌"}.get(o["status"], "•")
        lines.append(
            f"{status_emoji} <code>{o['order_id']}</code> — {o['game_name']} {o['package_label']} "
            f"(${o['price_usd']:.2f}) — {o['status']}"
        )
    bot.send_message(message.chat.id, "\n".join(lines))


@bot.message_handler(commands=["stats"])
def cmd_stats(message):
    if not is_admin(message.from_user.id):
        return
    orders = orders_store.get_all_orders(limit=200)
    total = len(orders)
    paid = len([o for o in orders if o["status"] in ("PAID", "FULFILLED")])
    revenue = sum(o["price_usd"] for o in orders if o["status"] in ("PAID", "FULFILLED"))
    bot.send_message(
        message.chat.id,
        f"📊 <b>Admin Stats</b>\nOrders សរុប: {total}\nបានទូទាត់: {paid}\nចំណូលសរុប: ${revenue:.2f}"
    )


@bot.callback_query_handler(func=lambda c: c.data.startswith("game:"))
def cb_game(call):
    game_key = call.data.split(":")[1]
    game = PRODUCTS[game_key]
    STATE[call.message.chat.id] = {"step": "choose_package", "game_key": game_key}
    bot.edit_message_text(
        f"{game['icon']} <b>{game['name']}</b>\nជ្រើសរើសកញ្ចប់ដែលអ្នកចង់ទិញ:",
        call.message.chat.id, call.message.message_id,
        reply_markup=packages_menu(game_key)
    )


@bot.callback_query_handler(func=lambda c: c.data == "back:games")
def cb_back_games(call):
    STATE.pop(call.message.chat.id, None)
    bot.edit_message_text(
        "🎮 <b>Kairozen Game Topup Bot</b>\nជ្រើសរើសហ្គេម:",
        call.message.chat.id, call.message.message_id,
        reply_markup=games_menu()
    )


@bot.callback_query_handler(func=lambda c: c.data.startswith("pkg:"))
def cb_package(call):
    _, game_key, pkg_code = call.data.split(":")
    pkg = get_package(game_key, pkg_code)
    game = PRODUCTS[game_key]
    STATE[call.message.chat.id] = {
        "step": "enter_player_id",
        "game_key": game_key,
        "pkg_code": pkg_code,
    }
    bot.edit_message_text(
        f"{game['icon']} <b>{game['name']}</b> — {pkg['label']} (${pkg['price_usd']:.2f})\n\n"
        f"សូមវាយបញ្ចូល <b>{game['id_label']}</b> របស់អ្នក:",
        call.message.chat.id, call.message.message_id,
    )


@bot.message_handler(func=lambda m: STATE.get(m.chat.id, {}).get("step") == "enter_player_id")
def msg_player_id(message):
    st = STATE[message.chat.id]
    st["player_id"] = message.text.strip()
    game = PRODUCTS[st["game_key"]]
    if game["needs_server"]:
        st["step"] = "enter_server_id"
        bot.send_message(message.chat.id, "សូមវាយបញ្ចូល <b>Server ID / Zone ID</b> របស់អ្នក:")
    else:
        st["server_id"] = ""
        _show_order_summary(message.chat.id)


@bot.message_handler(func=lambda m: STATE.get(m.chat.id, {}).get("step") == "enter_server_id")
def msg_server_id(message):
    st = STATE[message.chat.id]
    st["server_id"] = message.text.strip()
    _show_order_summary(message.chat.id)


def _show_order_summary(chat_id):
    st = STATE[chat_id]
    game = PRODUCTS[st["game_key"]]
    pkg = get_package(st["game_key"], st["pkg_code"])
    st["step"] = "confirm"
    lines = [
        "🧾 <b>សូមផ្ទៀងផ្ទាត់ព័ត៌មាន Order</b>\n",
        f"ហ្គេម: {game['icon']} {game['name']}",
        f"កញ្ចប់: {pkg['label']}",
        f"តម្លៃ: <b>${pkg['price_usd']:.2f}</b>",
        f"{game['id_label']}: <code>{st['player_id']}</code>",
    ]
    if game["needs_server"]:
        lines.append(f"Server/Zone ID: <code>{st['server_id']}</code>")
    lines.append("\n⚠️ សូមពិនិត្យ ID ឲ្យបានត្រឹមត្រូវ — ប្រសិនបើខុស ក្រុមហ៊ុនមិនទទួលខុសត្រូវទេ។")
    bot.send_message(chat_id, "\n".join(lines), reply_markup=confirm_menu())


@bot.callback_query_handler(func=lambda c: c.data == "cancel_order")
def cb_cancel(call):
    STATE.pop(call.message.chat.id, None)
    bot.edit_message_text("❌ បានបោះបង់ order។ វាយ /start ដើម្បីចាប់ផ្តើមម្តងទៀត។",
                           call.message.chat.id, call.message.message_id)


@bot.callback_query_handler(func=lambda c: c.data == "confirm_order")
def cb_confirm(call):
    chat_id = call.message.chat.id
    st = STATE.get(chat_id)
    if not st:
        bot.answer_callback_query(call.id, "Session ផុតកំណត់ សូម /start ម្តងទៀត")
        return
    game = PRODUCTS[st["game_key"]]
    pkg = get_package(st["game_key"], st["pkg_code"])

    order_id = orders_store.new_order(
        user_id=call.from_user.id,
        username=call.from_user.username,
        game_key=st["game_key"],
        game_name=game["name"],
        package_label=pkg["label"],
        price_usd=pkg["price_usd"],
        player_id=st["player_id"],
        server_id=st.get("server_id", ""),
        bay2game_product_code=pkg["bay2game_product_code"],
    )

    khqr = camrapidpay.create_khqr_payment(
        amount_usd=pkg["price_usd"],
        description=f"{game['name']} {pkg['label']} - {order_id}",
        ref_id=order_id,
    )

    if not khqr["success"]:
        bot.edit_message_text(
            "❌ មិនអាចបង្កើត KHQR បានទេ សូមព្យាយាមម្តងទៀត ឬទាក់ទង admin។",
            chat_id, call.message.message_id
        )
        err_detail = (
            f"⚠️ KHQR creation FAILED\n"
            f"order_id: {order_id}\n"
            f"status_code: {khqr.get('status_code')}\n"
            f"error: {khqr.get('error')}\n"
            f"raw: {khqr.get('raw')}"
        )
        for admin_id in config.ADMIN_IDS:
            try:
                bot.send_message(admin_id, err_detail)
            except Exception:
                pass
        return

    qr_string = khqr.get("qr_code", "")
    qr_image_url = (
        f"https://api.qrserver.com/v1/create-qr-code/?size=350x350&data={qr_string}"
        if qr_string else None
    )

    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(
        pe.label("check_payment", "ខ្ញុំបានទូទាត់ — ពិនិត្យ"),
        callback_data=f"check:{order_id}", style="success", **pe.button_kwargs("check_payment"),
    ))

    caption = (
        f"💳 <b>ស្កេន KHQR ដើម្បីទូទាត់ ${pkg['price_usd']:.2f}</b>\n"
        f"ហាង: {config.SHOP_NAME}\n"
        f"Order ID: <code>{order_id}</code>\n\n"
        f"ក្រោយពេលទូទាត់រួច ចុចប៊ូតុងខាងក្រោមដើម្បីឲ្យ bot ពិនិត្យ។"
    )

    STATE.pop(chat_id, None)

    if qr_image_url:
        bot.send_photo(chat_id, qr_image_url, caption=caption, reply_markup=kb)
    else:
        bot.send_message(chat_id, f"{caption}\n\n<code>{qr_string}</code>", reply_markup=kb)

    bot.delete_message(chat_id, call.message.message_id)

    for admin_id in config.ADMIN_IDS:
        try:
            bot.send_message(
                admin_id,
                f"🆕 Order ថ្មី <code>{order_id}</code>\n"
                f"User: @{call.from_user.username or call.from_user.id}\n"
                f"{game['name']} {pkg['label']} — ${pkg['price_usd']:.2f}\n"
                f"ស្ថានភាព: រង់ចាំទូទាត់"
            )
        except Exception:
            pass


@bot.callback_query_handler(func=lambda c: c.data.startswith("check:"))
def cb_check_payment(call):
    order_id = call.data.split(":")[1]
    order = orders_store.get_order(order_id)
    if not order:
        bot.answer_callback_query(call.id, "រកមិនឃើញ order នេះទេ")
        return

    if order["status"] in ("PAID", "FULFILLED"):
        bot.answer_callback_query(call.id, "Order នេះទូទាត់រួចហើយ ✅")
        return

    result = camrapidpay.check_transaction(order_id)
    if not result.get("paid"):
        bot.answer_callback_query(call.id, "⏳ មិនទាន់ឃើញការទូទាត់ទេ សូមព្យាយាមម្តងទៀតបន្ទាប់ពីស្កេន")
        return

    orders_store.update_status(order_id, "PAID")
    bot.answer_callback_query(call.id, "✅ ទូទាត់ជោគជ័យ! កំពុងបញ្ជូនកញ្ចប់...")
    bot.send_message(call.message.chat.id, f"💰 ការទូទាត់ order <code>{order_id}</code> ជោគជ័យ! កំពុងដំណើរការ...")

    _fulfill_order(order_id)


def _fulfill_order(order_id):
    order = orders_store.get_order(order_id)
    if not order:
        return
    result = bay2game_api.create_order(
        userid=order["player_id"],
        product_code=order["bay2game_product_code"],
        server_id=order.get("server_id", ""),
        trx_ref=order_id,
    )
    if result.get("success"):
        orders_store.update_status(order_id, "FULFILLED", bay2game_response=result["raw"])
        users_store.track_purchase(order["user_id"], order["price_usd"])
        bot.send_message(
            order["user_id"],
            f"🎉 <b>ជោគជ័យ!</b>\nOrder <code>{order_id}</code> ({order['game_name']} {order['package_label']}) "
            f"ត្រូវបានបញ្ជូនចូល {order['player_id']} រួចរាល់។\nសូមអរគុណដែលប្រើប្រាស់ Kairozen Store! 🙏"
        )
    else:
        orders_store.update_status(order_id, "FAILED", bay2game_response=result.get("raw", {}))
        bot.send_message(
            order["user_id"],
            f"⚠️ Order <code>{order_id}</code> ទូទាត់ជោគជ័យ ប៉ុន្តែការបញ្ជូនកញ្ចប់មានបញ្ហា។ "
            f"Admin នឹងដោះស្រាយ manual ជូនក្នុងពេលឆាប់ៗនេះ។"
        )
        for admin_id in config.ADMIN_IDS:
            try:
                bot.send_message(
                    admin_id,
                    f"❌ FULFILLMENT FAILED\nOrder: <code>{order_id}</code>\n"
                    f"Player: {order['player_id']} ({order['game_name']} {order['package_label']})\n"
                    f"Bay2Game raw: <code>{result.get('raw')}</code>\n"
                    f"សូម top up ដោយដៃជូន user!"
                )
            except Exception:
                pass


admin_panel.register(bot, reload_products_cb=reload_products)

if __name__ == "__main__":
    print("🚀 Kairozen Game Topup Bot កំពុងដំណើរការ...")
    bot.infinity_polling(skip_pending=True)
