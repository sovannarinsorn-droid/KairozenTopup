# របៀប Deploy ទៅ Render

## 1) រៀបចំ GitHub Repo
ដាក់ file ទាំងអស់នេះចូល repo មួយ (bot.py, requirements.txt, render.yaml, Procfile, runtime.txt)

## 2) បង្កើត Web Service នៅ Render
1. ចូល https://dashboard.render.com → **New** → **Web Service**
2. ភ្ជាប់ GitHub repo របស់អ្នក
3. Render នឹងអាន `render.yaml` ដោយស្វ័យប្រវត្តិ (Blueprint) — ឬកំណត់ដោយដៃ៖
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python bot.py`
   - **Plan**: Free (ឬ Starter ដើម្បីជៀសវាង sleep)

## 3) កំណត់ Environment Variables (Settings → Environment)
| Key | តម្លៃ |
|---|---|
| `BOT_TOKEN` | Token ពី @BotFather |
| `BAY2GAME_BASE_URL` | https://api.bay2game.xyz/api |
| `BAY2GAME_API_KEY` | API key ពិត — យកតាម Telegram [@Bay2GameBot](https://t.me/Bay2GameBot) ដោយវាយ `/profile` |
| `USD_TO_KHR_RATE` | អត្រាប្តូររូបិយប័ណ្ណ USD→៛ (default 4100) សម្រាប់គណនាតម្លៃដើម |
| `CAMRAPID_API_KEY` | API key ពិត — ស្នើតាម Telegram [@CamRapidSecureSupport](https://t.me/CamRapidSecureSupport) |
| `CAMRAPID_CREATE_URL` | https://pay.camrapidpay.com/api/v1/khqr/create-payments |
| `CAMRAPID_CHECK_URL` | https://pay.camrapidpay.com/check-transaction-api |
| `PORT` | Render កំណត់ជូនស្វ័យប្រវត្តិ (មិនចាំបាច់ដាក់ដោយដៃ) |

⚠️ កុំភ្លេចកែ `ADMIN_IDS` ក្នុង `bot.py` ជា Telegram ID ពិតរបស់ Admin (deploy រួចមិនអាចប្តូរតាម env បានទេ លុះត្រាតែកែកូដ)។

## 4) ហេតុអ្វី Bot ត្រូវការ Flask/Port?
Render **Web Service** តម្រូវឲ្យ app bind port មួយ (តាម env var `PORT`) មិនដូច Background Worker ទេ។
`bot.py` បានបញ្ចូល Flask health-check server (`/`) រត់ស្របគ្នាជាមួយ Telegram polling loop ដើម្បីបំពេញលក្ខខណ្ឌនេះ។

## 5) Free Tier នឹងគេង (Sleep) — Self-Ping
Render Free Web Service នឹងគេងបន្ទាប់ពីគ្មាន traffic ~15 នាទី ដែលធ្វើឲ្យ bot ឈប់ដំណើរការ (រួមទាំង Auto-Payment polling)។
`bot.py` មាន self-ping loop ស្វ័យប្រវត្តិ (ប្រើ `RENDER_EXTERNAL_URL` ដែល Render ដាក់ជូនស្វ័យប្រវត្តិ) ping ខ្លួនឯងរាល់ 10 នាទី។

⚠️ **សំខាន់**: Self-ping មិនធានា 100% ថា bot ភ្ញាក់ជានិច្ចទេ (Render អាចនៅតែគេងបើមិនមាន traffic ខាងក្រៅ)។
ដើម្បីឲ្យ Auto-Payment + Auto-Topup ដំណើរការគ្រប់ពេលដោយទុកចិត្តបាន ១០០%៖
- **ណែនាំ**: ប្រើ **Render Background Worker** (មិនមែន Web Service) ជាមួយ **Starter plan** ($7/ខែ) ដែលមិនគេងទាល់តែសោះ
- ឬប្រើសេវា uptime monitor ខាងក្រៅ (ឧ. UptimeRobot) ping `https://your-app.onrender.com` រាល់ 5-10 នាទី

## 6) ពិនិត្យ Log
Render Dashboard → service → **Logs** — មើលបន្ទាត់ `🚀 Bot កំពុងដំណើរការ...` ដើម្បីដឹងថា bot ចាប់ផ្តើមជោគជ័យ។
