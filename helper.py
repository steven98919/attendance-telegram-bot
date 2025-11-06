from datetime import datetime, date
from db import jam_masuk_rahmadan,jam_masuk_normal,tgl_ahkir_rahmadan,tgl_awal_rahmadan
from dotenv import load_dotenv
import os

# Load the .env file
load_dotenv()

# Get the names as a Python list (strip spaces just in case)
SPECIAL_NAMES = [n.strip() for n in os.getenv("SPECIAL_NAMES", "").split(",")]

def output_help():
    return f'''
Berikut adalah perintah-perintah yang tersedia di Absensi Telebot:

Laporan
/rekap - Rekap Laporan kehadiran karyawan
/rekap_divisi - Rekap Laporan kehadiran karyawan perDivisi
/export - Laporan tahunan berbentuk PDF perDivisi

Status
/today - Mendapatkan status absensi karyawan per hari ini
/history - Mendapatkan status absensi karyawan ke belakang

Izin 
/edit_izin - Mengedit perizinan karyawan
/input_izin - Menginput perizinan karyawan 

Cuti Bersama
/show_cuti_bersama - Menampilkan daftar cuti bersama tahunan
/edit_cuti_bersama - Mengedit cuti bersama tahunan

Cuti Karyawan
/show_cuti_karyawan - Menampilkan daftar cuti bersama tahunan
/edit_cuti_karyawan - Mengedit cuti untuk seluruh karyawan

Laporan Perorangan/Divisi 
/summary - Menampilkan Laporan perorangan atau perteam dalam format PDF

Absensi 
/input_absen - Menambahkan Absen secara manual ke Sistem
/delete_absen - Menghapus Absen secara manual ke Sistem
    '''

# Absen
# /edit_absen - Mengedit absensi karyawan secara manual ❌
# /input_absen - Menginput absensi karyawan secara manual ❌

def get_day_name(d_name):
    if d_name == "Monday":
        return "Senin"
    elif d_name == "Tuesday":
        return "Selasa"
    elif d_name == "Wednesday":
        return "Rabu"
    elif d_name == "Thursday":
        return "Kamis"
    elif d_name == "Friday":
        return "Jumat"
    elif d_name == "Saturday":
        return "Sabtu"
    elif d_name == "Sunday":
        return "Minggu"
    else:
        return 0
    
def check_ramadan(date_str):
    date = datetime.strptime(date_str, '%Y-%m-%d')
    awal_rahmadan = datetime.strptime(tgl_awal_rahmadan, '%Y-%m-%d')
    ahkir_rahmadan = datetime.strptime(tgl_ahkir_rahmadan, '%Y-%m-%d')

    if awal_rahmadan <= date <= ahkir_rahmadan:
        return True
    else:
        return False

format_time = jam_masuk_normal

def check_telat(scan_date, name, tgl):
    global format_time
    if name in SPECIAL_NAMES:
        time_to_check_str = "09:30:00"
    elif check_ramadan(tgl):
        time_to_check_str = jam_masuk_rahmadan
        format_time = jam_masuk_rahmadan
    else:
        time_to_check_str = jam_masuk_normal

    # Parse the time strings into datetime objects
    given_time = datetime.strptime(scan_date, "%H:%M:%S")
    time_to_check = datetime.strptime(time_to_check_str, "%H:%M:%S")

    # Compare the times
    if time_to_check > given_time:
        return True
    else:
        return False
    
