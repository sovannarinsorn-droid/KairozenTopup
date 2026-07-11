# -*- coding: utf-8 -*-
"""
fetch_bay2game_products.py — ទាញ product list ពិតពី Bay2Game ដោយប្រើ API key ពិត

របៀបប្រើ:
    export BAY2GAME_API_KEY="xxxxxxxxxxxx"   # យកពី @Bay2GameBot -> /profile
    python fetch_bay2game_products.py

⚠️ ចំណាំ: ខ្ញុំមិនទាន់ដឹង endpoint ត្រឹមត្រូវ 100% សម្រាប់ "product list" របស់ Bay2Game
ព្រោះ developer_docs render ដោយ JS ទើបទាញមិនបានពេញលេញ។ Script នេះនឹងសាកល្បង
endpoint ដែលគេប្រើជាទូទៅ (products, price-list, games, catalog ។ល។) ហើយបង្ហាញលទ្ធផល
raw JSON ជូន — Phanna អាចមើល field name ពិត រួចប្រាប់ខ្ញុំវិញ ខ្ញុំនឹងកែ
game_topup_bot/products.json ឲ្យត្រូវតាមទិន្នន័យពិតភ្លាមតែម្តង។
"""
import json
import os
import requests

API_KEY = os.environ.get("BAY2GAME_API_KEY", "")
BASE_URL = "https://api.bay2game.com"

CANDIDATE_ENDPOINTS = [
    "/products",
    "/product_list",
    "/price_list",
    "/games",
    "/game_list",
    "/catalog",
    "/get_products",
]

HEADERS_VARIANTS = [
    {"Authorization": f"Bearer {API_KEY}"},
    {"api_key": API_KEY},
    {"X-API-KEY": API_KEY},
]


def try_fetch():
    if not API_KEY:
        print("❌ សូម export BAY2GAME_API_KEY មុនសិន (យកពី @Bay2GameBot -> /profile)")
        return

    found_any = False
    for path in CANDIDATE_ENDPOINTS:
        url = BASE_URL + path
        for headers in HEADERS_VARIANTS:
            try:
                resp = requests.get(url, headers=headers, timeout=10)
            except requests.RequestException as e:
                continue
            if resp.status_code == 200:
                try:
                    data = resp.json()
                except ValueError:
                    continue
                print(f"\n✅ ជោគជ័យ! {url}  (headers: {list(headers.keys())})")
                print(json.dumps(data, indent=2, ensure_ascii=False)[:3000])
                with open("bay2game_raw_response.json", "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                print("\n💾 បានរក្សាទុកលទ្ធផលពេញលេញក្នុង bay2game_raw_response.json")
                found_any = True
            else:
                print(f"• {url} -> HTTP {resp.status_code} ({list(headers.keys())})")

    if not found_any:
        print(
            "\n⚠️ គ្មាន endpoint ណាដំណើរការទេ។ សូមផ្ញើ `/profile` និង `/help` ទៅ @Bay2GameBot "
            "ដើម្បីសុំ full API documentation ផ្ទាល់ពី Bay2Game ។"
        )


if __name__ == "__main__":
    try_fetch()
