# Kairozen Game Topup Bot

Telegram bot សម្រាប់ topup Free Fire / Mobile Legends / PUBG Mobile
- ទូទាត់: CamRapidPay KHQR
- ដឹកជញ្ជូន (fulfillment): Bay2Game API

## រចនាសម្ព័ន្ធឯកសារ
```
config.py          → token, API key, admin id (កំណត់ env vars)
products.json       → បញ្ជីហ្គេម/កញ្ចប់ (កែបានផ្ទាល់)
camrapidpay.py       → បង្កើត/ពិនិត្យការទូទាត់ KHQR
bay2game_api.py      → ហៅ Bay2Game ដើម្បីបញ្ជូនកញ្ចប់ (⚠️ សូមអានចំណាំខាងក្រោម)
orders_store.py      → កត់ត្រា order ក្នុង orders.json
game_topup_bot.py    → bot flow សំខាន់ (run ឯកនេះ)
```

## ដំឡើង (Termux)
```bash
pip install -r requirements.txt
export BOT_TOKEN="123456:ABC-DEF..."
export BAY2GAME_API_KEY="xxxxxxxx"
export CAMRAPIDPAY_API_KEY="d9f5828e...(ស្រាប់ជា default ក្នុង config.py)"
python game_topup_bot.py
```

## ⚠️ ត្រូវធ្វើមុនប្រើពិត (Bay2Game)
ខ្ញុំបានឃើញព័ត៌មាន Bay2Game ពី landing page (`bay2game.xyz/developer_docs`) ប៉ុណ្ណោះ
ព្រោះទំព័រនោះ render ដោយ JS ទើបខ្ញុំមិនអាចទាញ full endpoint list បាន។ ដែលឃើញច្បាស់មានតែ:

```
POST https://api.bay2game.com/create_orders
{
  "userid": "sample_game",
  "server_id": "",
  "product_code": "sample_item",
  "callback_url": "https://sampledomain.com/callback"
}
```

**ជំហានត្រូវធ្វើ**:
1. Telegram → **@Bay2GameBot** → វាយ `/profile` ដើម្បីទទួល API key ពិត
2. សុំ/ស្វែងរក full docs៖ product list endpoint, order-status endpoint, auth header
   format ត្រឹមត្រូវ (ខ្ញុំសន្មត `Authorization: Bearer <key>` — អាចខុស)
3. ដាក់ `bay2game_product_code` ក្នុង `products.json` ឲ្យត្រូវនឹង product code
   ពិតដែល Bay2Game កំណត់ (តម្លៃក្នុងឯកសារឥឡូវជា placeholder)
4. កែ `bay2game_api.py` → `check_order_status()` ឲ្យត្រូវ endpoint ពិត
5. តម្លៃ (`price_usd`) ក្នុង `products.json` ជាតម្លៃគំរូ — ត្រូវប្តូរតាមតម្លៃ wholesale
   ពិតពី Bay2Game + margin ដែល Phanna ចង់បាន

## Flow
1. `/start` → ជ្រើសហ្គេម → ជ្រើសកញ្ចប់ → វាយ Player ID (+ Server ID បើ ML)
2. បញ្ជាក់ order → bot បង្កើត KHQR (CamRapidPay)
3. User ស្កេនទូទាត់ → ចុច "ខ្ញុំបានទូទាត់" → bot ពិនិត្យ CamRapidPay
4. បើទូទាត់ត្រូវ → bot ហៅ Bay2Game `create_orders` ស្វ័យប្រវត្តិ → user ទទួល Diamond/UC
5. បើ fulfillment បរាជ័យ → admin ទទួល alert ដើម្បី topup ដោយដៃ (fallback)

## 💎 Premium Emoji លើ Button
Bot API 9.4 បន្ថែម `icon_custom_emoji_id` និង `style` ("danger"/"success"/"primary") ទៅលើ
InlineKeyboardButton/KeyboardButton — pyTelegramBotAPI ≥4.34.0 គាំទ្ររួចហើយ។

**លក្ខខណ្ឌ**: Bot owner (គណនី Phanna) ត្រូវមាន Telegram Premium សកម្ម ឬបានទិញ Fragment
username ជូន bot បើពុំនោះទេ icon នឹងមិនបង្ហាញ (Telegram នឹង fallback ទៅ unicode emoji វិញ)។

**ការកំណត់**: ដាក់ custom emoji ID ចូល `premium_emoji.py` → `EMOJI_IDS` dict។ យក ID ដោយ
ផ្ញើ emoji ទៅ @userinfobot ឬ @RawDataBot ក្នុងសារដែលមាន custom emoji នោះ រួច copy
`custom_emoji_id` ចេញ។ បើមិនទាន់ដាក់ ID កូដនឹង fallback ទៅ unicode emoji ធម្មតាដោយស្វ័យប្រវត្តិ
(មិន error ទេ)។

```bash
pip install --upgrade "pyTelegramBotAPI>=4.34.0"
```

## 🛠 Admin Panel (ក្នុង bot ដោយផ្ទាល់)
វាយ `/admin` (admin only) ដើម្បីបើក panel មាន៖
- 💰 **កែតម្លៃកញ្ចប់** — ជ្រើសហ្គេម → កញ្ចប់ → វាយតម្លៃថ្មី (កែ `products.json` ផ្ទាល់ + reload ស្វ័យប្រវត្តិ, មិនចាំបាច់ restart bot)
- 💎 **Setup Premium Emoji** — ជ្រើស button key → ផ្ញើ custom emoji ក្នុងសារ → រក្សាទុកក្នុង `emoji_ids.json`
- 📢 **ផ្ញើសារទៅ Users** — Broadcast ទៅ users ទាំងអស់ ឬ DM ជាក់លាក់តាម user_id
- 👥 **មើល Users** — total count, users ថ្មីៗ, ស្វែងរកតាម ID/username + មើល order history

## 📦 ស្ថានភាព Product Catalog
- ✅ **Free Fire (SG/MY)** — 17 កញ្ចប់ (11 featured) — តម្លៃ + code ពិតពី Bay2Game
- ✅ **Mobile Legends** — 105 កញ្ចប់ (16 featured) — តម្លៃ + code ពិតពី Bay2Game
- ✅ **PUBG Mobile** — 23 កញ្ចប់ (12 featured) — តម្លៃ + code ពិតពី Bay2Game

`price_usd` = `cost_usd` បច្ចុប្បន្ន (wholesale, មិនទាន់បូក markup)។ `featured: true/false`
កំណត់ថាកញ្ចប់ណាបង្ហាញក្នុង bot menu (ដើម្បីជៀសវាង Mobile Legends 105 button)។ Admin Panel
> កែតម្លៃ អាចមើលទាំង Featured និង "មើលទាំងអស់" (មាន pagination)។ ដើម្បីប្តូរថាតើកញ្ចប់ណា
featured សូមកែ `"featured": true/false` ក្នុង `products.json` ដោយផ្ទាល់ ឬសុំខ្ញុំកែជូន។

## Commands
- `/start` — ចាប់ផ្តើម topup
- `/myorders` — មើល order ថ្មីៗខ្លួនឯង
- `/stats` — admin only, មើលចំនួន order + ចំណូល

## Deploy លើ Render
ដូចគម្រោង Phanna Premium Bot V6 — deploy ជា **Background Worker**, មិនមែន Web Service
(ព្រោះ bot នេះប្រើ `infinity_polling`, មិនត្រូវការ HTTP port)។ បើចង់ប្រើ Bay2Game webhook
callback ត្រូវបន្ថែម Flask keep-alive endpoint ដាច់ដោយឡែក ដូចគម្រោងចាស់។
