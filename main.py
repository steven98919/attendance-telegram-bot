import telebot
import os
from dotenv import load_dotenv
from ModulExcel.excel import process_template_excel
from ModulPdf.pdf import process_template_export
from ModulSummary.summary import process_template_summary
from ModulGenerateCuti.Cuti import process_cuti_automatis
from db import *
from helper import *
import schedule
import telegram
import time
from datetime import datetime, date, timedelta
import threading
from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP
from telegram.ext import CallbackQueryHandler
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# env variable
load_dotenv()
BOT_API = os.getenv('BOT_API')
bot = telebot.TeleBot(BOT_API)

# Variabel global untuk menyimpan data karyawan
all_employees = []
tele_id_admin = [int(id) for id in os.getenv("TELEBOT_ID_ADMIN", "").split(",") if id]
print(tele_id_admin)
def check_telegram_id(client_telegram_id):
    global tele_id_admin
    if client_telegram_id not in tele_id_admin:
        print(f"Unauthorized access. Do nothing or return an error message. id = {client_telegram_id}")
        return True
    else:
        print("Authorized access. Proceed with the request.")
        return False
    
# Fungsi untuk mendapatkan data karyawan jika belum tersedia
def get_or_fetch_employees():
    global all_employees
    if not all_employees:
        all_employees = GetAllEmployee(orderby="name")
    return all_employees

# main command
@bot.message_handler(commands=['help', 'start'])
def start(message):
    if check_telegram_id(message.chat.id):
        return None
    bot.send_message(message.chat.id, output_help())

def error_message(message):
    bot.send_message(message.chat.id, "❌ Error, mohon hubungi Dev.")


global_get_izin_by_date = {}

# ==================================================history start===============================================
@bot.message_handler(commands=['history'])
def start(message):
    if check_telegram_id(message.chat.id):
        return None
    calendar, step = DetailedTelegramCalendar(calendar_id=1, max_date=date.today()).build()
    bot.send_message(message.chat.id,
                     f"Select {LSTEP[step]}",
                     reply_markup=calendar)

@bot.callback_query_handler(func=DetailedTelegramCalendar.func(calendar_id=1))
def cal(c):
    result, key, step = DetailedTelegramCalendar(calendar_id=1, max_date=date.today()).process(c.data)
    if not result and key:
        bot.edit_message_text(f"Select {LSTEP[step]}",
                              c.message.chat.id,
                              c.message.message_id,
                              reply_markup=key)
    elif result:
        att = getAttendance_and_non_attendance(result)
        cuti = ShowingIzin(result,result, True)
        output = template_daily_report(result, att, cuti)

        bot.send_message(c.message.chat.id, output['tepat'])
        bot.send_message(c.message.chat.id, output['telat'])

        list_karyawan = output['list_karyawan']
        if not len(list_karyawan) == 0 :
            input_after_today_and_hisotry(list_karyawan, c.message.chat.id, result)

        bot.edit_message_text(f"You selected {result}",
                              c.message.chat.id,
                              c.message.message_id,
                              reply_markup=None)
# ==================================================history end====================================================

# ==================================================today start====================================================
@bot.message_handler(commands=['today'])
def start(message):
    if check_telegram_id(message.chat.id):
        return None
    insert_message_history_to_windows(message.chat.id,message.text,message.chat.username)
    today_process(message.chat.id)

def today_process(chat_id):
    att = getAttendance_and_non_attendance(date.today())
    print(att)
    cuti = ShowingIzin(date.today(),date.today(), True)

    output = template_daily_report(date.today(), att, cuti)

    bot.send_message(chat_id, output['tepat'])
    bot.send_message(chat_id, output['telat'])

    list_karyawan = output['list_karyawan']
    if not len(list_karyawan) == 0 :
        input_after_today_and_hisotry(list_karyawan, chat_id, date.today())

def input_after_today_and_hisotry(list_karyawan, chat_id, date):
    global global_get_izin_by_date
    global_get_izin_by_date[chat_id] = date

    inline_keyboard = InlineKeyboardMarkup(row_width=2)
    for employee in list_karyawan:
        id_user = Get_Data_from_Table('user', condition=f"name = '{employee[1]}'")[0][0]
        if employee[0] == "C":
            inline_keyboard.add(InlineKeyboardButton(employee[1], callback_data=f'inputIzin_{date}.{id_user}'))
        elif employee[0] == "T":
            inline_keyboard.add(InlineKeyboardButton(f'Telat | {employee[1]}', callback_data=f'inputCutiJenisIzin_{date}.{id_user}.1.T'))

    inline_keyboard.add(InlineKeyboardButton('Batal', callback_data='batal'))
    
    bot.send_message(chat_id, text="Untuk input izin, pilih nama berikut:", reply_markup=inline_keyboard)
    

        
# ==================================================today end====================================================

# ==================================================export start====================================================
@bot.message_handler(commands=['export'])
def start(message):
    if check_telegram_id(message.chat.id):
        return None
    
    # bypass inlinekeybaord
    # proses_export(datetime.now().year, message.chat.id, message_id=False)
    year = datetime.now().year

    inline_keyboard = InlineKeyboardMarkup(row_width=2)
    inline_keyboard.add(
        InlineKeyboardButton(year, callback_data=f'export_{year}'),
        InlineKeyboardButton(year-1, callback_data=f'export_{year-1}'),
        InlineKeyboardButton(year-2, callback_data=f'export_{year-2}'),
        InlineKeyboardButton(year-3, callback_data=f'export_{year-3}'),
    )
    inline_keyboard.add(InlineKeyboardButton('Batal', callback_data='batal'))
    bot.send_message(message.chat.id, text="Choose a year:", reply_markup=inline_keyboard)

def proses_export(year, chat_id, message_id=False):
    if message_id:
        bot.edit_message_text(f"Mohon tunggu",chat_id, message_id)
        
    current_date = datetime.now().date()
    iso_year, iso_week, iso_day = current_date.isocalendar()
    
    # iso_week = iso_week
    print(iso_year, iso_week, iso_day)
    
    divisi = Get_Data_from_Table('user_divisi')
    for d in divisi:
        if message_id:
            bot.edit_message_text(f"Mohon tunggu Memproses Export Divisi {d[2]}",chat_id, message_id)
            
        employee = GetAllEmployeeForRekap(condition=f'code_dep = "{d[1]}" AND role = "Staff"', year=int(year)-1)
        print(employee)
        filename = f'W{iso_week}-{d[2]}.pdf'
        if not len(employee) == 0:
            process_template_export(employee, year, filename)
            doc_path = f'{os.getcwd()}/new-bot/ModulPdf/{filename}'
            with open(doc_path, 'rb') as doc:
                bot.send_document(chat_id, doc)
            
    # supervisi
    if message_id:
        bot.edit_message_text(f"Mohon tunggu Memproses Export Supervisor",chat_id, message_id)
        
    employee = GetAllEmployeeForRekap(condition=f'(role = "Spv" OR role = "JuniorSpv" OR role = "SE Advisor")',year=int(year)-1)
    filename = f'W{iso_week}-SUPERVISOR.pdf'
    if not len(employee) == 0:
        process_template_export(employee, year, filename)
        doc_path = f'{os.getcwd()}/new-bot/ModulPdf/{filename}'
        with open(doc_path, 'rb') as doc:
            bot.send_document(chat_id, doc)
        
    
    # Manager
    if message_id:
        bot.edit_message_text(f"Mohon tunggu Memproses Export Manager",chat_id, message_id)
    employee = GetAllEmployeeForRekap(condition=f'code_dep = "MANAGEMENT"',year=int(year)-1)
    filename = f'W{iso_week}-MANAGEMENT.pdf'
    if not len(employee) == 0:
        process_template_export(employee, year, filename)
        doc_path = f'{os.getcwd()}/new-bot/ModulPdf/{filename}'
        with open(doc_path, 'rb') as doc:
            bot.send_document(chat_id, doc)
            
    # ALL
    if message_id:
        bot.edit_message_text(f"Mohon tunggu Memproses Export Seluruh Karyawan",chat_id, message_id)
    employee = GetAllEmployeeForRekap(year=int(year)-1)
    filename = f'W{iso_week}-SeluruhKaryawan.pdf'
    if not len(employee) == 0:
        process_template_export(employee, year, filename)
        doc_path = f'{os.getcwd()}/new-bot/ModulPdf/{filename}'
        with open(doc_path, 'rb') as doc:
            bot.send_document(chat_id, doc)

