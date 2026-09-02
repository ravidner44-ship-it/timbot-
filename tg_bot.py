#!/usr/bin/env python3
"""
Tell Tims Auto-Coupon Super Telegram Bot (Royal Punjabi Edition)
Developer: SIDHU (@deep_xd5)
Full Auto-Detection: Photos, Multi-Photo Albums, Text Digits, /code Command
"""

import os
import sys
import time
import threading
import telebot
from telebot import types

# Add execution directory to sys.path
sys.path.insert(0, os.path.dirname(__file__))

from tims_bot import TellTimsBot
from ocr_engine import extract_code_from_image_bytes, clean_and_extract_codes
import punjabi_dialogues as pd

# Load Token from Environment with hardcoded fallback
DEFAULT_TOKEN = "8770141008:AAGbQxt-7qIhsLrA6EKGT-J_K1pikp-v5QQ"
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip() or DEFAULT_TOKEN

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")

# Album buffer for handling multi-photo batches
album_buffer = {}
album_lock = threading.Lock()

def process_single_survey(survey_code):
    """
    Runs survey solver and formats swagger Punjabi response
    """
    solver = TellTimsBot()
    res = solver.solve(survey_code)
    
    if res["success"] and res.get("validation_code"):
        return {
            "code": survey_code,
            "success": True,
            "val_code": res["validation_code"],
            "msg": pd.get_success_msg(res["validation_code"])
        }
    elif res["success"]:
        return {
            "code": survey_code,
            "success": True,
            "val_code": None,
            "msg": f"✅ **ਜਵਾਬ ਆ ਗਿਆ:**\n{res['message']}\n\n👨‍💻 **Dev:** {pd.DEV_NAME} ({pd.DEV_USERNAME})"
        }
    else:
        err_msg = res.get("message", "")
        if "already been used" in err_msg.lower():
            return {
                "code": survey_code,
                "success": False,
                "val_code": None,
                "msg": pd.get_already_used_msg()
            }
        return {
            "code": survey_code,
            "success": False,
            "val_code": None,
            "msg": f"❌ **ਗਲਤੀ:** {err_msg}\n\n👨‍💻 **Dev:** {pd.DEV_NAME} ({pd.DEV_USERNAME})"
        }


# ==================== COMMAND HANDLERS ====================

@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.reply_to(message, pd.get_start_msg())

@bot.message_handler(commands=['help'])
def handle_help(message):
    help_text = (
        f"📖 **ਕਿਵੇਂ ਵਰਤਣਾ ਹੈ? (How to Use)**\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"1️⃣ **ਸਿੱਧਾ ਕੋਡ ਭੇਜੋ:** ਬਿਨਾਂ ਕਿਸੇ ਕਮਾਂਡ ਦੇ ਰਸੀਦ ਦਾ 21-ਅੰਕਾਂ ਦਾ ਕੋਡ ਲਿਖ ਕੇ ਭੇਜੋ।\n"
        f"2️⃣ **ਫੋਟੋ ਭੇਜੋ:** ਰਸੀਦ ਦੀ ਫੋਟੋ ਭੇਜੋ, ਬੋਟ ਆਪੇ ਕੋਡ ਲੱਭ ਕੇ ਕੂਪਨ ਦੇ ਦਊਗਾ।\n"
        f"3️⃣ **ਇਕੱਠੀਆਂ ਫੋਟੋਆਂ:** ਇੱਕੋ ਵਾਰ 'ਚ 5-10 ਰਸੀਦਾਂ ਭੇਜੋ, ਸਾਰੇ ਕੂਪਨ ਇਕੱਠੇ ਤਿਆਰ ਹੋਣਗੇ!\n"
        f"4️⃣ **ਕਮਾਂਡ ਨਾਲ:** `/code 2032-9620-2142-1050-60409`\n\n"
        f"👨‍💻 **ਮਾਲਕ:** **{pd.DEV_NAME}** ({pd.DEV_USERNAME}) ☬"
    )
    bot.reply_to(message, help_text)

