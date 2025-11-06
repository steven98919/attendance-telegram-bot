import calendar
import datetime
from datetime import datetime as dt
from db import *

def day_of_year(date):
    date = dt.strptime(date, "%Y-%m-%d")
    first_day = dt(date.year, 1, 1)
    delta = date - first_day
    day_number = delta.days + 1  
    return day_number

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

def count_2d_array(arr):
    count = 0
    for row in arr:
        for element in row:
            count += 1

    return count

def get_week_number(year, month, day):
    day = change_sign(day)
    input_date = datetime(year, month, day)
    output = input_date.isocalendar()[1]
    return str(output)

def change_sign(number):
    result = -number if number < 0 else number
    return result


def generate_formulas(row_number, index):
    def case1():
        return f'=E{row_number}+H{row_number}+I{row_number}+J{row_number}+int((K{row_number})/2)'

    def case2():
        return f'=COUNTIF(L{row_number}:XFD{row_number},"A")+F{row_number}+G{row_number}+int((K{row_number}+1)/2)'

    def case3():
        return f'=COUNTIF($L{row_number}:$XFD{row_number},"DN")'

    def case4():
        return f'=COUNTIF($L{row_number}:$XFD{row_number},"T")'

    def case5():
        return f'=COUNTIF(L{row_number}:XFD{row_number},"S")'

    def case6():
        return f'=COUNTIF(L{row_number}:XFD{row_number},"C")+COUNTIF(L{row_number}:XFD{row_number},"CB")'

    def case7():
        return f'=COUNTIF($L{row_number}:$XFD{row_number},"K")'

    def case8():
        return f'=COUNTIF($L{row_number}:$XFD{row_number},"HD")'

    def default():
        return "Invalid index"

    switch_dict = {
        0: case1,
        1: case2,
        2: case3,
        3: case4,
        4: case5,
        5: case6,
        6: case7,
        7: case8
    }

    return switch_dict.get(index, default)()

def generate_formulas_cuti(row_number, index, year=dt.now().year):
    def case1():
        return f'{year}'

    def case2():
        return f'12'

    def case3():
        data = Get_Data_from_Table('user_cuti_bersama', condition=f'tahun = {year}')
        if len(data) == 0 :
            return 0
        return f'{data[0][1]}'

    def case4():
        return f'=VLOOKUP(A{row_number},KEHADIRAN!$A$4:$I$100,9,FALSE)+INT(VLOOKUP(A{row_number},KEHADIRAN!$A$4:$K$100,11,FALSE)/2)'

    def case5():
        return f'=F{row_number}+G{row_number}'

    def case6():
        return f'=D{row_number}+E{row_number}-H{row_number}'

    def default():
        return "Invalid index"

    switch_dict = {
        3: case1,
        4: case2,
        5: case3,
        6: case4,
        7: case5,
        8: case6,
    }

    return switch_dict.get(index, default)()

def get_start_and_end_days(year):
    first_day = dt(year, 1, 1)
    last_day = dt(year, 12, 31)
    formatted_start_day = first_day.strftime("%Y-%m-%d")
    formatted_end_day = last_day.strftime("%Y-%m-%d")

    return [formatted_start_day, formatted_end_day]