# ==================================================export end====================================================

# ==================================================AutoInputSisaCuti Start====================================================
@bot.message_handler(commands=['AutoInputSisaCuti'])
def start(message):
    if check_telegram_id(message.chat.id):
        return None
    
    year = datetime.now().year -1 
    employee = GetAllEmployeeForRekap(year=year-1)
    if not len(employee) == 0:
        value = process_cuti_automatis(employee, year)
    
    for v in value:
        # print(v[0], v[-1])
        output = Input_Data_Into_Table('user_cuti', ['id_user','tahun', 'sisa_cuti'], [v[0],year,v[-1]])
        if output:
            bot.send_message(message.chat.id, text=f"✅ Berhasil input {v[1]} sisa cuti {year} sebanyak {v[-1]} ")
        else:
            bot.send_message(message.chat.id, text=f"❌ Gagal input {v[1]} sisa cuti {year} sebanyak {v[-1]} ")
            
    


# ==================================================AutoInputSisaCuti end====================================================


# ==================================================rekap start====================================================
@bot.message_handler(commands=['rekap'])
def start(message):
    if check_telegram_id(message.chat.id):
        return None
    year = datetime.now().year

    inline_keyboard = InlineKeyboardMarkup(row_width=2)
    inline_keyboard.add(
        InlineKeyboardButton(year, callback_data=f'rekap_{year}'),
        InlineKeyboardButton(year-1, callback_data=f'rekap_{year-1}'),
        InlineKeyboardButton(year-2, callback_data=f'rekap_{year-2}'),
        InlineKeyboardButton(year-3, callback_data=f'rekap_{year-3}'),
    )
    inline_keyboard.add(InlineKeyboardButton('Batal', callback_data='batal'))
    bot.send_message(message.chat.id, text="Choose a year:", reply_markup=inline_keyboard)
    # bot.send_message(message.chat.id, text="Sedang dinonaktifkan, mohon hubungi Dev.")

def proses_rekap(year, chat_id, message_id):
    bot.edit_message_text(f"Mohon tunggu",chat_id, message_id)
    employee = GetAllEmployeeForRekap(year=int(year)-1)
    wordbook_name = process_template_excel(int(year), employee, bot, chat_id, message_id, 'Seluruh Karyawan')
    doc_path = f'{os.getcwd()}/{wordbook_name}'
    with open(doc_path, 'rb') as doc:
        bot.send_document(chat_id, doc)
# ==================================================rekap end====================================================

        
# ==================================================rekap divisi start====================================================
@bot.message_handler(commands=['rekap_divisi'])
def start(message):
    if check_telegram_id(message.chat.id):
        return None
    year = datetime.now().year

    inline_keyboard = InlineKeyboardMarkup(row_width=2)
    inline_keyboard.add(
        InlineKeyboardButton(year, callback_data=f'rekapdivisi_{year}'),
        InlineKeyboardButton(year-1, callback_data=f'rekapdivisi_{year-1}'),
        InlineKeyboardButton(year-2, callback_data=f'rekapdivisi_{year-2}'),
        InlineKeyboardButton(year-3, callback_data=f'rekapdivisi_{year-3}'),
    )
    inline_keyboard.add(InlineKeyboardButton('Batal', callback_data='batal'))
    bot.send_message(message.chat.id, text="Choose a year:", reply_markup=inline_keyboard)

def proses_rekap_divisi(year, chat_id, message_id):
    # staff perdivisi
    divisi = Get_Data_from_Table('user_divisi')
    for d in divisi:
        bot.edit_message_text(f"Mohon tunggu Memproses Rekap Divisi {d[2]}",chat_id, message_id)
        employee = GetAllEmployeeForRekap(condition=f'code_dep = "{d[1]}" AND role = "Staff"',year=int(year)-1)
        if not len(employee) == 0:
            wordbook_name = process_template_excel(int(year), employee, bot, chat_id, message_id, d[1])
            doc_path = f'{os.getcwd()}/{wordbook_name}'
            with open(doc_path, 'rb') as doc:
                bot.send_document(chat_id, doc)
    
    # supervisi
    bot.edit_message_text(f"Mohon tunggu Memproses Rekap Supervisor",chat_id, message_id)
    employee = GetAllEmployeeForRekap(condition=f'(role = "Spv" OR role = "JuniorSpv" OR role = "SE Advisor")',year=int(year)-1)
    if not len(employee) == 0:
        wordbook_name = process_template_excel(int(year), employee, bot, chat_id, message_id, 'Supervisor')
        doc_path = f'{os.getcwd()}/{wordbook_name}'
        with open(doc_path, 'rb') as doc:
            bot.send_document(chat_id, doc)
    
    # Manager
    bot.edit_message_text(f"Mohon tunggu Memproses Rekap Manager",chat_id, message_id)
    employee = GetAllEmployeeForRekap(condition=f'code_dep = "MANAGEMENT"',year=int(year)-1)
    if not len(employee) == 0:
        wordbook_name = process_template_excel(int(year), employee, bot, chat_id, message_id, 'Manager')
        doc_path = f'{os.getcwd()}/{wordbook_name}'
        with open(doc_path, 'rb') as doc:
            bot.send_document(chat_id, doc)
# ==================================================rekap divisi end====================================================
    
# ==================================================input_cuti_karyawan start====================================================
@bot.message_handler(commands=['input_izin'])
def start(message):
    if check_telegram_id(message.chat.id):
        return None
    process_input_izin_2(message)

def process_input_izin_2(message):
    calendar, step = DetailedTelegramCalendar(calendar_id=2).build()
    bot.send_message(message.chat.id,
                     f"Select {LSTEP[step]}",
                     reply_markup=calendar)
    
@bot.callback_query_handler(func=DetailedTelegramCalendar.func(calendar_id=2))
def cal(c):
    result, key, step = DetailedTelegramCalendar(calendar_id=2).process(c.data)
    if not result and key:
        bot.edit_message_text(f"Select {LSTEP[step]}",
                              c.message.chat.id,
                              c.message.message_id,
                              reply_markup=key)
    elif result:
        delete_callback_markup_keyboard(c, bot)
        process_input_izin(c.message,result, page=1)

