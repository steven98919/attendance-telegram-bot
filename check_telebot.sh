#!/bin/bash

# Cek apakah screen "new-telebot" sedang aktif
if screen -ls | grep -q "new-telebot"; then
    # Jika screen "new-telebot" sedang aktif, print "screen aktif"
    echo "screen aktif"
else
    # Jika screen "new-telebot" tidak aktif, print "screen aktif" dan jalankan:
    echo "screen tidak aktif"
    screen -S new-telebot -d -m python3 /home/dev/new-bot/main.py
fi
