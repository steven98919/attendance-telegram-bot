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
def create_pdf(employee,filename, year, att):
    data_kehadiran = [
        ['NAMA KARYAWAN', 'DIVISI', 'JABATAN', 'HARI KERJA', 'KEHADIRAN (A)', 'DINAS (DN)', 'KETERL\nAMBATAN (T)', 'SAKIT (S)', 'CUTI (C)', 'CUTI KHUSUS (K)', 'SETENGAH HARI (HD)'],
    ]

    data_cuti = [
        ['NAMA KARYAWAN', 'DIVISI', 'JABATAN', f'SISA CUTI {int(year) -1}', f'CUTI {year}', f'PEMAKAIAN CUTI', 'PEMAKAIAN CUTI', 'TOTAL (F+G)', 'HAK CUTI KARYAWAN (D+E-H)'],
        ['NAMA KARYAWAN', 'DIVISI', 'JABATAN', f'SISA CUTI {int(year) -1}', f'CUTI {year}', f'CUTI BERSAMA', 'CUTI TAHUNAN', 'TOTAL (F+G)', 'HAK CUTI KARYAWAN (D+E-H)'],
        ['A','B','C','D','E','F','G','H','I']
    ]
    data_keterlambatan = [
        
    ]
    
    for e in employee:
        if not e['name'] in att:
            continue
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
        HariKerja = A + S + C + K + int(HD/2)
        
        jumlah_cuti_karyawan = C + kalkulasi_hd
        total_f_g = jumlah_cuti_karyawan+int(cuti_bersama)
        hak_cuti = sisa_cuti+cuti_tahun_ini - total_f_g

        data_kehadiran.append([name, divisi, role, str(HariKerja), str(A), str(DN), str(T), str(S), str(C), str(K), str(HD)])
        data_cuti.append([name, divisi, role, sisa_cuti, cuti_tahun_ini, cuti_bersama, jumlah_cuti_karyawan, total_f_g, hak_cuti])

    margin_top = 0.1 * inch
    margin_bottom = 0.1 * inch
    margin_left = 0.1 * inch
    margin_right = 0.1 * inch

    doc = SimpleDocTemplate(f'/home/dev/new-bot/ModulPdf/{filename}', pagesize=landscape(A3), topMargin=margin_top, bottomMargin=margin_bottom, leftMargin=margin_left, rightMargin=margin_right)
    
    styles = getSampleStyleSheet()
    
    # Membuat judul di tengah dan besar
    titleKehadiran = Paragraph(f"<para align='center'><b><font size='16'>REKAP KEHADIRAN KARYAWAN - TAHUN {year}</font></b></para>", styles["Heading1"])
    titleCuti = Paragraph(f"<para align='center'><b><font size='16'>REKAP CUTI KARYAWAN - TAHUN {year}</font></b></para>", styles["Heading1"])
    titleKeterlambatan = Paragraph(f"<para align='center'><b><font size='16'>REKAP JUMLAH TELAT KARYAWAN - TAHUN {year}</font></b></para>", styles["Heading1"])

    titleKeterlambatan.alignment = 1
    titleKehadiran.alignment = 1
    titleCuti.alignment = 1
    
    

    # Membuat waktu pembuatan PDF
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    time_text = Paragraph(f"<font size=8>Dibuat pada: {current_time}</font>", styles["Normal"])
    
    # ==========================Kehadiran
    data_formatted_kehadiran = []
    for i,row in enumerate(data_kehadiran):
        if i == 0:
            data_formatted_kehadiran.append([cell.replace(' ','\n') for cell in row])
        else:
            data_formatted_kehadiran.append([cell for cell in row])
    table_kehadiran = Table(data_formatted_kehadiran, colWidths=[3.0*inch, 1.5*inch, 1.5*inch, 1*inch, 1*inch, 1*inch, 1*inch, 1*inch, 1*inch, 1*inch, 1*inch])
    style_kehadiran = TableStyle([
                        ('BACKGROUND', (0, 0), (2, 0), colors.HexColor('#0070c0')),
                        ('BACKGROUND', (3, 0), (-1, 0), colors.HexColor('#f4b184')),
                        ('TEXTCOLOR', (0, 0), (2, 0), colors.HexColor('#FFFFFF')),
                        ('TEXTCOLOR', (3, 0), (-1, 0), colors.HexColor('#000000')),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTRE'),
                        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ('BACKGROUND', (0, 1), (2, -1), colors.HexColor('#ddebf7')),
                        ('BACKGROUND', (3, 1), (-1, -1), colors.HexColor('#fff2cc')),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black),
                        ('FONTSIZE', (0, 0), (-1, -1), 12),
                        ])
    table_kehadiran.setStyle(style_kehadiran)
    # ==========================end Kehadiran
    

    
    # ==========================Cuti
    data_formatted_cuti = []
    for i,row in enumerate(data_cuti):
        if i == 0 or i == 1:
            data_formatted_cuti.append([cell.replace(' ','\n') for cell in row])
        else:
            data_formatted_cuti.append([cell for cell in row])
    table_cuti = Table(data_formatted_cuti, colWidths=[3.0*inch, 1.5*inch, 1.5*inch, 1*inch, 1*inch, 1.2*inch, 1*inch, 1*inch, 1*inch])
    style_cuti = TableStyle([
                        ('BACKGROUND', (0, 0), (2, 2), colors.HexColor('#0070c0')),
                        ('BACKGROUND', (3, 0), (-1, 2), colors.HexColor('#f4b184')),
                        ('TEXTCOLOR', (0, 0), (2, 2), colors.HexColor('#FFFFFF')),
                        ('TEXTCOLOR', (3, 0), (-1, 2), colors.HexColor('#000000')),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTRE'),
                        ('ALIGN', (0, 3), (0, -1), 'LEFT'),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ('BACKGROUND', (0, 3), (2, -1), colors.HexColor('#ddebf7')),
                        ('BACKGROUND', (3, 3), (-1, -1), colors.HexColor('#fff2cc')),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black),
                        ('FONTSIZE', (0, 0), (-1, -1), 12),
                        ('SPAN',(0,0),(0,1)),
                        ('SPAN',(1,0),(1,1)),
                        ('SPAN',(2,0),(2,1)),
                        ('SPAN',(3,0),(3,1)),
                        ('SPAN',(4,0),(4,1)),
                        ('SPAN',(5,0),(6,0)),
                        ('SPAN',(7,0),(7,1)),
                        ('SPAN',(8,0),(8,1)),
                        ])
    table_cuti.setStyle(style_cuti)
    # ==========================end Cuti
    
    year_calendar = generate_year_calendar(year)
    list_absensi = []
    span_absensi_month = []
    span_absensi_week = []
    list_a = formating_data_absen(data_kehadiran, att)
        

    for count in range(0,6):
        list_month = []
        list_week = []
        list_day = []
        left_formats = ['NAMA\nKARYAWAN', 'DIVISI', 'JABATAN']
        for left_format in left_formats:
            list_month.append(left_format)
            list_week.append(left_format)
            list_day.append(left_format)
            
        row_count = 3
        count = count*2
        
        temp_month = []
        temp_week = []
        
        for month in range(0+count,2+count):
            month_name = calendar.month_name[month+1]
            month_1strow = row_count
            
            for week in year_calendar[month]:
                week_1strow = row_count

                for i,day in enumerate(week):
                    list_month.append(month_name)
                    list_week.append(f'WEEK {get_week_number(year, month+1, week[0])}')
                    if(day >= 0):
                        list_day.append(change_sign(day))
                    else:
                        list_day.append(change_sign(day))
                    row_count += 1
                
                week_2ndrow = row_count
                temp_week.append([week_1strow,week_2ndrow-1])
            
            month_2ndrow = row_count
            temp_month.append([month_1strow,month_2ndrow-1])
            
        span_absensi_month.append(temp_month)
        span_absensi_week.append(temp_week)
        
        d_first, d_last = get_first_and_last_day(year, count+1)
        i_first = date_to_index(d_first)
        i_last = date_to_index(d_last)
        finish_data = [list_month,list_week, list_day]
        for a in list_a:
            filtered_data = a[0:3] + a[i_first+3 : i_last+4]
            finish_data.append(filtered_data)
        list_absensi.append(finish_data)
    
    # ==========================keterlambatan
    data_formatted_keterlambatan = keterlambatan_formater(list_a, generate_weeks(year))
    colwidth = [1.4*inch,0.6*inch,0.65*inch] + [0.22*inch for i in range(len(data_formatted_keterlambatan[0])-3)]
    table_keterlambatan = Table(data_formatted_keterlambatan, colWidths=colwidth)
    style_keterlambatan = TableStyle([
                        ('BACKGROUND', (0, 0), (2, 1), colors.HexColor('#0070c0')),
                        ('BACKGROUND', (3, 0), (-1, 1), colors.HexColor('#f4b184')),
                        ('TEXTCOLOR', (0, 0), (2, 1), colors.HexColor('#FFFFFF')),
                        ('TEXTCOLOR', (3, 0), (-1, 1), colors.HexColor('#000000')),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTRE'),
                        ('ALIGN', (0, 2), (0, -1), 'LEFT'),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ('BACKGROUND', (0, 2), (2, -1), colors.HexColor('#ddebf7')),
                        # ('BACKGROUND', (3, 2), (-1, -1), colors.HexColor('#fff2cc')),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black),
                        ('FONTSIZE', (0, 0), (-1, -1), 8),
                        ('SPAN',(3,0),(-1,0)),
                        ('SPAN',(0,0),(0,1)),
                        ('SPAN',(1,0),(1,1)),
                        ('SPAN',(2,0),(2,1)),
                        ])
    
    for row, values, in enumerate(data_formatted_keterlambatan[2:]):
        for column, value in enumerate(values[3:]):
            if value >= 5:
                style_keterlambatan.add('BACKGROUND', (column+3, row+2), (column+3, row+2), colors.HexColor('#E93324'))
            elif value == 4:
                style_keterlambatan.add('BACKGROUND', (column+3, row+2), (column+3, row+2), colors.HexColor('#F5C343'))
            elif value == 3:
                style_keterlambatan.add('BACKGROUND', (column+3, row+2), (column+3, row+2), colors.HexColor('#FFFF54'))
            elif value == 2:
                style_keterlambatan.add('BACKGROUND', (column+3, row+2), (column+3, row+2), colors.HexColor('#FBE6A3'))
            elif value == 1:
                style_keterlambatan.add('BACKGROUND', (column+3, row+2), (column+3, row+2), colors.HexColor('#B2CF93'))
            elif value == 0:
                style_keterlambatan.add('BACKGROUND', (column+3, row+2), (column+3, row+2), colors.HexColor('#5B823F'))
            else:
                style_keterlambatan.add('BACKGROUND', (column+3, row+2), (column+3, row+2), colors.HexColor('#d2222d'))
                
                
    table_keterlambatan.setStyle(style_keterlambatan)
    # ==========================end keterlambatan
    
    content = [
        titleKehadiran,
        table_kehadiran,
        Spacer(1, 1*inch),
        titleKeterlambatan,
        table_keterlambatan,
        Spacer(1, 1*inch),
        titleCuti, 
        table_cuti,
        Spacer(1, 0.1*inch),
        time_text,
        PageBreak(),
        ]
    
    for a in range(0,6):
        table_absen = table_absensi_formating(list_absensi[a], span_absensi_month[a], span_absensi_week[a])
        content.append(Spacer(1, 0.5*inch))
        content.append(table_absen)
        if a % 2 != 0:  # Check if 'a' is even
            content.append(Spacer(1, 0.25*inch))
            content.append(time_text)
            content.append(PageBreak())

    doc.build(content)