def process_input_izin(message, date, page=1):
    employees = get_or_fetch_employees()

    start_index = (page - 1) * 10
    end_index = min(page * 10, len(employees))
    current_page_employees = employees[start_index:end_index]

    inline_keyboard = InlineKeyboardMarkup(row_width=4)

    for i, employee in enumerate(current_page_employees):
        inline_keyboard.add(InlineKeyboardButton(employee['name'], callback_data=f'inputIzin_{date}.{employee["id"]}'))

    pref = InlineKeyboardButton(' ', callback_data=f' ')
    next = InlineKeyboardButton(' ', callback_data=f' ')
    batal = InlineKeyboardButton('Tutup', callback_data='batal')

    if start_index > 0:
        pref = InlineKeyboardButton('<<', callback_data=f'pageInputIzin_{page - 1}.{date}')
    
    if end_index < len(employees):
        next = InlineKeyboardButton('>>', callback_data=f'pageInputIzin_{page + 1}.{date}')

    pagination = []
    total_page = int(len(employees)/10)+1
    for i in range(1, total_page):  
        pagination.append(InlineKeyboardButton(str(i), callback_data=f'pageInputIzin_{i}.{date}'))
    inline_keyboard.row(pref, *pagination, next)
    inline_keyboard.add(batal)

    bot.send_message(message.chat.id, text=f"List data Karyawan | {start_index}-{len(employees)} \nPilih karyawan:", reply_markup=inline_keyboard)

def process_input_izin_3(message, data):
    inline_keyboard = InlineKeyboardMarkup(row_width=3)
    inline_keyboard.add(
        InlineKeyboardButton('1', callback_data=f'inputCutiJumlahHari_{data}.1'),
        InlineKeyboardButton('2', callback_data=f'inputCutiJumlahHari_{data}.2'),
        InlineKeyboardButton('3', callback_data=f'inputCutiJumlahHari_{data}.3'),
        InlineKeyboardButton('4', callback_data=f'inputCutiJumlahHari_{data}.4'),
        InlineKeyboardButton('5', callback_data=f'inputCutiJumlahHari_{data}.5'),
    )
    inline_keyboard.add(InlineKeyboardButton('Batal', callback_data='batal'))
    bot.send_message(message.chat.id, text="Pilih Jumlah Hari Izin:", reply_markup=inline_keyboard)

def process_input_izin_4(message, data):
    inline_keyboard = InlineKeyboardMarkup(row_width=3)
    inline_keyboard.add(
        InlineKeyboardButton('DINAS (DN)', callback_data=f'inputCutiJenisIzin_{data}.DN'),
        InlineKeyboardButton('Sakit (S)', callback_data=f'inputCutiJenisIzin_{data}.S'),
        InlineKeyboardButton('Cuti (C)', callback_data=f'inputCutiJenisIzin_{data}.C'),
        InlineKeyboardButton('Cuti Khusus (K)', callback_data=f'inputCutiJenisIzin_{data}.K'),
        InlineKeyboardButton('Setengah Hari (HD)', callback_data=f'inputCutiJenisIzin_{data}.HD'),
        InlineKeyboardButton('Telat (T)', callback_data=f'inputCutiJenisIzin_{data}.T'),
    )
    inline_keyboard.add(InlineKeyboardButton('Batal', callback_data='batal'))
    bot.send_message(message.chat.id, text="Pilih Jenis Izin:", reply_markup=inline_keyboard)

def process_input_izin_5(message, data):
    nama = data.split('.')
    user = Get_Data_from_Table('user', condition=f"id = {nama[1]}")[0]
    bot.send_message(message.chat.id, f"Masukan Note untuk {user[1]}:")
    bot.register_next_step_handler(message, lambda m: process_input_izin_7(m, data))

global_input_note_id = {}

def process_input_izin_7(message, data):
    note = message.text
    global global_input_note_id
    global_input_note_id[message.chat.id] = note

    data = data.split('.')
    user = Get_Data_from_Table('user', condition=f"id = {data[1]}")[0]
    tgl_awal = date.fromisoformat(data[0])
    tgl_akhir = tgl_awal + timedelta(days=int(data[2])-1)
    jenis_izin = data[3]

    inline_keyboard = InlineKeyboardMarkup(row_width=2)
    inline_keyboard.add(
        InlineKeyboardButton('Ya', callback_data=f'inputCutiKonfirmasi_{data[1]}.{jenis_izin}.{tgl_awal}.{tgl_akhir}.true'),
        InlineKeyboardButton('Tidak', callback_data=f'inputCutiKonfirmasi_{data}.false'),
    )

    bot.send_message(message.chat.id, f"Apakah Anda yakin ingin menginput izin berikut:\n\nNama : {user[1]}\nTanggal Awal : {tgl_awal}\nTanggal Akhir : {tgl_akhir}\nJenis Izin : {jenis_izin}\nNote : {note}", reply_markup=inline_keyboard)


def process_input_izin_6(message, data):
    data = data.split(".")
    data.pop()
    if message.chat.id in global_input_note_id:
        data.append(global_input_note_id[message.chat.id])
        del global_input_note_id[message.chat.id]
    else:
        data.append(' ')

    output = Input_Data_Into_Table('user_izin', ['id_user', 'jenis_izin', 'tgl_awal', 'tgl_akhir', 'note'], [*data])
    if output == True:
        bot.send_message(message.chat.id, f"Izin berhasil di input izin ✅")
    else:
        bot.send_message(message.chat.id, f"Izin Gagal di input ❌")
        
    if message.chat.id in global_get_izin_by_date:
        date = global_get_izin_by_date[message.chat.id]
        att = getAttendance_and_non_attendance(date)
        cuti = ShowingIzin(date,date, True)
        output = template_daily_report(date, att, cuti)

        list_karyawan = output['list_karyawan']
        if not len(list_karyawan) == 0 :
            input_after_today_and_hisotry(list_karyawan, message.chat.id, date)
        else:
            del global_get_izin_by_date[message.chat.id]
    else:
        process_input_izin(message, data[2])

# ==================================================input_cuti_karyawan end====================================================

# ==================================================edit_cuti_karyawan start====================================================
@bot.message_handler(commands=['edit_izin'])
def start(message):
    if check_telegram_id(message.chat.id):
        return None
    process_edit_izin(message)

def process_edit_izin(message, page=1):
    employees = get_or_fetch_employees()

    start_index = (page - 1) * 10
    end_index = min(page * 10, len(employees))
    current_page_employees = employees[start_index:end_index]

    inline_keyboard = InlineKeyboardMarkup(row_width=4)

    for i, employee in enumerate(current_page_employees):
        inline_keyboard.add(InlineKeyboardButton(employee['name'], callback_data=f'editIzin_{employee["id"]}'))

    pref = InlineKeyboardButton(' ', callback_data=f' ')
    next = InlineKeyboardButton(' ', callback_data=f' ')
    batal = InlineKeyboardButton('Tutup', callback_data='batal')

    if start_index > 0:
        pref = InlineKeyboardButton('<<', callback_data=f'pageEditIzin_{page - 1}')
    
    if end_index < len(employees):
        next = InlineKeyboardButton('>>', callback_data=f'pageEditIzin_{page + 1}')

    pagination = []
    total_page = int(len(employees)/10)+1
    for i in range(1, total_page):  
        pagination.append(InlineKeyboardButton(str(i), callback_data=f'pageEditIzin_{i}'))
    inline_keyboard.row(pref, *pagination, next)
    inline_keyboard.add(batal)

    bot.send_message(message.chat.id, text=f"List data Karyawan | {start_index}-{len(employees)} \nPilih karyawan:", reply_markup=inline_keyboard)

def process_edit_izin_2(message, data):
    user = Get_Data_from_Table('user', condition=f"id = {data}")[0]
    user_izin = Get_Data_from_Table('user_izin', condition=f"id_user = {data}", order_by="id desc", limit="9")

    inline_keyboard = InlineKeyboardMarkup(row_width=1)
    button = []

    if len(user_izin) == 0:
        inline_keyboard.add(InlineKeyboardButton('Tidak ada Izin', callback_data='pageEditIzin_1'))
    else:
        for v, i in enumerate(user_izin):  
            text = f"{v+1} | {i[3]} → {i[4]} ({i[2]})"
            button.append(InlineKeyboardButton(f'{text}', callback_data=f'editIzinKaryawan_{i[0]}'))
            

        inline_keyboard.add(*button)
    
    inline_keyboard.add(InlineKeyboardButton('Batal', callback_data='batal'))

    bot.send_message(message.chat.id, text=f"Pilih Izin karyawan {user[1]} :", reply_markup=inline_keyboard)

