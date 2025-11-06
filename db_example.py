import mysql.connector
from mysql.connector import Error
from collections import OrderedDict
from collections import defaultdict
from datetime import datetime, timedelta

jam_masuk_normal = '08:46:00'
jam_masuk_rahmadan = '08:01:00'
tgl_awal_rahmadan = '2025-03-2'
tgl_ahkir_rahmadan = '2025-03-28'

def connect_to_database_absensi():
    try:
        connection = mysql.connector.connect(
            host="",
            user="telegram",
            password="",
            database="absensi"
        )
        return connection
    except Error as err:
        print(f"Error: {err}")
        return None
     
def connect_to_database_telebot():
    try:
        connection = mysql.connector.connect(
            host="",
            user="telegram",
            password="",
            database="telebot"
        )
        return connection
    except Error as err:
        print(f"Error: {err}")
        return None

def connect_to_database_windows():
    try:
        connection = mysql.connector.connect(
            host="",
            user="telegram",
            password="",
            database="absensi"
        )
        return connection
    except Error as err:
        print(f"Error: {err}")
        return None
    
def Get_User_Pin_by_name(name):
    try:
        connection = connect_to_database_absensi()
        if connection is not None:
            cursor = connection.cursor()
            insert_query = f"SELECT * FROM `pegawai` where `pegawai_nama` = '{name}'"
            cursor.execute(insert_query)
            records = cursor.fetchall()
            return records
        else:
            print('Failed to connect')
            return False
    except Error as err:
        print(f"Error: {err}")
        return False
    finally:
        if connection is not None:
            connection.close()
    
#Displays all employees by division and job title
def input_absensi_to_windows(pin,date,hour,min,executor):
    query = f"""
    INSERT INTO `att_log` 
    (`sn`, `scan_date`, `pin`, `verifymode`, `inoutmode`, `reserved`, `work_code`, `att_id`) VALUES 
    ('999', '{date} {hour}:{min}:00.000000', '{pin}', '100', '10', '0', '0', 'input manual by {executor}')"""
    
    try:
        connection = connect_to_database_windows()
        if connection:
            cursor = connection.cursor()
            cursor.execute(query)
            connection.commit()
            return True

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return str(err) 

    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()
            
def insert_message_history_to_windows(tele_id, tele_name, tele_message):
    query = f"""
    INSERT INTO `message_history` 
    (`tele_id`, `tele_name`, `tele_message`) VALUES 
    ('{tele_id}', '{tele_name}', '{tele_message}')
    """

    try:
        connection = connect_to_database_telebot()
        if connection:
            cursor = connection.cursor()
            cursor.execute(query)
            connection.commit()
            return True

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return str(err)

    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()


def delete_absensi_from_windows(pin, scan_date):
    query = f"""
    DELETE FROM `att_log`
    WHERE `pin` = '{pin}' AND `scan_date` = '{scan_date}'"""
    print(query)
    try:
        connection = connect_to_database_windows()
        if connection:
            cursor = connection.cursor()
            cursor.execute(query)
            connection.commit()
            return True

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return str(err) 

    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

    
def getAttendance_and_non_attendance(user_input_date):
    connection = connect_to_database_absensi()
    cursor = connection.cursor()

    attendance_results = getAttendance(user_input_date, cursor)
    non_attendance_results = get_non_attendance(user_input_date, cursor)

    cursor.close()
    connection.close()

    return attendance_results, non_attendance_results


#Get on-time employee attendance
def getAttendance(user_input_date, cursor):
    # Function to get attendance records for a specific date
    query = f"""SELECT pegawai.pegawai_nama, MIN(DATE_FORMAT(att_log.scan_date, '%H:%i:%s')) AS formatted_date, 
                GROUP_CONCAT(DATE_FORMAT(att_log.scan_Date, '%H:%i:%s') 
                ORDER BY att_log.scan_date) AS all_formatted_dates 
                FROM pegawai LEFT JOIN att_log ON att_log.pin = pegawai.pegawai_pin 
                WHERE att_log.scan_date IS NULL OR DATE(att_log.scan_date) = '{user_input_date}' 
                GROUP BY pegawai.pegawai_nama"""

    cursor.execute(query)
    records = cursor.fetchall()

    # Create a list to store the results
    attendance_results = []

    # Process and append records to the list
    for record in records:
        pegawai_nama, first_formatted_date, all_formatted_dates = record
        attendance_results.append({
            'name': pegawai_nama,
            'first_time_attendance': first_formatted_date,
            'all_scan_time_attendance': all_formatted_dates
        })

    return attendance_results

