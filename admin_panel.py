# -*- coding: utf-8 -*-
"""
admin_panel.py — Admin Panel ក្នុង Telegram bot ដោយផ្ទាល់ (មិនចាំបាច់ deploy កូដថ្មីរាល់ពេលកែ)

មុខងារ:
  💰 កែតម្លៃកញ្ចប់ (products.json)
  💎 Setup Premium Emoji (emoji_ids.json)
  📢 ផ្ញើសារទៅ users (broadcast ទាំងអស់ ឬ DM ជាក់លាក់)
  👥 មើល users (list + ស្វែងរក + history)

របៀបប្រើ: import admin_panel; admin_panel.register(bot, reload_products_cb)
"""
import time
import telebot
from telebot import types

import config
import products_store
import premium_emoji as pe
import users_store
import orders_store

ADMIN_STATE = {}
_reload_products_cb = None


def is_admin(user_id):
    return user_id in config.ADMIN_IDS


def register(bot: telebot.TeleBot, reload_products_cb=None):
    global _reload_products_cb
    _reload_products_cb = reload_products_cb

    # ---------- Main menu ----------

    def admin_menu_kb():
        kb = types.InlineKeyboardMarkup(row_width=1)
        kb.add(types.InlineKeyboardButton("💰 កែតម្លៃកញ្ចប់", callback_data="adm:price"))
        kb.add(types.InlineKeyboardButton("💎 Setup Premium Emoji", callback_data="adm:emoji"))
        kb.add(types.InlineKeyboardButton("📢 ផ្ញើសារទៅ Users", callback_data="adm:msg"))
        kb.add(types.InlineKeyboardButton("👥 មើល Users", callback_data="adm:users"))
        return kb

    @bot.message_handler(commands=["admin"])
    def cmd_admin(message):
        if not is_admin(message.from_user.id):
            return
        ADMIN_STATE.pop(message.chat.id, None)
        bot.send_message(message.chat.id, "🛠 <b>Admin Panel</b>", reply_markup=admin_menu_kb())

    @bot.callback_query_handler(func=lambda c: c.data == "adm:home")
    def cb_home(call):
        if not is_admin(call.from_user.id):
            return
        ADMIN_STATE.pop(call.message.chat.id, None)
        bot.edit_message_text("🛠 <b>Admin Panel</b>", call.message.chat.id, call.message.message_id,
                               reply_markup=admin_menu_kb())

    # ---------- 💰 Price editing ----------

    PAGE_SIZE = 15

    @bot.callback_query_handler(func=lambda c: c.data == "adm:price")
    def cb_price_games(call):
        if not is_admin(call.from_user.id):
            return
        products = products_store.load()
        kb = types.InlineKeyboardMarkup(row_width=1)
        for key, g in products.items():
            total = len(g["packages"])
            kb.add(types.InlineKeyboardButton(
                f"{g['icon']} {g['name']} ({total})", callback_data=f"adm:price:g:{key}:featured:0"
            ))
        kb.add(types.InlineKeyboardButton("⬅️ ត្រឡប់", callback_data="adm:home"))
        bot.edit_message_text("💰 <b>ជ្រើសហ្គេមដើម្បីកែតម្លៃ</b>", call.message.chat.id, call.message.message_id,
                               reply_markup=kb)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("adm:price:g:"))
    def cb_price_packages(call):
        if not is_admin(call.from_user.id):
            return
        _, _, _, game_key, mode, page_str = call.data.split(":")
        page = int(page_str)
        products = products_store.load()
        game = products[game_key]
        all_pkgs = game["packages"]
        pkgs = [p for p in all_pkgs if p.get("featured", True)] if mode == "featured" else all_pkgs

        start = page * PAGE_SIZE
        page_items = pkgs[start:start + PAGE_SIZE]
        has_prev = page > 0
        has_next = start + PAGE_SIZE < len(pkgs)

        kb = types.InlineKeyboardMarkup(row_width=1)
        for pkg in page_items:
            warn = " ⚠️" if pkg.get("cost_usd") is not None and pkg["price_usd"] <= pkg["cost_usd"] else ""
            kb.add(types.InlineKeyboardButton(
                f"{pkg['label']} — ${pkg['price_usd']:.2f}{warn}",
                callback_data=f"adm:price:p:{game_key}:{pkg['code']}"
            ))

        nav_row = []
        if has_prev:
            nav_row.append(types.InlineKeyboardButton("⬅️ មុន", callback_data=f"adm:price:g:{game_key}:{mode}:{page-1}"))
        if has_next:
            nav_row.append(types.InlineKeyboardButton("បន្ទាប់ ➡️", callback_data=f"adm:price:g:{game_key}:{mode}:{page+1}"))
        if nav_row:
            kb.row(*nav_row)

        other_mode = "all" if mode == "featured" else "featured"
        other_label = f"🔽 មើលទាំងអស់ ({len(all_pkgs)})" if mode == "featured" else "⭐ មើលតែ Featured"
        kb.add(types.InlineKeyboardButton(other_label, callback_data=f"adm:price:g:{game_key}:{other_mode}:0"))
        kb.add(types.InlineKeyboardButton("⬅️ ត្រឡប់", callback_data="adm:price"))

        title_mode = "Featured" if mode == "featured" else "ទាំងអស់"
        bot.edit_message_text(
            f"{game['icon']} <b>{game['name']}</b> — {title_mode} ({len(pkgs)}) — ទំព័រ {page+1}",
            call.message.chat.id, call.message.message_id, reply_markup=kb
        )

    @bot.callback_query_handler(func=lambda c: c.data.startswith("adm:price:p:"))
    def cb_price_prompt(call):
        if not is_admin(call.from_user.id):
            return
        _, _, _, game_key, pkg_code = call.data.split(":")
        pkg = products_store.get_package(game_key, pkg_code)
        ADMIN_STATE[call.message.chat.id] = {"step": "await_price", "game_key": game_key, "pkg_code": pkg_code}
        cost_line = ""
        if pkg.get("cost_usd") is not None:
            margin = pkg["price_usd"] - pkg["cost_usd"]
            cost_line = f"\nតម្លៃដើម (cost): ${pkg['cost_usd']:.2f} | ចំណេញបច្ចុប្បន្ន: ${margin:.2f}"
        bot.send_message(
            call.message.chat.id,
            f"💰 <b>{pkg['label']}</b>\nតម្លៃលក់បច្ចុប្បន្ន: <b>${pkg['price_usd']:.2f}</b>{cost_line}\n\n"
            f"សូមវាយបញ្ចូលតម្លៃថ្មី (ជាលេខ ឧ. 1.90):"
        )

    @bot.message_handler(func=lambda m: ADMIN_STATE.get(m.chat.id, {}).get("step") == "await_price")
    def msg_price_update(message):
        if not is_admin(message.from_user.id):
            return
        st = ADMIN_STATE.pop(message.chat.id)
        try:
            new_price = float(message.text.strip().replace("$", ""))
            if new_price <= 0:
                raise ValueError
        except ValueError:
            bot.send_message(message.chat.id, "❌ តម្លៃមិនត្រឹមត្រូវ សូមព្យាយាមម្តងទៀត (ឧ. 1.90)")
            ADMIN_STATE[message.chat.id] = st
            return
        pkg = products_store.update_price(st["game_key"], st["pkg_code"], new_price)
        if _reload_products_cb:
            _reload_products_cb()
        bot.send_message(
            message.chat.id,
            f"✅ បានកែតម្លៃ <b>{pkg['label']}</b> ទៅជា <b>${pkg['price_usd']:.2f}</b> ជោគជ័យ!",
            reply_markup=admin_menu_kb()
        )

    # ---------- 💎 Premium Emoji setup ----------

    @bot.callback_query_handler(func=lambda c: c.data == "adm:emoji")
    def cb_emoji_list(call):
        if not is_admin(call.from_user.id):
            return
        status = pe.status_summary()
        kb = types.InlineKeyboardMarkup(row_width=1)
        for key, (name, is_set) in status.items():
            icon = "✅" if is_set else "⭕"
            kb.add(types.InlineKeyboardButton(f"{icon} {name}", callback_data=f"adm:emoji:k:{key}"))
        kb.add(types.InlineKeyboardButton("⬅️ ត្រឡប់", callback_data="adm:home"))
        bot.edit_message_text(
            "💎 <b>Setup Premium Emoji</b>\n✅ = មាន ID រួចហើយ | ⭕ = ប្រើ unicode fallback\n\nជ្រើសប៊ូតុងណាដែលចង់កំណត់ emoji:",
            call.message.chat.id, call.message.message_id, reply_markup=kb
        )

    @bot.callback_query_handler(func=lambda c: c.data.startswith("adm:emoji:k:"))
    def cb_emoji_prompt(call):
        if not is_admin(call.from_user.id):
            return
        key = call.data.split(":")[3]
        name, fallback = pe.KEY_INFO.get(key, ("", ""))
        current = pe.get_id(key)
        ADMIN_STATE[call.message.chat.id] = {"step": "await_emoji", "key": key}
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("🗑 លុប custom emoji (ប្រើ unicode វិញ)", callback_data=f"adm:emoji:clear:{key}"))
        bot.send_message(
            call.message.chat.id,
            f"💎 <b>{name}</b>\nCustom emoji ID បច្ចុប្បន្ន: <code>{current or 'មិនទាន់មាន (unicode ' + fallback + ')'}</code>\n\n"
            f"សូម <b>ផ្ញើ custom (premium) emoji</b> មួយក្នុងសារ (Telegram emoji keyboard → Premium tab) "
            f"bot នឹងទាញ ID ស្វ័យប្រវត្តិ។",
            reply_markup=kb
        )

    @bot.callback_query_handler(func=lambda c: c.data.startswith("adm:emoji:clear:"))
    def cb_emoji_clear(call):
        if not is_admin(call.from_user.id):
            return
        key = call.data.split(":")[3]
        pe.remove_id(key)
        ADMIN_STATE.pop(call.message.chat.id, None)
        bot.answer_callback_query(call.id, "✅ បានលុប — ប្រើ unicode fallback វិញ")
        cb_emoji_list(call)

    @bot.message_handler(
        func=lambda m: ADMIN_STATE.get(m.chat.id, {}).get("step") == "await_emoji",
        content_types=["text"],
    )
    def msg_emoji_capture(message):
        if not is_admin(message.from_user.id):
            return
        st = ADMIN_STATE.get(message.chat.id, {})
        key = st.get("key")
        custom_emoji_id = None
        for ent in (message.entities or []):
            if ent.type == "custom_emoji":
                custom_emoji_id = ent.custom_emoji_id
                break
        if not custom_emoji_id:
            bot.send_message(
                message.chat.id,
                "❌ មិនឃើញ custom (premium) emoji ក្នុងសារនេះទេ។ សូមប្រើ emoji keyboard → tab ⭐ Premium "
                "រួចផ្ញើម្តងទៀត (unicode emoji ធម្មតាមិនដំណើរការទេ)។"
            )
            return
        pe.set_id(key, custom_emoji_id)
        ADMIN_STATE.pop(message.chat.id, None)
        name, _ = pe.KEY_INFO.get(key, ("", ""))
        bot.send_message(
            message.chat.id,
            f"✅ បានកំណត់ Premium emoji សម្រាប់ <b>{name}</b> ជោគជ័យ!\n"
            f"ID: <code>{custom_emoji_id}</code>\n\n"
            f"⚠️ បើមិនឃើញ icon លើ button — ត្រូវប្រាកដថាគណនី bot owner មាន Telegram Premium សកម្ម។",
            reply_markup=admin_menu_kb()
        )

    # ---------- 📢 Message to users ----------

    @bot.callback_query_handler(func=lambda c: c.data == "adm:msg")
    def cb_msg_menu(call):
        if not is_admin(call.from_user.id):
            return
        total = users_store.count_users()
        kb = types.InlineKeyboardMarkup(row_width=1)
        kb.add(types.InlineKeyboardButton(f"📢 Broadcast ទៅ users ទាំងអស់ ({total})", callback_data="adm:msg:all"))
        kb.add(types.InlineKeyboardButton("✉️ ផ្ញើទៅ User ជាក់លាក់", callback_data="adm:msg:one"))
        kb.add(types.InlineKeyboardButton("⬅️ ត្រឡប់", callback_data="adm:home"))
        bot.edit_message_text("📢 <b>ផ្ញើសារទៅ Users</b>", call.message.chat.id, call.message.message_id,
                               reply_markup=kb)

    @bot.callback_query_handler(func=lambda c: c.data == "adm:msg:all")
    def cb_broadcast_prompt(call):
        if not is_admin(call.from_user.id):
            return
        ADMIN_STATE[call.message.chat.id] = {"step": "await_broadcast_text"}
        bot.send_message(call.message.chat.id, "📢 សូមវាយសារដែលចង់ Broadcast ទៅ users ទាំងអស់:")

    @bot.message_handler(func=lambda m: ADMIN_STATE.get(m.chat.id, {}).get("step") == "await_broadcast_text")
    def msg_broadcast_confirm(message):
        if not is_admin(message.from_user.id):
            return
        ADMIN_STATE[message.chat.id] = {"step": "confirm_broadcast", "text": message.text}
        total = users_store.count_users()
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton(f"✅ ផ្ញើទៅ {total} users", callback_data="adm:msg:send_all"))
        kb.add(types.InlineKeyboardButton("❌ បោះបង់", callback_data="adm:home"))
        bot.send_message(
            message.chat.id,
            f"📢 <b>សារជាមុន:</b>\n\n{message.text}\n\n👥 នឹងផ្ញើទៅ <b>{total}</b> users សូមបញ្ជាក់៖",
            reply_markup=kb
        )

    @bot.callback_query_handler(func=lambda c: c.data == "adm:msg:send_all")
    def cb_broadcast_send(call):
        if not is_admin(call.from_user.id):
            return
        st = ADMIN_STATE.pop(call.message.chat.id, None)
        if not st or "text" not in st:
            bot.answer_callback_query(call.id, "Session ផុតកំណត់")
            return
        text = st["text"]
        users = users_store.get_all_users()
        bot.edit_message_text(f"⏳ កំពុងផ្ញើទៅ {len(users)} users...", call.message.chat.id, call.message.message_id)
        success, failed = 0, 0
        for u in users:
            try:
                bot.send_message(u["user_id"], text)
                success += 1
            except Exception:
                failed += 1
            time.sleep(0.05)
        bot.send_message(
            call.message.chat.id,
            f"✅ Broadcast ចប់សព្វគ្រប់!\nជោគជ័យ: {success}\nបរាជ័យ (ប្លុក bot ។ល។): {failed}",
            reply_markup=admin_menu_kb()
        )

    @bot.callback_query_handler(func=lambda c: c.data == "adm:msg:one")
    def cb_dm_prompt_id(call):
        if not is_admin(call.from_user.id):
            return
        ADMIN_STATE[call.message.chat.id] = {"step": "await_dm_userid"}
        bot.send_message(call.message.chat.id, "✉️ សូមវាយ <b>User ID</b> ដែលចង់ផ្ញើសារទៅ:")

    @bot.message_handler(func=lambda m: ADMIN_STATE.get(m.chat.id, {}).get("step") == "await_dm_userid")
    def msg_dm_userid(message):
        if not is_admin(message.from_user.id):
            return
        target_id = message.text.strip()
        if not target_id.isdigit():
            bot.send_message(message.chat.id, "❌ User ID ត្រូវជាលេខ សូមព្យាយាមម្តងទៀត:")
            return
        ADMIN_STATE[message.chat.id] = {"step": "await_dm_text", "target_id": int(target_id)}
        bot.send_message(message.chat.id, f"✉️ សូមវាយសារដែលចង់ផ្ញើទៅ User <code>{target_id}</code>:")

    @bot.message_handler(func=lambda m: ADMIN_STATE.get(m.chat.id, {}).get("step") == "await_dm_text")
    def msg_dm_send(message):
        if not is_admin(message.from_user.id):
            return
        st = ADMIN_STATE.pop(message.chat.id)
        try:
            bot.send_message(st["target_id"], message.text)
            bot.send_message(message.chat.id, "✅ បានផ្ញើសារជោគជ័យ!", reply_markup=admin_menu_kb())
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ មិនអាចផ្ញើបានទេ (user ប្លុក bot ឬ ID មិនត្រឹមត្រូវ)\n<code>{e}</code>")

    # ---------- 👥 View users ----------

    @bot.callback_query_handler(func=lambda c: c.data == "adm:users")
    def cb_users_overview(call):
        if not is_admin(call.from_user.id):
            return
        total = users_store.count_users()
        recent = users_store.get_all_users(limit=15)
        lines = [f"👥 <b>Users សរុប: {total}</b>\n", "<b>ថ្មីៗ 15 នាក់:</b>"]
        for u in recent:
            uname = f"@{u['username']}" if u.get("username") else u["user_id"]
            lines.append(
                f"• <code>{u['user_id']}</code> {uname} — {u['total_orders']} orders (${u['total_spent_usd']:.2f})"
            )
        kb = types.InlineKeyboardMarkup(row_width=1)
        kb.add(types.InlineKeyboardButton("🔍 ស្វែងរក User", callback_data="adm:users:search"))
        kb.add(types.InlineKeyboardButton("⬅️ ត្រឡប់", callback_data="adm:home"))
        bot.edit_message_text("\n".join(lines), call.message.chat.id, call.message.message_id, reply_markup=kb)

    @bot.callback_query_handler(func=lambda c: c.data == "adm:users:search")
    def cb_users_search_prompt(call):
        if not is_admin(call.from_user.id):
            return
        ADMIN_STATE[call.message.chat.id] = {"step": "await_user_search"}
        bot.send_message(call.message.chat.id, "🔍 សូមវាយ User ID ឬ @username ដែលចង់ស្វែងរក:")

    @bot.message_handler(func=lambda m: ADMIN_STATE.get(m.chat.id, {}).get("step") == "await_user_search")
    def msg_users_search(message):
        if not is_admin(message.from_user.id):
            return
        ADMIN_STATE.pop(message.chat.id, None)
        results = users_store.search_users(message.text)
        if not results:
            bot.send_message(message.chat.id, "❌ រកមិនឃើញ user នេះទេ។", reply_markup=admin_menu_kb())
            return
        for u in results[:5]:
            orders = orders_store.get_user_orders(u["user_id"], limit=5)
            lines = [
                f"👤 <b>User <code>{u['user_id']}</code></b>",
                f"Username: @{u['username']}" if u.get("username") else "Username: —",
                f"ចូលដំបូង: {u['first_seen'][:10]}",
                f"ចូលចុងក្រោយ: {u['last_seen'][:10]}",
                f"Order សរុប: {u['total_orders']} (${u['total_spent_usd']:.2f})",
            ]
            if orders:
                lines.append("\n<b>Order ថ្មីៗ:</b>")
                for o in orders:
                    lines.append(f"• {o['game_name']} {o['package_label']} — {o['status']}")
            bot.send_message(message.chat.id, "\n".join(lines))
        bot.send_message(message.chat.id, "—", reply_markup=admin_menu_kb())
