# 🚀 Tell Tims Auto-Coupon Telegram Bot (100% Free 24/7 Hosting Guide)
**Developer:** SIDHU (`@deep_xd5`)

---

## 🌟 Features
1. **Direct Photo OCR**: Receipt ki photo bhejo -> Instant coupon code!
2. **Multi-Photo Batch**: Ek sath 5-10 photos bhejo -> Sabhi ke coupon codes ek sath generate honge!
3. **Direct Text Codes**: Bina kisi command ke direct 21-digit code likh kar bhejo -> Auto solve!
4. **`/code` Command**: `/code 2032-9620-2142-1050-60409`
5. **Royal Punjabi Dialogues & Swagger Dev Branding**: `@deep_xd5`

---

## 🛠️ Step 1: Telegram Bot Token Create Karein
1. Telegram par **`@BotFather`** search karein.
2. `/newbot` likhein.
3. Bot ka naam aur username set karein (e.g. `TellTims_SidhuBot`).
4. `@BotFather` aapko **HTTP API Token** dega (e.g. `7823456789:AAHk...`).

---

## 💻 Step 2: Local Run (Apne Computer par)
1. `Downloads\tims_survey_bot\.env` file open karein.
2. Token paste karein:
   ```env
   TELEGRAM_BOT_TOKEN=your_token_here
   ```
3. `run_tg_bot.bat` par double click karein!

---

## ☁️ Step 3: 24/7 Free Cloud Hosting (Bina Computer On Rakhe)

### Option A: Render.com (100% Free)
1. Is folder ko apne **GitHub Repository** mein upload / push karein.
2. **[Render.com](https://render.com)** par login karein.
3. **New +** -> **Background Worker** (ya **Web Service**) select karein.
4. Apna GitHub Repo connect karein.
5. Settings:
   - **Runtime:** `Docker` (automatically `Dockerfile` detect kar lega)
   - **Environment Variables:**
     - Key: `TELEGRAM_BOT_TOKEN`
     - Value: `your_bot_token_here`
6. **Deploy** par click karein. Bot 24/7 life-time free chalega!

### Option B: Koyeb.com (100% Free - No Credit Card)
1. **[Koyeb.com](https://koyeb.com)** par login karein.
2. **Create Service** -> **GitHub Repo** select karein.
3. Builder mein `Dockerfile` select karein.
4. Environment variable `TELEGRAM_BOT_TOKEN` set karein aur deploy dabayein!