#Get the attendance of employees who have not been absent
def get_non_attendance(user_input_date, cursor):
    # Function to get employees with no attendance for a specific date
    exclude_names = ["rahadi", "yustinus", "WANTI", "galvin", "edward"]
    exclude_condition = " OR ".join(f"pegawai.pegawai_nama = '{name}'" for name in exclude_names)

    query = f"""SELECT pegawai.pegawai_nama 
                FROM pegawai
                WHERE pegawai.pegawai_pin 
                NOT IN (SELECT att_log.pin FROM att_log WHERE DATE(att_log.scan_date) = '{user_input_date}') 
                AND pegawai.pegawai_nip IS NOT NULL
                AND NOT ({exclude_condition})"""

    cursor.execute(query)
    non_attendance_records = cursor.fetchall()

    # Create a list to store the results
    non_attendance_results = []

    # Process and append records to the list
    for record in non_attendance_records:
        employee_name = record[0]
        non_attendance_results.append({
            'name': employee_name
        })

    return non_attendance_results

# <!===================================================NEW FUNCTION FROM MES DBASE====================================================!>#


#Displays all employees by division and job title
def GetAllEmployee(orderby="code_dep"):
    query = f"""SELECT  user.id, name, code_dep, role FROM user INNER JOIN user_role ON user.role_id = user_role.id 
               WHERE is_active = 1 AND role != "Directors" 
               ORDER BY {orderby}""" #Get Sisa Cuti, 
    
    try:
        connection = connect_to_database_telebot()
        if connection:
            cursor = connection.cursor()
            cursor.execute(query)
            records = cursor.fetchall()
            
            employee_list = []
            for record in records:
                id, name, divisi, role = record[0], record[1], record[2], record[3]
                employee_list.append({
                    'id' : id,
                    'name': name,
                    'divisi': divisi,
                    'role': role
                })
                
            if not employee_list:
                print("No records found")
                
            return employee_list

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return str(err) 

    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()
    
def GetAllEmployeeForRekap(condition=None, year = datetime.now().year-1):
    print(year)
    query = f"""SELECT  user.id, name, code_dep, role , user_cuti.sisa_cuti FROM user INNER JOIN user_role ON user.role_id = user_role.id left join user_cuti
               on user_cuti.id_user = user.id
               WHERE is_active = 1 AND role != "Directors" AND user_cuti.tahun = '{year}'
               """ #Get Sisa Cuti, 
    if condition is not None:
        query += f" AND {condition}"

    query += f" ORDER BY code_dep"
    print(query)
    try:
        connection = connect_to_database_telebot()
        if connection:
            cursor = connection.cursor()
            cursor.execute(query)
            records = cursor.fetchall()
            
            employee_list = []
            for record in records:
                id, name, divisi, role, sisa_cuti = record[0], record[1], record[2], record[3], record[4]
                employee_list.append({
                    'id' : id,
                    'name': name,
                    'divisi': divisi,
                    'role': role,
                    'sisa_cuti' : sisa_cuti
                })
                
            if not employee_list:
                print("No records found")
                
            return employee_list

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return False

    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

# Insert data into a dbase table
# Parameters (Table, Columns, Values)
# Example:
    #Input_Data_Into_Table("YOUR_TABLE", ['Column1', 'Column2], ['value1', 'value2'])
def Input_Data_Into_Table(table, columns, values):
    try:
        connection = connect_to_database_telebot()
        if connection is not None:
            cursor = connection.cursor()

            insert_query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(['%s']*len(values))})"
            data = tuple(values)
            print(insert_query, data)
            cursor.execute(insert_query, data)

            connection.commit()
            print("Insert Success!")
            return True
        else:
            print('Failed to connect')
            return False
    except Error as err:
        print(f"Error: {err}")
        return False
    finally:
        if connection is not None:
            connection.close()

# select into db
#(string, string, string, string)
            # Get_Data_from_tabel(nama table, order_by='date', join='user_id where table.id = user_id.id', join_type='left')
def Get_Data_from_Table(table, select="*", condition=None, order_by=None, join=None, limit=None):
    query = f"SELECT {select} FROM {table}"

    if join is not None:
        query += f" {join}"

    if condition is not None:
        query += f" WHERE {condition}"

    if order_by is not None:
        query += f" ORDER BY {order_by}"
    
    if limit is not None:
        query += f" limit {limit}"


    try:
        connection = connect_to_database_telebot()
        if connection:
            cursor = connection.cursor()
            cursor.execute(query)
            records = cursor.fetchall()
                
            return records

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return str(err) 

    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

