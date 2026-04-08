#!/bin/bash

# Loop continuous dengan interval 5 detik
while true; do
    # Cek apakah screen "new-telebot" sedang aktif
    if screen -ls | grep -q "new-telebot"; then
        # Jika screen "new-telebot" sedang aktif, print "screen aktif"
        echo "$(date '+%Y-%m-%d %H:%M:%S') - screen aktif"
    else
        # Jika screen "new-telebot" tidak aktif, print "screen aktif" dan jalankan:
        echo "$(date '+%Y-%m-%d %H:%M:%S') - screen tidak aktif, memulai screen..."
        screen -S new-telebot -d -m python3 /home/dev/new-bot/main.py
    fi

    # Tunggu 5 detik sebelum pengecekan berikutnya
    sleep 5
done
