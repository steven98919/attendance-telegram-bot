import xlsxwriter
from ModulExcel.format import Template_excel
import calendar
from ModulExcel.excel_helper import *
from datetime import date,datetime,time
from dotenv import load_dotenv
import os

# Load the .env file
load_dotenv()

# Get the names as a Python list (strip spaces just in case)
SPECIAL_NAMES = [n.strip() for n in os.getenv("SPECIAL_NAMES", "").split(",")]


format_excel = Template_excel()
process_count = 0

def check_telat_khusus(td):
    try:
        reference_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        target_time = time(9, 30)
        target_datetime = reference_date.replace(hour=target_time.hour, minute=target_time.minute)
        result_datetime = reference_date + td
        if result_datetime <= target_datetime:
            return True
        else:
            return False
    except:
        return False

def send_message(bot, chat_id, message_id, aditional_file_name):
    global process_count
    process_total = 4
    process_count += 1
    presen = int(process_count/process_total*100)
    loading = ""

    for i in range(process_count):
        loading+="██"

    for i in range(process_total-process_count):
        loading+="▒▒"
    
    bot.edit_message_text(f"Mohon tunggu sedang memproses {aditional_file_name} \nProses {process_count}/{process_total} \n{loading} {presen}%",chat_id, message_id)

def process_template_excel(year, employee, bot, chat_id, message_id, aditional_file_name):
    global process_count
    send_message(bot, chat_id, message_id, aditional_file_name)

    workbook_name = f'Rekap {year} {aditional_file_name}.xlsx'
    workbook = xlsxwriter.Workbook(workbook_name)
    send_message(bot, chat_id, message_id, aditional_file_name)
    
    template_kehadiran(year, employee, workbook, bot, chat_id, message_id)
    send_message(bot, chat_id, message_id, aditional_file_name)

    template_cuti(year, employee, workbook, bot, chat_id, message_id)
    send_message(bot, chat_id, message_id, aditional_file_name)
    
    workbook.close()
    process_count = 0
    return workbook_name

def template_kehadiran(year, employee, workbook, bot, chat_id, message_id):
    global format_excel
    worksheet = workbook.add_worksheet("KEHADIRAN")

    start_col_count = 0
    total_employee = len(employee)

    # header
    len_header = len(format_excel.header_text_blue)
    for col in range(0, len_header):
        worksheet.write(2, col, format_excel.header_text_blue[col] , workbook.add_format(format_excel.header_blue))
        start_col_count += 1
        
    for col in range(0, len(format_excel.header_text_orange)):
        worksheet.write(2, col + len_header , format_excel.header_text_orange[col] , workbook.add_format(format_excel.header_orange))
        start_col_count += 1

        for temp in range(0, total_employee):
            row_number = 3 + temp
            worksheet.write(row_number, col + len_header , generate_formulas(row_number+1, col) , workbook.add_format(format_excel.content_orange))

    # freeze and format
    worksheet.freeze_panes(3, start_col_count)
    worksheet.set_column(0, 0 , 15)
    worksheet.set_column(1, 2 , 10)
    worksheet.set_column(3, start_col_count-1 , 8)
    worksheet.set_column(start_col_count, 999, 3, workbook.add_format({'align': 'center'}))
    
    # Other sheet formatting.
    worksheet.merge_range(0, 0, 1, start_col_count-3, "REKAP KEHADIRAN KARYAWAN - TAHUN "+str(year), workbook.add_format(format_excel.title))
    worksheet.merge_range(0, start_col_count-2, 1, start_col_count-1, "Generate Date: "+str(date.today()), workbook.add_format(format_excel.content_orange))

    # temp value for processing
    year_calendar = generate_year_calendar(year)
    month_temp = start_col_count
    week_temp = start_col_count
    day_temp = start_col_count

    # header month and week
    for month in range(0,12):
        count_day = count_2d_array(year_calendar[month])
        month_name = calendar.month_name[month+1]
        worksheet.merge_range(0, month_temp, 0, count_day + month_temp - 1, month_name, workbook.add_format(format_excel.title_month))
        month_temp += count_day

        for week in year_calendar[month]:
            if(len(week) <= 1):
                worksheet.write(1, week_temp, "week"+get_week_number(year, month+1, week[0]), workbook.add_format(format_excel.title_week))
            else:
                worksheet.merge_range(1, week_temp, 1, len(week) + week_temp -1,  "WEEK "+get_week_number(year, month+1, week[0]), workbook.add_format(format_excel.title_week))
            week_temp += len(week)

            # looping for day in week
            for day in week:
                # check if day is minus or not, if minus == weekend 
                if(day >= 0):
                    worksheet.write(2, day_temp, day, workbook.add_format(format_excel.header_blue))
                else:
                    worksheet.write(2, day_temp, change_sign(day), workbook.add_format(format_excel.weekend_red))
                day_temp += 1

    
    # conditional formating
    month_temp -= 1
    conditional_formating_template(worksheet,workbook, month_temp, start_col_count, total_employee)

    # employee name and divisi 
    e_temp = 3 #mulai dari kolom 4

    date_range = get_start_and_end_days(year)
    att = MergeAttendanceAndLeaveInfo(date_range[0], date_range[1])

    for e in employee:
        worksheet.write(e_temp, 0, e['name'] , workbook.add_format(format_excel.content_blue))
        worksheet.write(e_temp, 1, e['divisi'] , workbook.add_format(format_excel.content_blue))
        worksheet.write(e_temp, 2, e['role'] , workbook.add_format(format_excel.content_blue))
        worksheet.set_row(e_temp, 30)
        for n,i in att[e['name']].items():
            temp_col = start_col_count + day_of_year(n)-1
            
            if isinstance(i, dict):
                type_value = i.get('type', '')
                note_value = i.get('note', '')

                if type_value == "T" and e['name'] in SPECIAL_NAMES and check_telat_khusus(note_value):
                    worksheet.write(e_temp, temp_col, "A", workbook.add_format(format_excel.content_blue))
                    worksheet.write_comment(e_temp, temp_col, f"{note_value}")
                else:
                    worksheet.write(e_temp, temp_col, f"{type_value}", workbook.add_format(format_excel.content_blue))
                    worksheet.write_comment(e_temp, temp_col, f"{note_value}")
            else:
                worksheet.write(e_temp, temp_col, f"{i}", workbook.add_format(format_excel.content_blue))

        e_temp += 1

    # ======================================= Input User ============================================

