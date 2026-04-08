#!/usr/bin/env python3
"""Send maintenance completion message"""

import telebot
from dotenv import load_dotenv
import os

load_dotenv()
BOT_API = os.getenv('BOT_API')
bot = telebot.TeleBot(BOT_API)

message = """✅ *MAINTENANCE SELESAI*

Bot sudah aktif kembali dan siap digunakan\.

Update yang diterapkan:
• Retry mechanism untuk export otomatis
• Pilihan 3 minggu terakhir di /export
• Optimasi sistem logging

Silakan gunakan bot seperti biasa\. 🚀"""

try:
    bot.send_message(911196345, message, parse_mode='MarkdownV2')
    print("✅ Maintenance done message sent to ID 911196345")
except Exception as e:
    print(f"❌ Error: {e}")
