#!/usr/bin/env python3
"""Send changelog to specific telegram ID"""

import telebot
from dotenv import load_dotenv
import os

load_dotenv()
BOT_API = os.getenv('BOT_API')
bot = telebot.TeleBot(BOT_API)

# Load admin IDs
tele_id_admin = [int(id) for id in os.getenv("TELEBOT_ID_ADMIN", "").split(",") if id]

changelog = """📋 *UPDATE SISTEM*
_9 Maret 2026_

━━━━━━━━━━━━━━━━━
🔴 *PERUBAHAN PENTING*

*1️⃣ Retry Mechanism \- Weekly Report*
Export otomatis \(Minggu 16:00\) sekarang:
  ✓ Retry 3x otomatis jika gagal
  ✓ Jeda 5 menit per retry
  ✓ Notifikasi admin jika tetap gagal

*2️⃣ Pilihan Week \- Menu /export*
Bisa pilih 3 minggu terakhir:
  ✓ Pilih tahun → pilih minggu \(W11, W10, W9\)
  ✓ Data akurat sesuai periode minggu
  ✓ Berguna jika report otomatis gagal

━━━━━━━━━━━━━━━━━
➕ *TAMBAHAN*

*3️⃣ Optimasi Logging*
  • Format: bot\-log\-dd\-mm\-yyyy\.log
  • Rotasi harian, simpan 7 hari

━━━━━━━━━━━━━━━━━
✅ *Status: Active*"""

maintenance_done = """✅ *MAINTENANCE SELESAI*

Bot sudah aktif kembali dan siap digunakan\.
Silakan gunakan bot seperti biasa\. 🚀"""

print(f"📢 Broadcasting to {len(tele_id_admin)} admins...")
print(f"Admin IDs: {tele_id_admin}\n")

for admin_id in tele_id_admin:
    try:
        print(f"Sending to admin ID {admin_id}...")

        # Send changelog
        bot.send_message(admin_id, changelog, parse_mode='MarkdownV2')
        print(f"  ✅ Changelog sent to {admin_id}")

        # Send maintenance done message
        bot.send_message(admin_id, maintenance_done, parse_mode='MarkdownV2')
        print(f"  ✅ Maintenance done sent to {admin_id}\n")

    except Exception as e:
        print(f"  ❌ Error sending to {admin_id}: {e}\n")

print("✅ Broadcast complete!")
