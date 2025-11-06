# import sys
# sys.path.append('../')

import textwrap
from reportlab.lib import colors
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.lineplots import LinePlot
from reportlab.graphics.widgets.markers import makeMarker
from db import *
from ModulSummary.helper import * 
from reportlab.graphics import shapes
from reportlab.graphics.charts.textlabels import Label
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.pagesizes import A3, landscape
from reportlab.lib.units import inch
from reportlab.graphics.shapes import Drawing, String
from reportlab.graphics.charts.legends import Legend
import calendar
from reportlab.graphics.charts.barcharts import VerticalBarChart

months = ['','Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

def linechart(data):
    drawing = Drawing(600, 220)
    
    lab = Label()
    lab.setOrigin(300,200)
    lab.textAnchor = 'middle'
    lab.dx = 0
    lab.dy = 0
    lab.setText('Keterlambatan (T)')
    drawing.add(lab)
    
    lp = LinePlot()
    lp.x = 50
    lp.y = 50
    lp.width = 500
    lp.height = 125
    lp.data = [data]
    lp.lines[0].strokeColor = colors.red  # Line color
    lp.lines[0].strokeWidth = 2  # Line width
    lp.xValueAxis.valueMin = 0
    lp.xValueAxis.valueMax = 12
    lp.yValueAxis.valueMin = 0
    lp.yValueAxis.valueMax = 20
    lp.xValueAxis.valueSteps = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    
    lp.xValueAxis.labelTextFormat = lambda x: months[int(x)]
    lp.yValueAxis.labelTextFormat = lambda y: str(int(y))
    lp.xValueAxis.visibleGrid = 1
    lp.yValueAxis.visibleGrid = 1
    lp.lines[0].symbol = makeMarker('Circle')
    drawing.add(lp)
    # drawing.save(formats=['pdf'], outDir='.', fnRoot='line_chart')
    # renderPM.drawToFile(drawing, 'line_chart.png', 'PNG')
    return drawing
    
    
def generate_bar_chart(data1, data2, labels):
    drawing = Drawing(600, 220)
    
    lab = Label()
    lab.setOrigin(300,220)
    lab.textAnchor = 'middle'
    lab.dx = 0
    lab.dy = 0
    lab.setText('Hari Kerja / Kehadiran (A)')
    drawing.add(lab)
    
    legend_x = 200
    
    kehadiran = Legend()
    kehadiran.x = legend_x
    kehadiran.y = 200
    kehadiran.alignment = 'right'
    kehadiran.colorNamePairs = [(colors.crimson, 'Kehadiran')]
    kehadiran.fontName = 'Helvetica'
    drawing.add(kehadiran)
    
    harikerja = Legend()
    harikerja.x = legend_x + 100
    harikerja.y = 200
    harikerja.alignment = 'right'
    harikerja.colorNamePairs = [(colors.darkseagreen, 'Hari Kerja')]
    harikerja.fontName = 'Helvetica'
    drawing.add(harikerja)
    
    bc = VerticalBarChart()
    bc.x = 50
    bc.y = 50
    bc.width = 500
    bc.height = 125
    bc.data = [data1, data2]  # Two sets of data
    bc.categoryAxis.categoryNames = labels
    bc.bars[0].fillColor = colors.crimson
    bc.bars[1].fillColor = colors.darkseagreen # Setting different color for the second set of data
    bc.barLabels.boxTarget='mid'
    bc.barLabels.fillColor        = colors.white
    bc.barLabels.fontSize         = 8
    bc.barLabels.fontName         = 'Helvetica'
    bc.barLabelFormat = '%s'
    bc.bars.strokeColor     = colors.white
    drawing.add(bc)
    
    return drawing


    
def process_template_summary(emp, filename, year):
    StartYear, EndYear = date_range(year)
    att = MergeAttendanceAndLeaveInfoKhususSumarry(StartYear, EndYear, emp)

    main_data = att[emp]
    data_by_month = defaultdict(dict)

    type_counts_by_month = defaultdict(lambda: defaultdict(int))

    for date_str, entry in main_data.items():
        date = datetime.strptime(date_str, '%Y-%m-%d')
        year_month = date.strftime('%Y-%m')
        data_by_month[year_month][date_str] = entry
        type_counts_by_month[date.month][entry['type']] += 1

    data_for_chart = []
    for month in range(1, 13):
        count = type_counts_by_month[month]['T']
        data_for_chart.append((month, count))
    
    line_chart = linechart(data_for_chart)

    # Print type counts for each month
    bulan = ['']
    HariKerja = ['HARI KERJA']
    kehadiran = ['KEHADIRAN']
    dinas = ['DINAS']
    keterlambatan = ['KETERLAMBATAN']
    sakit = ['SAKIT']
    cuti = ['CUTI']
    CutiKhusus = ['CUTI KHUSUS']
    SetengahHari = ['SETENGAH HARI']
    for month, type_counts in type_counts_by_month.items():
        bulan.append(calendar.month_name[month])
        
        A = type_counts['T']
        HD = 0
        S = 0
        C = 0
        K = 0

        if 'DN' in type_counts:
            dinas.append(type_counts['DN'])
            A += type_counts['DN']
        else:
            dinas.append(0)
            
        if 'S' in type_counts:
            sakit.append(type_counts['S'])
            S = type_counts['S']
        else:
            sakit.append(0)
            
        if 'C' in type_counts:
            cuti.append(type_counts['C'])
            C = type_counts['C']
        else:
            cuti.append(0)
            
        if 'K' in type_counts:
            CutiKhusus.append(type_counts['K'])
            K = type_counts['K']
        else:
            CutiKhusus.append(0)
        
        if 'HD' in type_counts:
            SetengahHari.append(type_counts['HD'])
            HD = type_counts['HD']
        else:
            SetengahHari.append(0)
            
        if 'A' in type_counts:
            A = type_counts['A'] + A + int((HD+1)/2)
            kehadiran.append(A)
        else:
            kehadiran.append(0)
        
        keterlambatan.append(type_counts['T'])
        HariKerja.append(A + S + C + K + int(HD/2))
        
    formated_data = [bulan, HariKerja, kehadiran, dinas, keterlambatan, sakit, cuti, CutiKhusus, SetengahHari]
    # print(formated_data)

    data_telat = {key: value for key, value in main_data.items() if value['type'] == 'T'}
    data_telat = dict(sorted(data_telat.items(), key=lambda x: datetime.strptime(x[0], '%Y-%m-%d'), reverse=True))
    count = 1
    formated_data_telat = [['NO','TANGGAL', 'JAM ABSEN', 'NOTE']]
    for time,data in data_telat.items():
        if data['note'] is not None:
            wrapped_text = textwrap.fill(data['note'], width=50)
        else:
            wrapped_text = 'Tidak ada Note'
        formated_data_telat.append([count, time, data['scan_time'], wrapped_text])
        count+= 1
    # print(formated_data_telat)

    margin_top = 0.1 * inch
    margin_bottom = 0.1 * inch
    margin_left = 0.1 * inch
    margin_right = 0.1 * inch

    doc = SimpleDocTemplate(f'/home/dev/new-bot/ModulSummary/{filename}', pagesize=landscape(A3), topMargin=margin_top, bottomMargin=margin_bottom, leftMargin=margin_left, rightMargin=margin_right)
    
    styles = getSampleStyleSheet()
    
    # Membuat judul di tengah dan besar
    Title = Paragraph(f"<para align='center'><b><font size='16'>ANNUAL SUMMARY - TAHUN {year}</font></b></para>", styles["Heading1"])
    Sub = Paragraph(f"<para align='center'><b><font size='16'>{emp}</font></b></para>", styles["Heading1"])

    Title.aligment = 1
    Sub.alignment = 1

    # Membuat waktu pembuatan PDF
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    time_text = Paragraph(f"<font size=8>Dibuat pada: {current_time}</font>", styles["Normal"])
    
    # ==========================Summary
    table_summary = Table(formated_data, colWidths=[2.0*inch, 1*inch, 1*inch, 1*inch, 1*inch, 1*inch, 1*inch, 1*inch, 1*inch, 1*inch, 1*inch])
    style_summary = TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f4b184')),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#000000')),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTRE'),
                        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#ddebf7')),
                        ('BACKGROUND', (1, 1), (-1, -1), colors.HexColor('#fff2cc')),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black),
                        ('FONTSIZE', (0, 0), (-1, -1), 12),
                        ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#ffffff')),
                        ('LINEABOVE', (0, 0), (0, 0), 0, colors.HexColor('#ffffff')),
                        ('LINEBEFORE', (0, 0), (0, 0), 0, colors.HexColor('#ffffff')),
                        
                        ])
    table_summary.setStyle(style_summary)
    # ==========================end Summary
    
    # ==========================Telat
    table_telat = Table(formated_data_telat, colWidths=[0.3*inch, 1*inch, 1*inch, 5*inch])
    style_telat = TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f4b184')),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#000000')),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTRE'),
                        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        # ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#ddebf7')),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#fff2cc')),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black),
                        ('FONTSIZE', (0, 0), (-1, -1), 12),
                        ])
    table_telat.setStyle(style_telat)
    # ==========================end Telat
    
    # Example data and labels
    data1 = kehadiran[1:]
    data2 = HariKerja[1:]
    labels = months[1:]

    # Generate the bar chart
    bar_chart = generate_bar_chart(data1, data2, labels)
        
    content = [
        Title,
        Sub,
        Spacer(1, 0.5*inch),
        table_summary,
        Spacer(1, 1*inch),
        Table([[Spacer(0.1*inch, 0), line_chart, bar_chart, Spacer(0.1*inch, 0)]]),
        Spacer(1, 1*inch),
        table_telat,
        Spacer(1, 0.1*inch),
        time_text,
        PageBreak(),
        ]
    
    doc.build(content)

# emp = 'Steven'
# year = 2024
# # emp = 'Destiawan Kris Wibowo'
# create_pdf(emp, 'test.pdf', year)