global_selected_id_izin = {}

def process_edit_izin_3(message, data):
    global global_selected_id_izin
    user_izin = Get_Data_from_Table('user_izin', select="user.name, user_izin.*",condition=f"user_izin.id = {data}", join="LEFT JOIN user ON user.id = user_izin.id_user")[0]
    global_selected_id_izin[message.chat.id] = data

    inline_keyboard = InlineKeyboardMarkup(row_width=4)

    inline_keyboard.add(
        InlineKeyboardButton(f'Jenis Izin', callback_data=f'editIzinKaryawanDetail_jenisizin.{user_izin[1]}.{user_izin[3]}'),
        InlineKeyboardButton(f'Tanggal Awal', callback_data=f'editIzinKaryawanDetail_tglawal.{user_izin[1]}.{user_izin[4]}'),
        InlineKeyboardButton(f'Tanggal Akhir', callback_data=f'editIzinKaryawanDetail_tglakhir.{user_izin[1]}.{user_izin[2]}'),
        InlineKeyboardButton(f'Note', callback_data=f'editIzinKaryawanDetail_note.{user_izin[1]}.{user_izin[2]}'),

        InlineKeyboardButton(f'{user_izin[3]}', callback_data=f'editIzinKaryawanDetail_jenisizin.{user_izin[1]}.{user_izin[3]}'),
        InlineKeyboardButton(f'{user_izin[4]}', callback_data=f'editIzinKaryawanDetail_tglawal.{user_izin[1]}.{user_izin[4]}'),
        InlineKeyboardButton(f'{user_izin[5]}', callback_data=f'editIzinKaryawanDetail_tglakhir.{user_izin[1]}.{user_izin[2]}'),
        InlineKeyboardButton(f'{user_izin[6]}', callback_data=f'editIzinKaryawanDetail_note.{user_izin[1]}.{user_izin[2]}')
    )
    
    inline_keyboard.row(
        InlineKeyboardButton('Tutup', callback_data='batal'),
        InlineKeyboardButton('Hapus ❌', callback_data=f'editIzinKaryawanDetail_del.{user_izin[1]}')
    )

    bot.send_message(message.chat.id, text=f"Edit Izin karyawan {user_izin[0]} :", reply_markup=inline_keyboard)

def process_edit_izin_edit_delete(message, data):
    user_izin = Get_Data_from_Table('user_izin', select="user.name, user_izin.*",condition=f"user_izin.id = {data}", join="LEFT JOIN user ON user.id = user_izin.id_user")[0]

    inline_keyboard = InlineKeyboardMarkup(row_width=2)
    inline_keyboard.add(
        InlineKeyboardButton('Hapus ❌', callback_data=f'editIzinKaryawanDeleteKonfirmasi_{data}'),
        InlineKeyboardButton('Batal', callback_data='batal'),
    )

    bot.send_message(message.chat.id, f"Apakah Anda yakin ingin menghapus izin berikut:\n\nNama : {user_izin[0]}\nTanggal Awal : {user_izin[4]}\nTanggal Akhir : {user_izin[5]}\nJenis Izin : {user_izin[3]}", reply_markup=inline_keyboard)

def process_edit_izin_edit_delete_process(message, data):
    output = delete_data_from_table('user_izin', f'id = {data}')
    if output == True:
        bot.send_message(message.chat.id, f"Izin berhasil di Hapus ✅")
    else:
        bot.send_message(message.chat.id, f"Izin Gagal di Hapus ❌")
    process_edit_izin(message)

def process_edit_izin_edit_jenisizin(message, data):
    inline_keyboard = InlineKeyboardMarkup(row_width=3)
    inline_keyboard.add(
        InlineKeyboardButton('DINAS (DN)', callback_data=f'editIzinKaryawanUpdate_jenisizin.{data}.DN'),
        InlineKeyboardButton('Sakit (S)', callback_data=f'editIzinKaryawanUpdate_jenisizin.{data}.S'),
        InlineKeyboardButton('Cuti (C)', callback_data=f'editIzinKaryawanUpdate_jenisizin.{data}.C'),
        InlineKeyboardButton('Cuti Khusus (K)', callback_data=f'editIzinKaryawanUpdate_jenisizin.{data}.K'),
        InlineKeyboardButton('Setengah Hari (HD)', callback_data=f'editIzinKaryawanUpdate_jenisizin.{data}.HD'),
        InlineKeyboardButton('Telat (T)', callback_data=f'editIzinKaryawanUpdate_jenisizin.{data}.T'),
    )
    inline_keyboard.add(InlineKeyboardButton('Batal', callback_data='batal'))
    bot.send_message(message.chat.id, text="Pilih Jenis Izin:", reply_markup=inline_keyboard)

def process_edit_izin_edit_tglawal(message):
    calendar, step = DetailedTelegramCalendar(calendar_id=3).build()
    bot.send_message(message.chat.id,
                     f"Select {LSTEP[step]}",
                     reply_markup=calendar)
    
@bot.callback_query_handler(func=DetailedTelegramCalendar.func(calendar_id=3))
def cal(c):
    result, key, step = DetailedTelegramCalendar(calendar_id=3).process(c.data)
    if not result and key:
        bot.edit_message_text(f"Select {LSTEP[step]}",
                              c.message.chat.id,
                              c.message.message_id,
                              reply_markup=key)
    elif result:
        global global_selected_id_izin
        if c.message.chat.id not in global_selected_id_izin:
            error_message(c.message)
            delete_callback_markup_keyboard(c,bot)
        else:
            user_izin_id = global_selected_id_izin[c.message.chat.id]
            delete_callback_markup_keyboard(c, bot)
            output = Update_Data_from_Table('user_izin', f'tgl_awal = "{result}"', f'id = {user_izin_id}')
            if output == True:
                bot.send_message(c.message.chat.id, text=f"Edit Berhasil ✅")
            else:
                bot.send_message(c.message.chat.id, f"Edit Gagal hubungi Dev ❌")

            process_edit_izin_3(c.message, user_izin_id)

def process_edit_izin_edit_tglakhir(message):
    calendar, step = DetailedTelegramCalendar(calendar_id=4).build()
    bot.send_message(message.chat.id,
                     f"Select {LSTEP[step]}",
                     reply_markup=calendar)
    
@bot.callback_query_handler(func=DetailedTelegramCalendar.func(calendar_id=4))
def cal(c):
    result, key, step = DetailedTelegramCalendar(calendar_id=4).process(c.data)
    if not result and key:
        bot.edit_message_text(f"Select {LSTEP[step]}",
                              c.message.chat.id,
                              c.message.message_id,
                              reply_markup=key)
    elif result:
        global global_selected_id_izin
        if c.message.chat.id not in global_selected_id_izin:
            error_message(c.message)
            delete_callback_markup_keyboard(c,bot)
        else:
            user_izin_id = global_selected_id_izin[c.message.chat.id]
            delete_callback_markup_keyboard(c, bot)
            output = Update_Data_from_Table('user_izin', f'tgl_akhir = "{result}"', f'id = {user_izin_id}')
            if output == True:
                bot.send_message(c.message.chat.id, text=f"Edit Berhasil ✅")
            else:
                bot.send_message(c.message.chat.id, f"Edit Gagal hubungi Dev ❌")

            process_edit_izin_3(c.message, user_izin_id)

