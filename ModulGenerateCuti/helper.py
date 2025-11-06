from datetime import date,datetime,time
import calendar
from datetime import datetime, date, timedelta
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.pagesizes import A3, landscape
from reportlab.lib.units import inch
from db import Get_Data_from_Table
from collections import defaultdict

def date_range(year):
    first_day = datetime(year, 1, 1)
    last_day = datetime(year, 12, 31)
    formatted_start_day = first_day.strftime("%Y-%m-%d")
    formatted_end_day = last_day.strftime("%Y-%m-%d")

    return formatted_start_day, formatted_end_day


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

# Fungsi untuk membuat PDF
def create_pdf(employee, year, att):

    data_cuti = [
    ]
    
    for e in employee:
        if not e['name'] in att:
            continue
        id = e['id']
        name = e['name']
        divisi = e['divisi']
        role = e['role']
        sisa_cuti = e['sisa_cuti']
        if sisa_cuti == None:
            sisa_cuti=0
    
        cuti_bersama = Get_Data_from_Table('user_cuti_bersama', condition=f'tahun = {year}')
        if len(cuti_bersama) >= 1:
            cuti_bersama = cuti_bersama[0][1]
        else:
            cuti_bersama = 0
        absensi = att[e['name']].values()
        absensi_dan_tanggal = att[e['name']]
        cuti_tahun_ini = 12
        
        monthly_counts = defaultdict(int)

        # Iterate over the data
        for date_str, entry in absensi_dan_tanggal.items():
            if isinstance(entry, dict) and entry.get('type') == 'HD':  # If the entry is a dict and type is 'C'
                # Extract month from the date string and increment the count for that month
                month = date_str.split('-')[1]
                monthly_counts[month] += 1
                
        kalkulasi_hd = 0

        # Print the counts for each month
        for month, count in monthly_counts.items():
            kalkulasi_hd += int(count/2)
        
        absenToList = list(absensi)
        
        for i, item in enumerate(absenToList):
            if isinstance(item, dict):
                absenToList[i] = item['type']
                
        DN = absenToList.count("DN")
        T = absenToList.count("T")
        S = absenToList.count("S")
        C = absenToList.count("C")
        K = absenToList.count("K")
        HD = absenToList.count("HD")
        A = absenToList.count("A") + T + DN + int((HD+1)/2)
        
        jumlah_cuti_karyawan = C + kalkulasi_hd
        total_f_g = jumlah_cuti_karyawan+int(cuti_bersama)
        hak_cuti = sisa_cuti+cuti_tahun_ini - total_f_g

        data_cuti.append([id, name, hak_cuti])
        # data_cuti.append([name, divisi, role, sisa_cuti, cuti_tahun_ini, cuti_bersama, jumlah_cuti_karyawan, total_f_g, hak_cuti])
        

        
    return data_cuti
    