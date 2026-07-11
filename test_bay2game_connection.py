# -*- coding: utf-8 -*-
"""
test_bay2game_connection.py — Debug ការតភ្ជាប់ទៅ Bay2Game

សាកល្បង:
  1. DNS/connectivity ទៅ api.bay2game.com
  2. /create_orders ជាមួយ product_code ក្លែងក្លាយ (មិនបង្កើត order ពិតទេ — គួរតែ
     return error 400/404 ប្រាប់ថា product មិនត្រឹមត្រូវ ជាជាង timeout ឬ 401)
  3. សាកល្បង auth header ជាច្រើនទម្រង់ ដើម្បីមើលថាមួយណាត្រូវ

Run:
    export BAY2GAME_API_KEY="xxxxx"
    python test_bay2game_connection.py
"""
import os
import json
import requests

API_KEY = os.environ.get("BAY2GAME_API_KEY", "")
URL = "https://api.bay2game.com/create_orders"

DUMMY_PAYLOAD = {
    "userid": "TEST_CONNECTION_CHECK_DO_NOT_PROCESS",
    "server_id": "",
    "product_code": "__invalid_test_code__",
    "callback_url": "",
}

AUTH_VARIANTS = [
    ("Bearer token header", {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}),
    ("Raw Authorization header", {"Authorization": API_KEY, "Content-Type": "application/json"}),
    ("api_key header", {"api_key": API_KEY, "Content-Type": "application/json"}),
    ("X-API-KEY header", {"X-API-KEY": API_KEY, "Content-Type": "application/json"}),
    ("api_key in body", {"Content-Type": "application/json"}),  # api_key added to payload below
]


def main():
    if not API_KEY:
        print("❌ សូម export BAY2GAME_API_KEY មុនសិន")
        return

    print("1️⃣ ពិនិត្យ DNS/connectivity...")
    try:
        r = requests.get("https://api.bay2game.com/", timeout=10)
        print(f"   ✅ Base URL ឆ្លើយតប: HTTP {r.status_code}")
    except requests.RequestException as e:
        print(f"   ❌ Base URL មិនឆ្លើយតបទេ: {e}")
        print("   → domain 'api.bay2game.com' ប្រហែលជាមិនត្រឹមត្រូវ សូមសុំ base URL ត្រឹមត្រូវពី @Bay2GameBot")
        return

    print("\n2️⃣ សាកល្បង POST /create_orders ជាមួយ auth variants ផ្សេងៗ...\n")
    for name, headers in AUTH_VARIANTS:
        payload = dict(DUMMY_PAYLOAD)
        if name == "api_key in body":
            payload["api_key"] = API_KEY
        try:
            resp = requests.post(URL, json=payload, headers=headers, timeout=15)
            print(f"• {name}: HTTP {resp.status_code}")
            try:
                print(f"   {json.dumps(resp.json(), ensure_ascii=False)[:300]}")
            except ValueError:
                print(f"   (non-JSON) {resp.text[:200]}")
        except requests.RequestException as e:
            print(f"• {name}: ❌ {e}")
        print()

    print(
        "💡 ការបកស្រាយ:\n"
        "  - HTTP 401/403 → domain/endpoint ត្រូវ ប៉ុន្តែ auth ខុសទម្រង់ (សាកល្បង variant ផ្សេង)\n"
        "  - HTTP 400/404 ជាមួយសារ error អំពី product/userid → endpoint + auth ត្រូវហើយ! (ល្អបំផុត)\n"
        "  - HTTP 404 លើគ្រប់ variant → path '/create_orders' ខុស ត្រូវសុំ path ត្រឹមត្រូវ\n"
        "  - Connection error គ្រប់ variant → domain ខុស"
    )


if __name__ == "__main__":
    main()