def process_edit_izin_edit_note(message):
    bot.send_message(message.chat.id, f"Masukan Note:")
    bot.register_next_step_handler(message, process_edit_izin_edit_note_2)

def process_edit_izin_edit_note_2(message):
    global global_selected_id_izin
    if message.chat.id not in global_selected_id_izin:
        error_message(message)
    else:
        user_izin_id = global_selected_id_izin[message.chat.id]
        output = Update_Data_from_Table('user_izin', f'note = "{message.text}"', f'id = {user_izin_id}')
        if output == True:
            bot.send_message(message.chat.id, text=f"Edit Berhasil ✅")
        else:
            bot.send_message(message.chat.id, f"Edit Gagal hubungi Dev ❌")

        process_edit_izin_3(message, user_izin_id)


# ==================================================edit_cuti_karyawan end====================================================
    

# ==================================================show_cuti_bersama start====================================================
@bot.message_handler(commands=['show_cuti_bersama'])
def start(message):
    if check_telegram_id(message.chat.id):
        return None
    data = Get_Data_from_Table('user_cuti_bersama')
    output = "Total Cuti Bersama \n\n"
    for d in data:
        output += f"{d[0]} = {d[1]} Hari \n "

    bot.send_message(message.chat.id, output)

# ==================================================show_cuti_bersama end====================================================


# ==================================================edit_cuti_bersama start====================================================
@bot.message_handler(commands=['edit_cuti_bersama'])
def start(message):
    if check_telegram_id(message.chat.id):
        return None
    year = datetime.now().year

    inline_keyboard = InlineKeyboardMarkup(row_width=2)
    inline_keyboard.add(
        InlineKeyboardButton(year, callback_data=f'editcutibersama_{year}'),
        InlineKeyboardButton(year-1, callback_data=f'editcutibersama_{year-1}'),
        InlineKeyboardButton(year-2, callback_data=f'editcutibersama_{year-2}'),
        InlineKeyboardButton(year-3, callback_data=f'editcutibersama_{year-3}'),
    )
    inline_keyboard.add(InlineKeyboardButton('Batal', callback_data='batal'))
    bot.send_message(message.chat.id, text="Choose a year:", reply_markup=inline_keyboard)

def process_edit_cuti_bersama(message, year):
    bot.send_message(message.chat.id, text=f"Masukan Total Cuti Bersama Tahun {year} =")
    bot.register_next_step_handler(message, lambda m: process_input_cuti_bersama(m, year))

def process_input_cuti_bersama(message, year):
    if message.text == "/batal" :
        bot.send_message(message.chat.id, text=f"Membatalkan Command")
        bot.clear_step_handler_by_chat_id(chat_id=message.chat.id)
    elif is_number(message.text):
        temp = Get_Data_from_Table('user_cuti_bersama', condition=f"tahun = {year}")
        if len(temp) == 0 :
            output = Input_Data_Into_Table('user_cuti_bersama', ['tahun', 'total_cuti_bersama'], [year, message.text])
            
        else:
            output = Update_Data_from_Table('user_cuti_bersama', f'total_cuti_bersama = {message.text}', f'tahun = {year}')
        if output == True:
            bot.send_message(message.chat.id, text=f"Input Berhasil ✅, Cuti bersama tahun {year} = {message.text}")
        else:
            bot.send_message(message.chat.id, f"Input Gagal hubungi Dev ❌")
        bot.clear_step_handler_by_chat_id(chat_id=message.chat.id)
    else:
        bot.send_message(message.chat.id, text=f"{message.text} bukan merupakan angka, silahkan masukan input angka kembali")
        bot.register_next_step_handler(message, lambda m: process_input_cuti_bersama(m, year))

# ==================================================edit_cuti_bersama end====================================================


# ==================================================edit_cuti_karyawan start====================================================
@bot.message_handler(commands=['edit_cuti_karyawan'])
def start(message):
    if check_telegram_id(message.chat.id):
        return None
    year = datetime.now().year

    inline_keyboard = InlineKeyboardMarkup(row_width=2)
    inline_keyboard.add(
        InlineKeyboardButton(year-1, callback_data=f'editcutikaryawan_{year-1}'),
        InlineKeyboardButton(year-2, callback_data=f'editcutikaryawan_{year-2}'),
        InlineKeyboardButton(year-3, callback_data=f'editcutikaryawan_{year-3}'),
        InlineKeyboardButton(year-3, callback_data=f'editcutikaryawan_{year-4}'),
    )
    inline_keyboard.add(InlineKeyboardButton('Batal', callback_data='batal'))
    bot.send_message(message.chat.id, text="Choose a year:", reply_markup=inline_keyboard)

def button_edit_cuti_karyawan(message, year, page=1):
    employees = get_or_fetch_employees()

    start_index = (page - 1) * 10
    end_index = min(page * 10, len(employees))
    current_page_employees = employees[start_index:end_index]

    inline_keyboard = InlineKeyboardMarkup(row_width=4)

    for i, employee in enumerate(current_page_employees):
        inline_keyboard.add(InlineKeyboardButton(employee['name'], callback_data=f'editcutiname_{employee["id"]}.{year}'))

    pref = InlineKeyboardButton(' ', callback_data=f' ')
    next = InlineKeyboardButton(' ', callback_data=f' ')
    batal = InlineKeyboardButton('Tutup', callback_data='batal')

    if start_index > 0:
        pref = InlineKeyboardButton('<<', callback_data=f'page_{page - 1}.{year}')
    
    if end_index < len(employees):
        next = InlineKeyboardButton('>>', callback_data=f'page_{page + 1}.{year}')

    pagination = []
    total_page = int(len(employees)/10)+1
    for i in range(1, total_page):  
        pagination.append(InlineKeyboardButton(str(i), callback_data=f'page_{i}.{year}'))
    inline_keyboard.row(pref, *pagination, next)
    inline_keyboard.add(batal)

    bot.send_message(message.chat.id, text=f"List data Karyawan | {start_index}-{len(employees)} \nPilih karyawan:", reply_markup=inline_keyboard)

def input_cuti_karyawan(message, year, user_id):
    user = Get_Data_from_Table('user', condition=f"id = {user_id}")
    bot.send_message(message.chat.id, text=f"Masukan Total Cuti {user[0][1]} Tahun {year} =")
    bot.register_next_step_handler(message, lambda m: process_input_cuti_karyawan(m, year, user_id))

def process_input_cuti_karyawan(message, year, user_id):
    user = Get_Data_from_Table('user', condition=f"id = {user_id}")

    if message.text == "/batal" :
        bot.send_message(message.chat.id, text=f"Membatalkan Command")
        bot.clear_step_handler_by_chat_id(chat_id=message.chat.id)
    elif is_number(message.text):
        temp = Get_Data_from_Table('user_cuti', condition=f"tahun = {year} and id_user = {user_id}")
        if len(temp) == 0 :
            output = Input_Data_Into_Table('user_cuti', ['id_user', 'tahun', 'sisa_cuti'], [user_id, year, message.text])
        else:
            output = Update_Data_from_Table('user_cuti', f'sisa_cuti = {message.text}', f'tahun = {year} and id_user = {user_id}')

        if output == True:
            bot.send_message(message.chat.id, text=f"Input Berhasil ✅, Total Cuti {user[0][1]} tahun {year} = {message.text}")
        else:
            bot.send_message(message.chat.id, f"Input Gagal hubungi Dev ❌")

        bot.clear_step_handler_by_chat_id(chat_id=message.chat.id)
    else:
        bot.send_message(message.chat.id, text=f"{message.text} bukan merupakan angka, silahkan masukan input angka kembali")
        bot.register_next_step_handler(message, lambda m: process_input_cuti_karyawan(m, year, user_id))