def keterlambatan_formater(data, calendar):
    main_format = []
    temp_format = []
    temp_header = []
    current_datetime = datetime.now()
    formatted_datetime = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
    
    temp_format.append(f'NAMA KARYAWAN')
    temp_format.append(f'DIVISI')
    temp_format.append(f'JABATAN')
    
    temp_header.append(f'NAMA KARYAWAN')
    temp_header.append(f'DIVISI')
    temp_header.append(f'JABATAN')
    
    
    for i in range(len(calendar)):
        temp_format.append(i+1)
        temp_header.append('Week')
    
    main_format.append(temp_header)
    main_format.append(temp_format)
        
    for d in data:
        temp_format = d[0:3]
        data_tanggal = d[3:-1]
        
        for c in calendar:
            temp_data = data_tanggal[c[0]-1:c[-1]-2]
            temp_format.append(temp_data.count('T'))
        
        main_format.append(temp_format)
        
    return(main_format)


def count_2d_array(arr):
    count = 0
    for row in arr:
        for element in row:
            count += 1

    return count

def generate_weeks(year):
    weeks = []
    current_date = date(year, 1, 1)
    week_days = []
    day_of_year = 1
    while current_date.year == year:
        week_days.append(day_of_year)
        if current_date.weekday() == 6:
            weeks.append(week_days)
            week_days = []
        current_date += timedelta(days=1)
        day_of_year += 1
    return weeks


