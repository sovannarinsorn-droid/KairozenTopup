# -*- coding: utf-8 -*-
"""products_store.py — អាន/សរសេរ products.json ជាដើម្បីឲ្យ admin កែតម្លៃពី bot ដោយផ្ទាល់"""
import json
import os
import threading
import config

_lock = threading.Lock()


def load():
    with open(config.PRODUCTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save(data):
    tmp = config.PRODUCTS_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, config.PRODUCTS_FILE)


def update_price(game_key, pkg_code, new_price):
    with _lock:
        data = load()
        if game_key not in data:
            return None
        for pkg in data[game_key]["packages"]:
            if pkg["code"] == pkg_code:
                pkg["price_usd"] = round(float(new_price), 2)
                save(data)
                return pkg
        return None


def get_package(game_key, pkg_code):
    data = load()
    if game_key not in data:
        return None
    for pkg in data[game_key]["packages"]:
        if pkg["code"] == pkg_code:
            return pkg
    return None