# ==================================================edit_cuti_karyawan end====================================================

# ==================================================show_cuti_karyawan start====================================================
@bot.message_handler(commands=['show_cuti_karyawan'])
def start(message):
    if check_telegram_id(message.chat.id):
        return None
    year = datetime.now().year

    inline_keyboard = InlineKeyboardMarkup(row_width=2)
    inline_keyboard.add(
        InlineKeyboardButton(year-1, callback_data=f'showcutikaryawan_{year-1}'),
        InlineKeyboardButton(year-2, callback_data=f'showcutikaryawan_{year-2}'),
        InlineKeyboardButton(year-3, callback_data=f'showcutikaryawan_{year-3}'),
        InlineKeyboardButton(year-4, callback_data=f'showcutikaryawan_{year-4}'),
    )
    inline_keyboard.add(InlineKeyboardButton('Batal', callback_data='batal'))
    bot.send_message(message.chat.id, text="Choose a year:", reply_markup=inline_keyboard)

def process_show_cuti_karyawan(message, year):
    data = Get_Data_from_Table('user', condition=f"user_cuti.tahun = {year}", join="JOIN user_cuti ON user.id = user_cuti.id_user")
    output =f"Cuti Karyawan Tahun {year} \n\n"
    for d in data:
        output += f"{d[1]}: {d[-1]} Hari\n"

    bot.send_message(message.chat.id, output)
# ==================================================show_cuti_karyawan end====================================================


# ==================================================Summary start====================================================
@bot.message_handler(commands=['summary'])
def start(message):
    if check_telegram_id(message.chat.id):
        return None
    year = datetime.now().year

    inline_keyboard = InlineKeyboardMarkup(row_width=2)
    inline_keyboard.add(
        InlineKeyboardButton(year, callback_data=f'summary_{year}'),
        InlineKeyboardButton(year-1, callback_data=f'summary_{year-1}'),
        InlineKeyboardButton(year-2, callback_data=f'summary_{year-2}'),
        InlineKeyboardButton(year-3, callback_data=f'summary_{year-3}'),
    )
    inline_keyboard.add(InlineKeyboardButton('Batal', callback_data='batal'))
    bot.send_message(message.chat.id, text="Choose a year:", reply_markup=inline_keyboard)

def Proses_Summary(message, data):
    inline_keyboard = InlineKeyboardMarkup(row_width=2)
    inline_keyboard.add(
        InlineKeyboardButton('Seluruh Karyawan', callback_data=f'summary1_{data}.semua'),
        InlineKeyboardButton('Perdivisi', callback_data=f'summary1_{data}.divisi'),
        InlineKeyboardButton('Spv', callback_data=f'summary1_{data}.spv'),
        InlineKeyboardButton('Manager', callback_data=f'summary1_{data}.manager'),
    )
    inline_keyboard.add(InlineKeyboardButton('Batal', callback_data='batal'))
    bot.send_message(message.chat.id, text="Choose a option:", reply_markup=inline_keyboard)
    
def Proses_Summary1(message, data):
    year = int(data.split('.')[0])
    option = data.split('.')[-1]
    if option == 'semua':
        employee = GetAllEmployeeForRekap(year=int(year)-1)
        for emp in employee:
            emp = emp['name']
            filename = f'{emp}.pdf'
            process_template_summary(emp, filename, year)
            doc_path = f'{os.getcwd()}/new-bot/ModulSummary/{filename}'
            with open(doc_path, 'rb') as doc:
                bot.send_document(message.chat.id, doc)
    elif option == 'spv':
        employee = GetAllEmployeeForRekap(condition=f'(role = "Spv" OR role = "JuniorSpv" OR role = "SE Advisor")',year=int(year)-1)
        for emp in employee:
            emp = emp['name']
            filename = f'{emp}.pdf'
            process_template_summary(emp, filename, year)
            doc_path = f'{os.getcwd()}/new-bot/ModulSummary/{filename}'
            with open(doc_path, 'rb') as doc:
                bot.send_document(message.chat.id, doc)
    elif option == 'manager':
        employee = GetAllEmployeeForRekap(condition=f'code_dep = "MANAGEMENT"',year=int(year)-1)
        for emp in employee:
            emp = emp['name']
            filename = f'{emp}.pdf'
            process_template_summary(emp, filename, year)
            doc_path = f'{os.getcwd()}/new-bot/ModulSummary/{filename}'
            with open(doc_path, 'rb') as doc:
                bot.send_document(message.chat.id, doc)
    elif option == 'divisi':
        divisi = Get_Data_from_Table('user_divisi')
        inline_keyboard = InlineKeyboardMarkup(row_width=2)
        for d in divisi:
            inline_keyboard.add(
                InlineKeyboardButton(d[1], callback_data=f'summary2_{data}.{d[1]}'),
            )
        inline_keyboard.add(InlineKeyboardButton('Batal', callback_data='batal'))
        bot.send_message(message.chat.id, text="Choose a option:", reply_markup=inline_keyboard)

def Proses_Summary2(message, data):
    year = int(data.split('.')[0])
    option = data.split('.')[-1]
    employee = GetAllEmployeeForRekap(condition=f'code_dep = "{option}" AND role = "Staff"',year=int(year)-1)
    for emp in employee:
        emp = emp['name']
        filename = f'{emp}.pdf'
        process_template_summary(emp, filename, year)
        doc_path = f'{os.getcwd()}/new-bot/ModulSummary/{filename}'
        with open(doc_path, 'rb') as doc:
            bot.send_document(message.chat.id, doc)
# ==================================================Summary end====================================================


# ==================================================input_absen start====================================================
@bot.message_handler(commands=['input_absen'])
def start(message):
    if check_telegram_id(message.chat.id):
        return None
    process_input_absen(message)

def process_input_absen(message):
    calendar, step = DetailedTelegramCalendar(calendar_id=5, max_date=date.today()).build()
    bot.send_message(message.chat.id,
                     f"Select {LSTEP[step]}",
                     reply_markup=calendar)
    
@bot.callback_query_handler(func=DetailedTelegramCalendar.func(calendar_id=5))
def cal(c):
    result, key, step = DetailedTelegramCalendar(calendar_id=5, max_date=date.today()).process(c.data)
    if not result and key:
        bot.edit_message_text(f"Select {LSTEP[step]}",
                              c.message.chat.id,
                              c.message.message_id,
                              reply_markup=key)
    elif result:
        delete_callback_markup_keyboard(c, bot)
        process_input_absen_2(c.message,result, page=1)