def generate_year_calendar(year):
    year_calendar = []
    for month in range(1, 13):
        month_calendar = []
        for week in calendar.monthcalendar(year, month):
            week_data = []
            for day in week:
                if day != 0:
                    if calendar.weekday(year, month, day) < 5:
                        week_data.append(day)
                    else:
                        week_data.append(-day)

            month_calendar.append(week_data)
        year_calendar.append(month_calendar)
    return year_calendar

def get_week_number(year, month, day):
    day = change_sign(day)
    input_date = datetime(year, month, day)
    output = input_date.isocalendar()[1]
    return str(output)

def change_sign(number):
    result = -number if number < 0 else number
    return result


def date_to_index(date_or_string):
    if isinstance(date_or_string, str):
        date_or_string = datetime.strptime(date_or_string, "%Y-%m-%d")
    start_of_year = datetime(date_or_string.year, 1, 1)
    delta = date_or_string - start_of_year
    return delta.days


def get_first_and_last_day(year, month):
    first_day = datetime(year, month, 1)
    if month == 12:
        next_month = datetime(year + 1, 2, 1)
    elif month == 11:
        next_month = datetime(year + 1, 1, 1)
    else:
        next_month = datetime(year, month + 2, 1)
    last_day = next_month - timedelta(days=1)
    
    return first_day, last_day