def Update_Data_from_Table(table, set, where):
    query = f"UPDATE {table} SET {set} WHERE {where}"
    print(query)
    try:
        connection = connect_to_database_telebot()
        if connection:
            cursor = connection.cursor()

            cursor.execute(query)
            connection.commit()
            print(f"Update Berhasil")
            return True

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return False 

    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()
            

#Get Attendance By Range
#Add this to your main.py
#StartDate = "2024-01-01"
#EndDate = "2024-01-31"

def delete_data_from_table(table, condition):
    query = f"DELETE FROM {table} WHERE {condition}"
    print(query)
    try:
        connection = connect_to_database_telebot()
        if connection:
            cursor = connection.cursor()
            cursor.execute(query)
            connection.commit()
            return True

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return False 

    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()


####NEW FUNCTION###




def ShowingIzin(StartDate, EndDate, single_day=False):
    try:
        connection = connect_to_database_telebot()
        if connection is not None:
            cursor = connection.cursor()

            Exception_names = ["Pak Rahadi", "Pak Yustinus", "Ibu Wanti", "Galvin Christopher", "Pak Edward"]
            Exception_condition = f"AND name NOT IN {tuple(Exception_names)}"
            if single_day == True:
                query_cuti = f"""SELECT user.name, user_izin.tgl_awal, user_izin.tgl_akhir, jenis_izin, note AS Keterangan
                                FROM user 
                                LEFT JOIN user_izin ON user.id = user_izin.id_user WHERE is_active = 1 {Exception_condition}
                                AND '{StartDate}' BETWEEN user_izin.tgl_awal AND user_izin.tgl_akhir
                                """
                cursor.execute(query_cuti)
            else:
                query_cuti = f"""SELECT user.name, user_izin.tgl_awal, user_izin.tgl_akhir, jenis_izin, note AS Keterangan
                                FROM user 
                                LEFT JOIN user_izin ON user.id = user_izin.id_user WHERE is_active = 1 {Exception_condition}
                                AND user_izin.tgl_awal BETWEEN %s and %s
                                AND user_izin.tgl_akhir BETWEEN %s and %s
                                """
        
                cursor.execute(query_cuti, (StartDate, EndDate, StartDate, EndDate))
            records = cursor.fetchall()

            for record in records:
                name = record[0],
                tgl_awal = record[1].strftime('%Y-%m-%d') if record[1] is not None else "N/A"
                tgl_akhir = record[2].strftime('%Y-%m-%d') if record[2] is not None else "N/A"
                jenis_izin = record[3] if record[3] is not None else ""
                note = record[4] if record[4] is not None else ""


            return records

    except Error as err:
        print(f"Error: {err}")
        return False
    finally:
        if connection is not None:
            connection.close()


def GetAttendanceByRange(StartDate, EndDate): 
    try:
        connection = connect_to_database_absensi()

        if connection is not None:
            Exception_names = ["rahadi", "yustinus", "WANTI", "galvin", "edward"]
            Exception_condition = f"AND pegawai_nama NOT IN {tuple(Exception_names)}"
            query_ReportAttendance = f"""SELECT pegawai_nama, scan_date, scan_time,
                                CASE
                                    WHEN (DATE(scan_date) BETWEEN '{tgl_awal_rahmadan}' AND '{tgl_ahkir_rahmadan}') AND scan_time >= '{jam_masuk_rahmadan}' THEN 'T'
                                    WHEN scan_time < '{jam_masuk_normal}' THEN 'A'
                                    WHEN scan_time >= '{jam_masuk_normal}' AND scan_time <= '13:30:00' THEN 'T'
                                    WHEN scan_time IS NULL OR scan_time = '' THEN 'TK'
                                END AS Keterangan
                                FROM (
                                    SELECT pegawai_nama, DATE(scan_date) AS scan_date,
                                        MIN(TIME(scan_date)) AS scan_time
                                    FROM pegawai 
                                    LEFT JOIN att_log ON pegawai.pegawai_pin = att_log.pin 
                                    WHERE DATE(scan_date) BETWEEN %s AND %s
                                    {Exception_condition} 
                                    GROUP BY pegawai_nama, pegawai_pin, DATE(scan_date)
                                ) AS subquery
                                ORDER BY scan_date ASC"""

            cursor = connection.cursor()
            cursor.execute(query_ReportAttendance, (StartDate, EndDate))
            records_report = cursor.fetchall()

            Employee_kehadiran = defaultdict(dict)
            
            for record in records_report:
                pegawai_nama, scan_date, scan_time, keterangan = record
                format_date = scan_date.strftime('%Y-%m-%d')

                # Initialize the date key if not present
                if format_date not in Employee_kehadiran[pegawai_nama]:
                    Employee_kehadiran[pegawai_nama][format_date] = ""

                if keterangan == 'T':
                    Employee_kehadiran[pegawai_nama][format_date] = {'type' : keterangan, 'note': scan_time}
                else:
                    Employee_kehadiran[pegawai_nama][format_date] = keterangan

            cursor.close()
            connection.close()

            return dict(Employee_kehadiran)

        else:
            print("Error: Unable to connect to the database")

    except Error as e:
        print("Error executing query:", e)
        