def process_input_absen_2(message, date, page=1):
    employees = get_or_fetch_employees()

    start_index = (page - 1) * 10
    end_index = min(page * 10, len(employees))
    current_page_employees = employees[start_index:end_index]

    inline_keyboard = InlineKeyboardMarkup(row_width=4)

    for i, employee in enumerate(current_page_employees):
        pin = Get_User_Pin_by_name(employee['name'])[0]
        name_split = employee["name"].split(" ")
        if(len(name_split)>=2):
            name = f"{name_split[0]} {name_split[1]}"
        else:
            name = f"{name_split[0]}"

        inline_keyboard.add(InlineKeyboardButton(employee['name'], callback_data=f'inputAbsen_{date}.{name}.{pin[1]}'))

    pref = InlineKeyboardButton(' ', callback_data=f' ')
    next = InlineKeyboardButton(' ', callback_data=f' ')
    batal = InlineKeyboardButton('Tutup', callback_data='batal')

    if start_index > 0:
        pref = InlineKeyboardButton('<<', callback_data=f'pageInputAbsen_{page - 1}.{date}')
    
    if end_index < len(employees):
        next = InlineKeyboardButton('>>', callback_data=f'pageInputAbsen_{page + 1}.{date}')

    pagination = []
    total_page = int(len(employees)/10)+1
    for i in range(1, total_page):  
        pagination.append(InlineKeyboardButton(str(i), callback_data=f'pageInputAbsen_{i}.{date}'))
    inline_keyboard.row(pref, *pagination, next)
    inline_keyboard.add(batal)

    bot.send_message(message.chat.id, text=f"List data Karyawan | {start_index}-{len(employees)} \nPilih karyawan:", reply_markup=inline_keyboard)

def process_input_absen_3(message, data):
    bot.send_message(message.chat.id, text="Input Waktu Absen Tanpa Tanda petik: \n(EX: 955 \U00002705 || 09:55 ❌)")
    bot.register_next_step_handler(message, lambda msg: process_input_absen_4(msg, data))
    
def process_input_absen_4(message, data):
    hour, min = string_to_time(message.text)
    print(hour,min)
    if hour is not False:
        dat = data.split('.')
        inline_keyboard = InlineKeyboardMarkup(row_width=2)
        inline_keyboard.add(
            InlineKeyboardButton('Ya', callback_data=f'inputAbsen2_{data}.{hour}.{min}'),
            InlineKeyboardButton('Tidak', callback_data=f'batal'),
        )
        print(message.chat.id)
        bot.send_message(message.chat.id, f"Apakah Anda yakin ingin menginput absen berikut:\n\nNama : {dat[1]}\nTanggal : {dat[0]}\nPukul : {hour}:{min}", reply_markup=inline_keyboard)
    else:
        bot.send_message(message.chat.id, f"{min}")
        process_input_absen_3(message, data)
# ==================================================input_absen end====================================================

# ==================================================delete_absen start====================================================
@bot.message_handler(commands=['delete_absen'])
def start(message):
    if check_telegram_id(message.chat.id):
        return None
    process_delete_absen(message)

def process_delete_absen(message):
    calendar, step = DetailedTelegramCalendar(calendar_id=6, max_date=date.today()).build()
    bot.send_message(message.chat.id,
                     f"Select {LSTEP[step]}",
                     reply_markup=calendar)
    
@bot.callback_query_handler(func=DetailedTelegramCalendar.func(calendar_id=6))
def cal(c):
    result, key, step = DetailedTelegramCalendar(calendar_id=6, max_date=date.today()).process(c.data)
    if not result and key:
        bot.edit_message_text(f"Select {LSTEP[step]}",
                              c.message.chat.id,
                              c.message.message_id,
                              reply_markup=key)
    elif result:
        delete_callback_markup_keyboard(c, bot)
        process_delete_absen_2(c.message,result)

def process_delete_absen_2(message, date):
    absen = getAttendance_and_non_attendance(date)
    
    inline_keyboard = InlineKeyboardMarkup(row_width=2)
    for a in absen[0]:
        if(a['first_time_attendance']):
            pin = Get_User_Pin_by_name(a['name'])[0]
            name_split = a["name"].split(" ")
            if(len(name_split)>=2):
                name = f"{name_split[0]} {name_split[1]}"
            else:
                name = f"{name_split[0]}"
            inline_keyboard.add(InlineKeyboardButton(f"{a['name']} {a['first_time_attendance']}", callback_data=f"deleteAbsen_{date}.{name}.{pin[1]}.{a['first_time_attendance']}"))
    
    if(len(absen[0]) <= 0):
        bot.send_message(message.chat.id, text=f"Tidak ada Absen pada tanggal {date}")
    else:
        bot.send_message(message.chat.id, text=f"Pilih absen utnuk di hapus:", reply_markup=inline_keyboard)



# ==================================================delete_absen end====================================================

# ==================================================identifier start====================================================
@bot.callback_query_handler(func=lambda call: True)
def start(call):
    if check_telegram_id(call.message.chat.id):
        return None
    identifier = call.data.split('_')
    callback_identifier(identifier[0], identifier[-1], call)

def callback_identifier(identifier, data, call):
    def rekap():
        proses_rekap(data, call.message.chat.id, call.message.message_id)
        delete_callback_markup_keyboard(call,bot)

    def export():
        proses_export(data, call.message.chat.id, call.message.message_id)
        delete_callback_markup_keyboard(call,bot)
        
    def rekapdivisi():
        proses_rekap_divisi(data, call.message.chat.id, call.message.message_id)
        delete_callback_markup_keyboard(call,bot)

    def editcutibersama():
        delete_callback_markup_keyboard(call,bot)
        process_edit_cuti_bersama(call.message, data)

    def editcutikaryawan():
        delete_callback_markup_keyboard(call,bot)
        button_edit_cuti_karyawan(call.message, data)

    def editcutiname():
        delete_callback_markup_keyboard(call,bot)
        newdata = data.split('.')
        input_cuti_karyawan(call.message, newdata[1], newdata[0])

    def page():
        delete_callback_markup_keyboard(call,bot)
        newdata = data.split('.')
        button_edit_cuti_karyawan(call.message, newdata[1], int(newdata[0]))

# =====================================input izin ==============================
    def pageInputIzin():
        delete_callback_markup_keyboard(call,bot)
        newdata = data.split('.')
        process_input_izin(call.message, newdata[1], int(newdata[0]))
    
    def inputIzin():
        delete_callback_markup_keyboard(call,bot)
        process_input_izin_3(call.message, data)

    def inputCutiJumlahHari():
        delete_callback_markup_keyboard(call,bot)
        process_input_izin_4(call.message, data)

    def inputCutiJenisIzin():
        delete_callback_markup_keyboard(call,bot)
        process_input_izin_5(call.message, data)

    def inputCutiKonfirmasi():
        global global_get_izin_by_date

        delete_callback_markup_keyboard(call,bot,False)
        temp = data.split('.')
        if temp[-1] == 'true':
            process_input_izin_6(call.message, data)
        else:
            if call.message.chat.id in global_get_izin_by_date:
                date = global_get_izin_by_date[call.message.chat.id]
                att = getAttendance_and_non_attendance(date)
                cuti = ShowingIzin(date,date, True)
                output = template_daily_report(date, att, cuti)

                list_karyawan = output['list_karyawan']
                if not len(list_karyawan) == 0 :
                    input_after_today_and_hisotry(list_karyawan, call.message.chat.id, date)
                else:
                    del global_get_izin_by_date[call.message.chat.id]
            else:
                process_input_izin(call.message, temp[0])

# =====================================input izin ==============================
            