@bot.message_handler(commands=['dev', 'about'])
def handle_dev(message):
    bot.reply_to(message, pd.ABOUT_TEXT)

@bot.message_handler(commands=['code'])
def handle_code_command(message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2 or not args[1].strip():
        bot.reply_to(message, f"⚠️ **ਕਮਾਂਡ ਵਰਤਣ ਦਾ ਤਰੀਕਾ:**\n`/code 2032-9620-2142-1050-60409`\n\n👨‍💻 **Dev:** {pd.DEV_USERNAME}")
        return

    codes = clean_and_extract_codes(args[1])
    if not codes:
        bot.reply_to(message, pd.get_invalid_msg())
        return

    code = codes[0]
    status_msg = bot.reply_to(message, f"🎯 **ਕੋਡ ਮਿਲ ਗਿਆ:** `{code}`\n\n{pd.get_processing_msg()}")
    result = process_single_survey(code)
    bot.edit_message_text(result["msg"], chat_id=message.chat.id, message_id=status_msg.message_id)


# ==================== DIRECT TEXT HANDLER ====================

@bot.message_handler(func=lambda msg: msg.text and not msg.text.startswith('/'))
def handle_direct_text(message):
    text = message.text.strip()
    codes = clean_and_extract_codes(text)

    if not codes:
        bot.reply_to(message, pd.get_invalid_msg())
        return

    if len(codes) == 1:
        code = codes[0]
        status_msg = bot.reply_to(message, f"🎯 **ਕੋਡ ਮਿਲ ਗਿਆ:** `{code}`\n\n{pd.get_processing_msg()}")
        result = process_single_survey(code)
        bot.edit_message_text(result["msg"], chat_id=message.chat.id, message_id=status_msg.message_id)
    else:
        status_msg = bot.reply_to(message, f"⏳ **ਮਿੱਤਰਾ {len(codes)} ਕੋਡ ਮਿਲ ਗਏ ਨੇ! ਸਾਰੇ ਸੋਲਵ ਹੋ ਰਹੇ ਆਂ...**")
        results = []
        for i, code in enumerate(codes, 1):
            res = process_single_survey(code)
            if res.get("val_code"):
                results.append(f"**[{i}] ਰਸੀਦ:** `{code}`\n🎟️ **ਕੂਪਨ ਕੋਡ:** `{res['val_code']}` ✅")
            else:
                results.append(f"**[{i}] ਰਸੀਦ:** `{code}`\n⚠️ {res['msg']}")
            time.sleep(0.4)

        final_msg = (
            f"🎉 **ਸਾਰੇ ਕੂਪਨ ਤਿਆਰ ਨੇ!**\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n\n" +
            "\n\n".join(results) +
            f"\n\n━━━━━━━━━━━━━━━━━━━━━\n👨‍💻 **ਪਾਵਰਡ ਬਾਏ:** **{pd.DEV_NAME}** ({pd.DEV_USERNAME}) ☬"
        )
        bot.edit_message_text(final_msg, chat_id=message.chat.id, message_id=status_msg.message_id)


# ==================== PHOTO & ALBUM HANDLERS ====================

def process_album_media(chat_id, media_group_id):
    """
    Handles multi-photo batches/albums
    """
    time.sleep(2.5) # Wait for all album chunks
    with album_lock:
        photos = album_buffer.pop(media_group_id, [])

    if not photos:
        return

    status_msg = bot.send_message(chat_id, f"📸 **{len(photos)} ਰਸੀਦਾਂ ਪ੍ਰਾਪਤ ਹੋਈਆਂ! EasyOCR ਨਾਲ ਕੋਡ ਸਕੈਨ ਕੀਤੇ ਜਾ ਰਹੇ ਨੇ...** ⏳")

    all_codes = []
    for file_id in photos:
        try:
            file_info = bot.get_file(file_id)
            file_bytes = bot.download_file(file_info.file_path)
            codes = extract_code_from_image_bytes(file_bytes)
            for c in codes:
                if c not in all_codes:
                    all_codes.append(c)
        except Exception as e:
            print(f"[-] OCR failed for photo: {e}")

    if not all_codes:
        bot.edit_message_text(pd.get_invalid_msg(), chat_id=chat_id, message_id=status_msg.message_id)
        return

    bot.edit_message_text(f"🚀 **ਕੁੱਲ {len(all_codes)} ਕੋਡ ਮਿਲ ਗਏ! ਸਰਵੇ ਸੋਲਵ ਹੋ ਰਹੇ ਆਂ...**", chat_id=chat_id, message_id=status_msg.message_id)

    results = []
    for i, code in enumerate(all_codes, 1):
        res = process_single_survey(code)
        if res.get("val_code"):
            results.append(f"**[{i}] ਰਸੀਦ:** `{code}`\n🎟️ **ਕੂਪਨ ਕੋਡ:** `{res['val_code']}` ✅")
        else:
            results.append(f"**[{i}] ਰਸੀਦ:** `{code}`\n⚠️ {res['msg']}")
        time.sleep(0.4)

    final_report = (
        f"🏆 **ਟਿਮ ਹੋਰਟਨਸ ਕੂਪਨ ਬੈਚ ਰਿਪੋਰਟ**\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n\n" +
        "\n\n".join(results) +
        f"\n\n━━━━━━━━━━━━━━━━━━━━━\n"
        f"👉 ਸਾਰੇ ਕੋਡ ਰਸੀਦਾਂ 'ਤੇ ਲਿਖੋ ਤੇ ਆਫਰ ਦਾ ਆਨੰਦ ਲਵੋ! ☕🍩\n"
        f"👨‍💻 **ਡਿਵੈਲਪਰ:** **{pd.DEV_NAME}** ({pd.DEV_USERNAME}) ☬"
    )
    bot.edit_message_text(final_report, chat_id=chat_id, message_id=status_msg.message_id)


@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    photo = message.photo[-1]
    media_group_id = message.media_group_id

    if media_group_id:
        with album_lock:
            if media_group_id not in album_buffer:
                album_buffer[media_group_id] = []
                threading.Thread(target=process_album_media, args=(message.chat.id, media_group_id), daemon=True).start()
            album_buffer[media_group_id].append(photo.file_id)
        return

    # Single Photo
    status_msg = bot.reply_to(message, "🔍 **ਰਸੀਦ ਵਿੱਚੋਂ ਸਰਵੇ ਕੋਡ ਪੜ੍ਹ ਰਿਹਾ ਆਂ, ਖਲੋਵੋ ਜਰਾ...**")
    
    try:
        file_info = bot.get_file(photo.file_id)
        file_bytes = bot.download_file(file_info.file_path)
        codes = extract_code_from_image_bytes(file_bytes)

        if not codes:
            bot.edit_message_text(pd.get_invalid_msg(), chat_id=message.chat.id, message_id=status_msg.message_id)
            return

        code = codes[0]
        bot.edit_message_text(f"🎯 **ਕੋਡ ਮਿਲ ਗਿਆ:** `{code}`\n\n{pd.get_processing_msg()}", chat_id=message.chat.id, message_id=status_msg.message_id)

        result = process_single_survey(code)
        bot.edit_message_text(result["msg"], chat_id=message.chat.id, message_id=status_msg.message_id)
    except Exception as e:
        bot.edit_message_text(f"❌ **ਗਲਤੀ:** {e}\n\n👨‍💻 **Dev:** {pd.DEV_USERNAME}", chat_id=message.chat.id, message_id=status_msg.message_id)


def start_bot():
    if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except:
            pass

    if not BOT_TOKEN:
        print("[-] Please set TELEGRAM_BOT_TOKEN in .env or environment variable.")
        return
        
    print(f"================================================================")
    print(f"  [*] Tell Tims Royal TG Bot by {pd.DEV_NAME} ({pd.DEV_USERNAME}) is ONLINE!")
    print(f"================================================================")
    
    while True:
        try:
            bot.infinity_polling(timeout=20, long_polling_timeout=20)
        except Exception as e:
            print(f"Polling reconnecting in 3s... ({e})")
            time.sleep(3)

if __name__ == "__main__":
    start_bot()