def GetAttendanceByRangeSingleEmployee(StartDate, EndDate, employee): 
    try:
        connection = connect_to_database_absensi()

        if connection is not None:
            Exception_condition = f"AND pegawai_nama = '{employee}'"
            query_ReportAttendance = f"""SELECT pegawai_nama, scan_date, scan_time,
                                CASE
                                    WHEN (DATE(scan_date) BETWEEN '{tgl_awal_rahmadan}' AND '{tgl_ahkir_rahmadan}') AND scan_time >= '{jam_masuk_rahmadan}' THEN 'T'
                                    WHEN scan_time < '{jam_masuk_normal}' THEN 'A'
                                    WHEN scan_time >= '{jam_masuk_normal}' AND scan_time <= '13:30:00' THEN 'T'
                                    WHEN scan_time IS NULL OR scan_time = '' THEN 'TK'
                                END AS Keterangan
                                FROM (
                                    SELECT pegawai_nama, DATE(scan_date) AS scan_date,
                                        MIN(TIME(scan_date)) AS scan_time
                                    FROM pegawai 
                                    LEFT JOIN att_log ON pegawai.pegawai_pin = att_log.pin 
                                    WHERE DATE(scan_date) BETWEEN %s AND %s
                                    {Exception_condition} 
                                    GROUP BY pegawai_nama, pegawai_pin, DATE(scan_date)
                                ) AS subquery
                                ORDER BY scan_date ASC"""

            cursor = connection.cursor()
            cursor.execute(query_ReportAttendance, (StartDate, EndDate))
            records_report = cursor.fetchall()

            Employee_kehadiran = defaultdict(dict)
            
            for record in records_report:
                pegawai_nama, scan_date, scan_time, keterangan = record
                format_date = scan_date.strftime('%Y-%m-%d')

                # Initialize the date key if not present
                if format_date not in Employee_kehadiran[pegawai_nama]:
                    Employee_kehadiran[pegawai_nama][format_date] = ""

                if keterangan == 'T':
                    Employee_kehadiran[pegawai_nama][format_date] = {'type' : keterangan, 'note': None, 'scan_time': scan_time}
                else:
                    Employee_kehadiran[pegawai_nama][format_date] = {'type' : keterangan, 'note': None, 'scan_time': scan_time}

            cursor.close()
            connection.close()

            return dict(Employee_kehadiran)

        else:
            print("Error: Unable to connect to the database")

    except Error as e:
        print("Error executing query:", e)



def MergeAttendanceAndLeaveInfo(StartDate, EndDate, single_day=False):
    leave_info = ShowingIzin(StartDate, EndDate, single_day)
    attendance_info = GetAttendanceByRange(StartDate, EndDate)
    

    for leave_record in leave_info:
        name, leave_start_date, leave_end_date, leave_type, note = leave_record

        leave_dates = set()
        current_date = leave_start_date
        while current_date <= leave_end_date:
            leave_dates.add(current_date.strftime('%Y-%m-%d'))
            current_date += timedelta(days=1)

        if name not in attendance_info:
            attendance_info[name] = {} 
        # if name in attendance_info:
        for date in leave_dates:
            # if date in attendance_info[name]:
            attendance_info[name][date] = {'type' : leave_type, 'note': note}
                # else:
                    # attendance_info[name][date] = {'type' : leave_type, 'note': note}


    return attendance_info

def MergeAttendanceAndLeaveInfoKhususSumarry(StartDate, EndDate, emp, single_day=False):
    leave_info = ShowingIzin(StartDate, EndDate, single_day)
    attendance_info = GetAttendanceByRangeSingleEmployee(StartDate, EndDate, emp)

    for leave_record in leave_info:
        name, leave_start_date, leave_end_date, leave_type, note = leave_record

        leave_dates = set()
        current_date = leave_start_date
        while current_date <= leave_end_date:
            leave_dates.add(current_date.strftime('%Y-%m-%d'))
            current_date += timedelta(days=1)

        if name in attendance_info:
            for date in leave_dates:
                if leave_type == 'T':                    
                    attendance_info[name][date]['note'] = note
                else:
                    attendance_info[name][date] = {'type' : leave_type, 'note': note, 'scan_time': None}


    return attendance_info
