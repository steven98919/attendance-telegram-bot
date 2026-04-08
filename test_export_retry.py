#!/usr/bin/env python3
"""
Test script to simulate scheduled export with retry mechanism
Only sends to test telegram ID: 911196345
"""

import sys
import os
import time
import logging

# Add the project directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import necessary modules
from datetime import datetime
from dotenv import load_dotenv
import telebot

# Load environment
load_dotenv()

# Import from main (this will also initialize the bot)
from main import proses_export, bot, logger

def test_export_with_retry():
    """Simulate export_scheduled_message with retry mechanism for testing"""
    test_id = 911196345
    year = datetime.now().year

    print(f"\n{'='*60}")
    print(f"Testing export with retry mechanism")
    print(f"Target ID: {test_id}")
    print(f"Year: {year}")
    print(f"{'='*60}\n")

    max_retries = 3
    retry_delay = 300  # 5 minutes (we'll use shorter for testing)

    # For testing, use shorter delay
    test_mode = True
    if test_mode:
        retry_delay = 10  # 10 seconds for testing
        print(f"⚠️  TEST MODE: Using {retry_delay}s delay instead of 5 minutes\n")

    for attempt in range(1, max_retries + 1):
        try:
            print(f"🔄 Export attempt {attempt}/{max_retries}")
            logger.info(f"[TEST] Export attempt {attempt}/{max_retries}")

            proses_export(year, test_id)

            print(f"✅ Export completed successfully on attempt {attempt}")
            logger.info("[TEST] Export completed successfully")
            return  # Success, exit function

        except Exception as e:
            print(f"❌ Attempt {attempt}/{max_retries} failed: {str(e)}")
            logger.error(f"[TEST] Export attempt {attempt}/{max_retries} failed: {str(e)}", exc_info=True)

            if attempt < max_retries:
                print(f"⏳ Waiting {retry_delay} seconds before retry...\n")
                logger.info(f"[TEST] Waiting {retry_delay} seconds before retry...")
                time.sleep(retry_delay)
            else:
                # All retries failed, send notification
                print(f"🚨 All {max_retries} retry attempts failed. Sending notification...")
                logger.error("[TEST] All retry attempts failed. Notifying admin...")

                error_message = (
                    "❌ EXPORT WEEKLY REPORT OTOMATIS GAGAL\n"
                    "Harap lakukan export manual."
                )

                try:
                    bot.send_message(test_id, error_message)
                    print(f"✉️  Failure notification sent to ID: {test_id}")
                    logger.info(f"[TEST] Failure notification sent to admin ID: {test_id}")
                except Exception as notify_error:
                    print(f"⚠️  Failed to send notification: {str(notify_error)}")
                    logger.error(f"[TEST] Failed to notify admin {test_id}: {str(notify_error)}")

    print(f"\n{'='*60}")
    print("Test completed")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    test_export_with_retry()
