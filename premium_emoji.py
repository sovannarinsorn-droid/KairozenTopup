# -*- coding: utf-8 -*-
"""
premium_emoji.py — គ្រប់គ្រង Premium (custom) emoji ID សម្រាប់ button
ឥឡូវទិន្នន័យផ្ទុកក្នុង emoji_ids.json (មិនមែន hardcode ក្នុងកូដទៀតទេ) ដូច្នេះ
admin អាចកែពី bot admin panel ដោយផ្ទាល់ ដោយមិនចាំបាច់ deploy កូដថ្មី។

ត្រូវការ: Bot owner (Phanna) មាន Telegram Premium សកម្ម (ឬបានទិញ Fragment username ជូន bot)
មិនដូច្នេះទេ icon_custom_emoji_id នឹងមិនបង្ហាញ។
"""
import json
import os
import threading

EMOJI_FILE = os.environ.get("EMOJI_FILE", "emoji_ids.json")
_lock = threading.Lock()

# key -> (ឈ្មោះបង្ហាញជាភាសាខ្មែរ, unicode fallback)
KEY_INFO = {
    "freefire": ("Free Fire", "🔥"),
    "mobilelegends": ("Mobile Legends", "⚔️"),
    "pubgm": ("PUBG Mobile", "🎯"),
    "topup": ("ម៉ឺនុយ ទិញ Topup", "🎮"),
    "myorders": ("ម៉ឺនុយ Order របស់ខ្ញុំ", "🧾"),
    "help": ("ម៉ឺនុយ ជំនួយ", "❓"),
    "confirm": ("ប៊ូតុង បញ្ជាក់", "✅"),
    "cancel": ("ប៊ូតុង បោះបង់", "❌"),
    "back": ("ប៊ូតុង ត្រឡប់ក្រោយ", "⬅️"),
    "check_payment": ("ប៊ូតុង ខ្ញុំបានទូទាត់", "✅"),
}


def _load():
    if not os.path.exists(EMOJI_FILE):
        return {}
    try:
        with open(EMOJI_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}


def _save(data):
    tmp = EMOJI_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, EMOJI_FILE)


def get_id(key):
    with _lock:
        return _load().get(key)


def set_id(key, custom_emoji_id):
    with _lock:
        data = _load()
        data[key] = custom_emoji_id
        _save(data)


def remove_id(key):
    with _lock:
        data = _load()
        data.pop(key, None)
        _save(data)


def button_kwargs(key: str) -> dict:
    """ត្រឡប់ {icon_custom_emoji_id: ...} បើមាន ID ពិត, ត្រឡប់ {} បើគ្មាន"""
    emoji_id = get_id(key)
    if emoji_id:
        return {"icon_custom_emoji_id": emoji_id}
    return {}


def label(key: str, text: str) -> str:
    """បើមាន custom emoji ID រួចហើយ (បង្ហាញជា icon ស្វ័យប្រវត្តិ) មិនចាំបាច់ដាក់ unicode ទៀត"""
    if get_id(key):
        return text
    _, fallback = KEY_INFO.get(key, ("", ""))
    return f"{fallback} {text}".strip()


def all_keys():
    return list(KEY_INFO.keys())


def status_summary():
    """{key: (khmer_name, is_set: bool)} — សម្រាប់ admin panel"""
    ids = _load()
    return {k: (name, bool(ids.get(k))) for k, (name, _fb) in KEY_INFO.items()}
