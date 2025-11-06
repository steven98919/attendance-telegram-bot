from datetime import datetime

def date_range(year):
    first_day = datetime(year, 1, 1)
    last_day = datetime(year, 12, 31)
    formatted_start_day = first_day.strftime("%Y-%m-%d")
    formatted_end_day = last_day.strftime("%Y-%m-%d")

    return formatted_start_day, formatted_end_day