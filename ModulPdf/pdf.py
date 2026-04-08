from db import *
from ModulPdf.helper import *
from dotenv import load_dotenv
import os

# Load the .env file
load_dotenv()

# Get the names as a Python list (strip spaces just in case)
SPECIAL_NAMES = [n.strip() for n in os.getenv("SPECIAL_NAMES", "").split(",")]


def process_template_export(employee, year, pdf_filename, end_date=None):
    year = int(year)
    StartYear, EndYear = date_range(year)

    # for custom enddate - override if end_date is provided
    if end_date:
        EndYear = end_date

    att = MergeAttendanceAndLeaveInfo(StartYear, EndYear)

    for special_name in SPECIAL_NAMES:
        for date, value in att.get(special_name, {}).items():
            if isinstance(value, dict) and value.get('type') == 'T':
                if check_telat_khusus(value['note']):
                    value['type'] = 'A'


    create_pdf(employee, pdf_filename, year, att)
    return True