# =====================================edit izin ==============================
    def pageEditIzin():
        delete_callback_markup_keyboard(call,bot)
        process_edit_izin(call.message, int(data))
    
    def editIzin():
        delete_callback_markup_keyboard(call,bot)
        process_edit_izin_2(call.message, data)

    def editIzinKaryawan():
        delete_callback_markup_keyboard(call,bot)
        process_edit_izin_3(call.message, data)

    def editIzinKaryawanDetail():
        delete_callback_markup_keyboard(call,bot)
        temp = data.split('.')
        if temp[0] == 'del':
            process_edit_izin_edit_delete_process(call.message,temp[1])
        elif temp[0] == 'jenisizin':
            process_edit_izin_edit_jenisizin(call.message,temp[1])
        elif temp[0] == 'tglawal':
            process_edit_izin_edit_tglawal(call.message)
        elif temp[0] == 'tglakhir':
            process_edit_izin_edit_tglakhir(call.message)
        elif temp[0] == 'note':
            process_edit_izin_edit_note(call.message)
        else:
            error_message(call.message)
    
    def editIzinKaryawanUpdate():
        delete_callback_markup_keyboard(call,bot)
        temp = data.split('.')
        output = False
        if temp[0] == 'jenisizin':
            output = Update_Data_from_Table('user_izin', f'jenis_izin = "{temp[2]}"', f'id = {temp[1]}')

        
        if output == True:
            bot.send_message(call.message.chat.id, text=f"Edit Berhasil ✅")
        else:
            bot.send_message(call.message.chat.id, f"Edit Gagal hubungi Dev ❌")

        process_edit_izin_3(call.message, temp[1])

# =====================================edit izin ==============================

    def showcutikaryawan():
        delete_callback_markup_keyboard(call,bot)
        process_show_cuti_karyawan(call.message, data)

    def default():
        # error_message(call.message)
        return True
    
    def batal():
        bot.send_message(call.message.chat.id, '❌ Perintah Dibatalkan.')
        global global_get_izin_by_date
        if call.message.chat.id in global_get_izin_by_date:
            del global_get_izin_by_date[call.message.chat.id]
        # Hapus markup keyboard
        delete_callback_markup_keyboard(call, bot)
        
    # =====================================summary ==============================

    def ProsesSummary():
        delete_callback_markup_keyboard(call,bot)
        Proses_Summary(call.message, data)
        
    def ProsesSummary1():
        delete_callback_markup_keyboard(call,bot)
        Proses_Summary1(call.message, data)
        
    def ProsesSummary2():
        delete_callback_markup_keyboard(call,bot)
        Proses_Summary2(call.message, data)
        
    # =====================================summary ==============================
    
    # =====================================input absen ==============================

    def ProsesAbsen():
        delete_callback_markup_keyboard(call,bot)
        process_input_absen_3(call.message, data)
        
    def pageProsesAbsen():
        delete_callback_markup_keyboard(call,bot)
        newdata = data.split('.')
        process_input_absen_2(call.message, newdata[1], int(newdata[0]))
        
    def ProsesAbsen2():
        delete_callback_markup_keyboard(call,bot)
        print(data)
        dat = data.split('.')
        pin = dat[2]
        date = dat[0]
        nama = dat[1]
        hour = dat[3]
        min = dat[4]
                    
        first_name = call.message.chat.first_name
        last_name = call.message.chat.last_name
        username = call.message.chat.username
        user_id = call.message.chat.id

        # Determine the name to display
        if first_name and last_name:
            executor = f"{first_name} {last_name}"
        elif first_name:
            executor = first_name
        elif username:
            executor = username
        else:
            executor = str(user_id)
            
        result = input_absensi_to_windows(pin,date,hour,min,executor)
        if(result is True):
            global tele_id_admin
            for id in tele_id_admin:
                bot.send_message(id, text=f"Input Absen Berhasil ✅, dengan detail sebagai berikut:\n\nNama : {nama}\nTanggal Absen : {date}\nJam Absen : {hour}:{min}\nPelaksana : {executor}")
        else:
            bot.send_message(call.message.chat.id, f"Input Gagal hubungi Dev ❌")
            
    def deleteAbsen():
        delete_callback_markup_keyboard(call,bot)
        print(data)
        dat = data.split('.')
        inline_keyboard = InlineKeyboardMarkup(row_width=2)
        inline_keyboard.add(
            InlineKeyboardButton('Ya', callback_data=f'deleteAbsen2_{data}'),
            InlineKeyboardButton('Tidak', callback_data=f'batal'),
        )

        bot.send_message(call.message.chat.id, f"Apakah Anda yakin ingin menghapus absen berikut:\n\nNama : {dat[1]}\nTanggal : {dat[0]}\nPukul : {dat[3]}", reply_markup=inline_keyboard)
        
        
    def deleteAbsen2():
        delete_callback_markup_keyboard(call,bot)
        print(data)
        dat = data.split('.')
        pin = dat[2]
        nama = dat[1]
        scan_time = f"{dat[0]} {dat[3]}"
        result = delete_absensi_from_windows(pin,scan_time)
        if(result is True):
            global tele_id_admin
            first_name = call.message.chat.first_name
            last_name = call.message.chat.last_name
            username = call.message.chat.username
            user_id = call.message.chat.id

            # Determine the name to display
            if first_name and last_name:
                pelaksana = f"{first_name} {last_name}"
            elif first_name:
                pelaksana = first_name
            elif username:
                pelaksana = username
            else:
                pelaksana = str(user_id)
                
            for id in tele_id_admin:
                bot.send_message(id, text=f"Delete Absen Berhasil ✅, dengan detail sebagai berikut:\n\nNama : {nama}\nTanggal Absen : {dat[0]}\nJam Absen : {dat[3]}\nPelaksana : {pelaksana}")
        else:
            bot.send_message(call.message.chat.id, f"Delete Gagal hubungi Dev ❌")
    # =====================================input absen ==============================


    switch_dict = {
        'rekap': rekap,
        'export': export,
        'rekapdivisi': rekapdivisi,
        'batal': batal,
        'editcutibersama': editcutibersama,
        'editcutikaryawan': editcutikaryawan,
        'page': page,
        'editcutiname': editcutiname,
        'showcutikaryawan': showcutikaryawan,
        'pageInputIzin': pageInputIzin,
        'inputIzin': inputIzin,
        'inputCutiJumlahHari' : inputCutiJumlahHari,
        'inputCutiJenisIzin' : inputCutiJenisIzin,
        'inputCutiKonfirmasi' : inputCutiKonfirmasi,
        'pageEditIzin' : pageEditIzin,
        'editIzin' : editIzin,
        'editIzinKaryawan' : editIzinKaryawan,
        'editIzinKaryawanDetail' : editIzinKaryawanDetail,
        'editIzinKaryawanUpdate' : editIzinKaryawanUpdate,
        'summary': ProsesSummary,
        'summary1': ProsesSummary1,
        'summary2': ProsesSummary2,
        'inputAbsen': ProsesAbsen,
        'pageInputAbsen': pageProsesAbsen,
        'inputAbsen2': ProsesAbsen2,
        'deleteAbsen': deleteAbsen,
        'deleteAbsen2': deleteAbsen2,
    }

    return switch_dict.get(identifier, default)()
# ==================================================identifier end====================================================

# ==================================================scheduled====================================================
# Function to send a scheduled message
def send_scheduled_message():
    for id in tele_id_admin:
        today_process(id)
        
def export_scheduled_message():
    year = datetime.now().year
    for id in tele_id_admin:
        proses_export(year, id)

# Schedule the job to run every day at 10 o'clock
schedule.every().sunday.at("16:00").do(export_scheduled_message)

schedule.every().monday.at("10:16").do(send_scheduled_message)
schedule.every().tuesday.at("10:16").do(send_scheduled_message)
schedule.every().wednesday.at("10:16").do(send_scheduled_message)
schedule.every().thursday.at("10:16").do(send_scheduled_message)
schedule.every().friday.at("10:16").do(send_scheduled_message)

# Function to run the polling loop in a separate thread
def polling_thread():
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            print(f"Error in polling: {e}")
            time.sleep(5)

# Start the polling thread
polling_thread = threading.Thread(target=polling_thread)
polling_thread.start()

# Keep the main thread running for the scheduled tasks
while True:
    schedule.run_pending()
    time.sleep(1)