def formating_data_absen(data_kehadiran, att):
    list_a = []
    list_temp = [''] * 366
    for i,a in enumerate(data_kehadiran):
        
        nama = a[0]
        nama = nama.split(' ')
        if len(nama) > 3:
            nama.pop()
            nama = ' '.join(nama)
        else:
            nama = ' '.join(nama)
            
        if len(nama) > 20:
            nama = nama.split(' ')
            nama[-1] = nama[-1][0] + '.'
            nama = ' '.join(nama)
            
        if a[2] == 'Assistant Manager':
            a[2] = 'AstManager'
        elif a[2] == 'JuniorSpv':
            a[2] = 'SJ'
        
        if a[1] == 'MANAGEMENT':
            a[1] = 'MGMT'
        
        if i == 0:
            continue
        temp_data = att[a[0]]
        for aa in temp_data.items():
            index = date_to_index(aa[0])
            if isinstance(aa[1], dict):
                list_temp[index] = aa[1]['type']
            else:
                list_temp[index] = aa[1]
        
        list_a.append([nama,a[1],a[2]] + list_temp) 
        list_temp = [''] * 366
        
    return list_a

def table_absensi_formating(data_list_absen, span_absensi_month, span_absensi_week):
    lebar_data = len(data_list_absen[0])
    # panjang_data = len(data_list_absen)
    colwidth = [1.4*inch,0.6*inch,0.65*inch] + [0.22*inch for i in range(lebar_data-3)]
    # colwidth = [1.4*inch if i == 0 else 0.6*inch if i == 1 else 0.65*inch if i == 2 else 0.22*inch for i in range(lebar_data)]
    table_absen = Table(data_list_absen, colWidths=colwidth)
    temp_stype_absen = [
                        ('ALIGN', (0, 0), (-1, -1), 'CENTRE'),
                        ('ALIGN', (0, 3), (0, -1), 'LEFT'),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black),
                        ('FONTSIZE', (0, 0), (-1, -1), 8),
                        ('SPAN',(0,0),(0,2)),
                        ('SPAN',(1,0),(1,2)),
                        ('SPAN',(2,0),(2,2)),
                        ('BACKGROUND', (0, 0), (-1, 2), colors.HexColor('#0070c0')),
                        ('BACKGROUND', (0, 3), (-1, -1), colors.HexColor('#ddebf7')),
                        ('BACKGROUND', (3, 0), (-1, 0), colors.HexColor('#ddebf7')),
                        ('BACKGROUND', (3, 1), (-1, 1), colors.HexColor('#5b9ad5')),
                        
                        ('TEXTCOLOR', (0, 0), (-1, 2), colors.HexColor('#FFFFFF')),
                        ('TEXTCOLOR', (3, 0), (-1, 1), colors.HexColor('#000000')),
                        ]
    for zz in span_absensi_month:
        temp_stype_absen.append(('SPAN',(zz[0],0),(zz[1],0)))
    for cc in span_absensi_week:
        temp_stype_absen.append(('SPAN',(cc[0],1),(cc[1],1)))
            
    TT = find_elements_2d(data_list_absen, 'T')
    if TT is not None:
        for T in TT:
            temp_stype_absen.append(('BACKGROUND',T,T,colors.HexColor('#ffff00')))
            temp_stype_absen.append(('TEXTCOLOR',T,T,colors.HexColor('#FF0000')))
    
    reds = find_elements_2d(data_list_absen, '')
    if reds is not None:
        for red in reds:
            temp_stype_absen.append(('BACKGROUND',red,red,colors.HexColor('#ff0000')))
            
    CC = find_elements_2d(data_list_absen, 'C')
    if CC is not None:
        for C in CC:
            temp_stype_absen.append(('BACKGROUND',C,C,colors.HexColor('#92d050')))
    
    SS = find_elements_2d(data_list_absen, 'S')
    if SS is not None:
        for S in SS:
            temp_stype_absen.append(('BACKGROUND',S,S,colors.HexColor('#cc66ff')))
    
    HDS = find_elements_2d(data_list_absen, 'HD')
    if HDS is not None:
        for HD in HDS:
            temp_stype_absen.append(('BACKGROUND',HD,HD,colors.HexColor('#ffc000')))
            
    DNS = find_elements_2d(data_list_absen, 'DN')
    if DNS is not None:
        for DN in DNS:
            temp_stype_absen.append(('BACKGROUND',DN,DN,colors.HexColor('#bdd7ee')))
            temp_stype_absen.append(('TEXTCOLOR',DN,DN,colors.HexColor('#FF0000')))
            
    KK = find_elements_2d(data_list_absen, 'K')
    if KK is not None:
        for K in KK:
            temp_stype_absen.append(('BACKGROUND',K,K,colors.HexColor('#ff9999')))
    
    style_absen = TableStyle(temp_stype_absen)
    table_absen.setStyle(style_absen)
    return table_absen

def find_elements_2d(array, element):
    positions = []
    for i in range(len(array)):
        for j in range(len(array[i])):
            if array[i][j] == element:
                positions.append((j, i))
    return positions if positions else None