def template_cuti(year, employee, workbook, bot, chat_id, message_id):
    global format_excel
    worksheet = workbook.add_worksheet("CUTI")

    start_col_count = 0
    total_employee = len(employee)

    # freeze and format
    worksheet.freeze_panes(5, start_col_count)
    worksheet.set_column(0, 8, 15)

    len_header = len(format_excel.header_text_blue)
    for col in range(0, len_header):
        worksheet.merge_range(2, col, 3, col, format_excel.header_text_blue[col] , workbook.add_format(format_excel.header_blue))
        worksheet.write(4, col , format_excel.header_text_alphabet[col] , workbook.add_format(format_excel.header_blue))
        start_col_count += 1

        
    def write_cuti_section(worksheet, col, title, header_text, start_row, total_employee):
        worksheet.merge_range(2, col, 3, col, title, workbook.add_format(format_excel.header_orange))
        worksheet.write(4, col, header_text, workbook.add_format(format_excel.header_orange))

        for temp in range(0, total_employee):
            row_number = start_row + temp
            worksheet.write(row_number, col, generate_formulas_cuti(row_number + 1, col, year), workbook.add_format(format_excel.content_orange))


        return col + 1

    start_row = 5

    col += 1
    col = write_cuti_section(worksheet, col, f'SISA CUTI {datetime.now().year-1}', format_excel.header_text_alphabet[col], start_row, total_employee)
    col = write_cuti_section(worksheet, col, f'CUTI {year}', format_excel.header_text_alphabet[col], start_row, total_employee)

    # worksheet.merge_range(2, col, 2, col + 2, 'PENGAMBILAN CUTI', workbook.add_format(format_excel.header_orange))
    # col += 1

    col = write_cuti_section(worksheet, col, f'CUTI BERSAMA PEMERINTAH {year}', format_excel.header_text_alphabet[col], start_row, total_employee)
    col = write_cuti_section(worksheet, col, 'CUTI TAHUNAN KARYAWAN', format_excel.header_text_alphabet[col], start_row, total_employee)
    col = write_cuti_section(worksheet, col, 'TOTAL(F + G)', format_excel.header_text_alphabet[col], start_row, total_employee)

    # worksheet.merge_range(2, col, 3, col, 'HAK CUTI KARYAWAN(D+E) - H', workbook.add_format(format_excel.header_orange))
    write_cuti_section(worksheet, col, 'HAK CUTI KARYAWAN(D+E) - H', format_excel.header_text_alphabet[col], start_row, total_employee)

    start_col_count += 6

    
    # Other sheet formatting.
    worksheet.merge_range(0, 0, 1, start_col_count-3, "REKAP CUTI KARYAWAN - TAHUN "+str(year), workbook.add_format(format_excel.title))
    worksheet.merge_range(0, start_col_count-2, 1, start_col_count-1, "Generate Date: "+str(date.today()), workbook.add_format(format_excel.content_orange))

    e_temp = 5
    for e in employee:
        worksheet.write(e_temp, 0, e['name'] , workbook.add_format(format_excel.content_blue))
        worksheet.write(e_temp, 1, e['divisi'] , workbook.add_format(format_excel.content_blue))
        worksheet.write(e_temp, 2, e['role'] , workbook.add_format(format_excel.content_blue))
        worksheet.write(e_temp, 3, e['sisa_cuti'] , workbook.add_format(format_excel.content_orange))

        worksheet.set_row(e_temp, 30)
        e_temp += 1

def conditional_formating_template(worksheet,workbook, month_temp, start_col_count, total_employee):
    values_to_check = ['K', 'HD', 'CB', 'C', 'S', 'T', 'A', '']
    total_employee = total_employee+2
    for value in values_to_check:
        if value == '':
            format = 'blank'
        else:
            format = value
        
        criteria = {'type': 'cell', 'criteria': '==', 'value': f'"{value}"', 'format': workbook.add_format(getattr(format_excel, f'cell_containt_{format.lower()}'))}
        worksheet.conditional_format(3, start_col_count, total_employee, month_temp, criteria)