def template_daily_report(date,att,cuti):
    #template tepat waktu
    date = convert_to_date(date)
    text_tepat = "Absen hari ini yang tepat waktu \U00002705 : \n"
    
    #template telat waktu, now untuk menentukan tnaggal hari ini, day menentukan day name
    now = date
    day = get_day_name(now.strftime("%A"))

    text_telat_dengan_ket = ""
    #tempalate belum absen
    text_dn = ""
    text_s = ""
    text_c = ""
    text_k = ""
    text_hd = ""
    text_kosong = ""
    text_telat = ""
    status_kosong = []

    cuti_dict = {name: (start_date, end_date, cat, note) for name, start_date, end_date, cat, note in cuti}
    print(cuti_dict)
    for x in att[0]:
        check = check_telat(x['first_time_attendance'], x['name'], str(date))

        if check:
            text_tepat      += x['first_time_attendance'] + "\t\t" + x['name'] + "\n"
        else:
            if x['name'] in cuti_dict:
                type = cuti_dict[x['name']][2]
                note = cuti_dict[x['name']][3]
                if type == 'T':
                    text_telat_dengan_ket      += f"🔹 | "+ x['name'] + " : Masuk pukul " + x['first_time_attendance'] + f" WIB ({note})\n"
            else:
                text_telat      += f"🔹 | "+ x['name'] + " : Masuk pukul " + x['first_time_attendance'] + " WIB\n"
                status_kosong.append(["T",x['name']])

    for x in att[1]:
        if x['name'] in cuti_dict:
            type = cuti_dict[x['name']][2]
            note = cuti_dict[x['name']][3]
            if type == 'C':
                text_c      += f"🔹 | {x['name']} : {note}\n"
            if type == 'S':
                text_s      += f"🔹 | {x['name']} : {note}\n"
            if type == 'DN':
                text_dn      += f"🔹 | {x['name']} : {note}\n"
            if type == 'K':
                text_k      += f"🔹 | {x['name']} : {note}\n"
            if type == 'HD':
                text_hd      += f"🔹 | {x['name']} : {note}\n"
            if type == 'T':
                text_hd      += f"🔹 | "+ x['name'] + F" : (Belum Absen) ({note})\n"
        else:
            text_kosong      += f"🔹 | "+ x['name'] + ":\n"
            status_kosong.append(["C",x['name']])
    
    # if format_time == '08:46:00':
    #     today_time_show = '08:45:00'
    # else:
    #     today_time_show = format_time

    text_main = f"Selamat Siang yth:\nDewan Direksi\nManajemen\n\nMohon izin menyampaikan informasi absensi untuk\n"
    text_main += f"hari *{day}* tanggal *{now.strftime('%d-%m-%Y')}* sebagai berikut:\n\n"
    text_main += f"A. List Karyawan Yang Datang Terlambat (Diatas Jam 08:45:00):\n"
    text_main += "A.1 Dengan keterangan:\n"
    text_main += text_telat_dengan_ket
    text_main += "\n\nA.2 Tidak ada keterangan:\n"
    text_main += text_telat


    #footer
    text_footer = "\n\nB.5 Ijin keluar kantor\nN/A\n\nDemikian informasi ini saya sampaikan.\n\nSalam,\nAntonius Satrio"

    text_null = "\n\nB. List Karyawan Yang Tidak Masuk/Belum Absen hingga jam 10.00:\n"
    text_null += "\nB.1 Ijin keterlambatan:\n"
    text_null += text_hd
    
    text_null += "\nB.2 Ijin tidak masuk kantor:\n"
    text_null += text_c
    text_null += text_k
    text_null += text_s

    text_null += "\nB.3 Ijin Dinas luar kota:\n"
    text_null += text_dn
    text_null += "\nB.4 Tidak ada keterangan:\n"
    text_null += text_kosong

    return {
        'tepat': text_tepat,
        'telat': text_main+text_null+text_footer,
        'list_karyawan' : status_kosong,
    }

def convert_to_date(input_value):
    if isinstance(input_value, str):
        date_object = datetime.strptime(input_value, "%Y-%m-%d").date()
        return date_object
    elif isinstance(input_value, date):
        return input_value
    else:
        raise ValueError("Tipe input tidak didukung")
    
def delete_callback_markup_keyboard(call,bot,del_message=True):
    bot.edit_message_text(chat_id=call.message.chat.id,
                        message_id=call.message.message_id,
                        text=call.message.text,
                        reply_markup=None)
    if del_message:
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
    
def is_number(input_str):
    if input_str:
        return input_str.isdigit()
    else:
        return False
    
def string_to_time(s):
    print(s)
    if s.isnumeric():
        print("The string is numeric.")
        
        if 3 <= len(s) <= 4:  # Ensure the length of the string is between 2 and 4 characters
            first_part = s[:-2]  # Extract the hour part (everything except the last two characters)
            last_two_chars = s[-2:]  # Extract the minute part (last two characters)
            
            hour = first_part
            minute = last_two_chars
            
            if 1 <= int(hour) <= 24 and 0 <= int(minute) < 60:  # Check if hour is valid (1-12) and minute is valid (0-59)
                return hour, minute
            else:
                print(f"Invalid time. Hour: {hour} (must be 1-24), Minute: {minute} (must be 0-59).")
                return False, f"Invalid time. Hour: {hour} (must be 1-24), Minute: {minute} (must be 0-59)."
        else:
            print(f"The string has a length of {len(s)}, which is not valid for a time format.")
            return False, f"The string has a length of {len(s)}, which is not valid for a time format."
            
    else:
        print("The string is not numeric.")
        return False, "The string is not numeric."
        
    
    return None, None
