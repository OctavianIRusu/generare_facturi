import calendar
import os
import sqlite3
from datetime import date
from pathlib import Path

import openpyxl
import pandas as pd
from dateutil.relativedelta import relativedelta
from openpyxl.chart import BarChart, Reference

# Set the root folder path and database path
MAIN_FOLDER_ROOT = Path(__file__).parent
DB_FILE = MAIN_FOLDER_ROOT / "bill_database.sqlite"

# Dictionary that maps Romanian counties to their corresponding abbreviations
ROMANIAN_COUNTIES_ABBR = {
    "Alba": "AB",
    "Arad": "AR",
    "Arges": "AG",
    "Bacau": "BC",
    "Bihor": "BH",
    "Bistrita-Nasaud": "BN",
    "Botosani": "BT",
    "Brasov": "BV",
    "Braila": "BR",
    "Buzau": "BZ",
    "Caras-Severin": "CS",
    "Calarasi": "CL",
    "Cluj": "CJ",
    "Constanta": "CT",
    "Covasna": "CV",
    "Dambovita": "DB",
    "Dolj": "DJ",
    "Galati": "GL",
    "Giurgiu": "GR",
    "Gorj": "GJ",
    "Harghita": "HR",
    "Hunedoara": "HD",
    "Ialomita": "IL",
    "Iasi": "IS",
    "Ilfov": "IF",
    "Maramures": "MM",
    "Mehedinti": "MH",
    "Mures": "MS",
    "Neamt": "NT",
    "Olt": "OT",
    "Prahova": "PH",
    "Satu Mare": "SM",
    "Salaj": "SJ",
    "Sibiu": "SB",
    "Suceava": "SV",
    "Teleorman": "TR",
    "Timis": "TM",
    "Tulcea": "TL",
    "Vaslui": "VS",
    "Valcea": "VL",
    "Vrancea": "VN"
}

# Dictionary that stores the price per unit for various charge categories
PRICE_PER_UNIT = {
    "energie_consumata": 1.40182,
    "acciza_necomerciala": 6.05,
    "certificate_verzi": 71.68059,
    "oug_27": 0.90812,
    "tva": 0.19
}

# Dictionary that stores information about the detailed consumption and price
CONSUMPTION_DETAILS = {
    "Produse si servicii": [
    "Energie consumata", 
    "Acciza necomerciala",               
    "Certificate verzi", 
    "OUG 27"],
    "Cantitate": [],
    "U.M.": ["kWh", "MWh", "MWh", "kWh"],
    "Pret unitar fara TVA": [],
    "Valoare fara TVA": [],
    "Valoare TVA (19%)": []
}

# connection = sqlite3.connect(DB_FILE)
# cursor = connection.cursor()

def open_database():
    connection = sqlite3.connect(DB_FILE)
    return connection
    
def perform_database_operation(connection):
    cursor = connection.cursor()
    return cursor

def close_database(connection):
    connection.close()

def authenticate(username, password, cursor):
    cursor.execute("""SELECT role FROM users 
        WHERE username = ? AND password = ?""", (username, password))
    result = cursor.fetchone()
    if result:
        role = result[0]
        if role == 'admin':
            return True, True
        else:
            return True, False
    return False, False

def view_users(cursor):
    cursor.execute('''
        SELECT * FROM users                   
    ''')
    rows = cursor.fetchall()
    for row in rows:
        print(row)

def add_new_user(connection, cursor):
    name = input("Introdu prenume si nume: ")
    street = input("Introdu adresa (strada, nr, bloc, apartament): ")
    zipcode = input("Introdu codul postal: ")
    city = input("Introdu localitatea: ")
    county = input("Introdu judetul: ")
    username = input("Introdu un nume de utilizator: ")
    password = input("Introdu o parola: ")
    role = input("Alege tip user (user/admin): ")
    
    cursor.execute('''INSERT INTO users (name, street, zipcode, city, 
        county, username, password, role)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
        (name, street, zipcode, city, county, username, password, role))
    connection.commit()
    print("-" * 60)
    print("Noul client a fost adaugat cu succes!")
    
def get_client_info(username, cursor):
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    if row:
        columns = [desc[0] for desc in cursor.description]
        user_dict = dict(zip(columns, row))
        return user_dict
    else:
        return None
    
def get_bill_info(username, bill_year, bill_month, cursor):
    cursor.execute("""SELECT * FROM bills 
                   WHERE username = ? AND bill_year = ? AND bill_month = ?""", 
        (username, bill_year, bill_month))
    row = cursor.fetchone()
    if row:
        columns = [desc[0] for desc in cursor.description]
        bill_info_dict = dict(zip(columns, row))
        return bill_info_dict
    else:
        return None

def create_consumption_table(username, bill_year, bill_month, cursor):
    cons_dict = get_bill_info(username, bill_year, bill_month, cursor)
    CONSUMPTION_DETAILS["Cantitate"] = [
        f"{cons_dict['energ_cons_cant']:.2f}",
        f"{cons_dict['acciza_cant']:.2f}",
        f"{cons_dict['certif_cant']:.2f}",
        f"{cons_dict['oug_cant']:.2f}",
    ]
    CONSUMPTION_DETAILS["Pret unitar fara TVA"] = [
        f"{PRICE_PER_UNIT['energie_consumata']:.2f}", 
        f"{PRICE_PER_UNIT['acciza_necomerciala']:.2f}",
        f"{PRICE_PER_UNIT['certificate_verzi']:.2f}", 
        f"{PRICE_PER_UNIT['oug_27']:.2f}"
    ]
    CONSUMPTION_DETAILS["Valoare fara TVA"] = [
        f"{cons_dict['energ_cons_val']:.2f}",
        f"{cons_dict['acciza_val']:.2f}",
        f"{cons_dict['certif_val']:.2f}",
        f"{cons_dict['oug_val']:.2f}",
    ]
    CONSUMPTION_DETAILS["Valoare TVA (19%)"] = [
        f"{cons_dict['energ_cons_tva']:.2f}",
        f"{cons_dict['acciza_tva']:.2f}",
        f"{cons_dict['certif_tva']:.2f}",
        f"{cons_dict['oug_tva']:.2f}",
    ]
    return CONSUMPTION_DETAILS

def get_romanian_month_name(bill_month):
    romanian_month_names = ["Ianuarie", "Februarie", "Martie", "Aprilie", 
        "Mai", "Iunie", "Iulie", "August", "Septembrie", "Octombrie", 
        "Noiembrie", "Decembrie"]
    return romanian_month_names[bill_month - 1]

def calculate_monthly_consumption(cursor, username, bill_year, bill_month, index_value):
    if bill_month == 1:
        cursor.execute("""SELECT index_value
                   FROM bills
                   WHERE username = ? AND bill_year = ? AND bill_month = ?
                   ORDER BY bill_year DESC, bill_month DESC
                   LIMIT 1""",
                   (username, bill_year - 1, 12))
    else:
        cursor.execute("""SELECT index_value
                   FROM bills
                   WHERE username = ? AND bill_year = ? AND bill_month = ?
                   ORDER BY bill_year DESC, bill_month DESC
                   LIMIT 1""",
                   (username, bill_year, bill_month - 1))
    previous_entry = cursor.fetchone()
    if previous_entry:
        previous_index = previous_entry[0]
        monthly_consumption = index_value - previous_index
    else:
        monthly_consumption = index_value
    return monthly_consumption

def calculate_bill_date(bill_year, bill_month):
    next_month = bill_month + 1
    if next_month > 12:
        next_month = 1
        bill_year += 1
    bill_generated_date = date(bill_year, next_month, 1)
    return bill_generated_date

def calculate_start_date(bill_year, bill_month):
    bill_start_date = date(bill_year, bill_month, 1)
    return bill_start_date

def calculate_end_date(bill_year, bill_month):
    bill_end_date = date(bill_year, bill_month, calendar.monthrange(year=bill_year, month=bill_month)[1])
    return bill_end_date

def calculate_bill_due_date(bill_year, bill_month):
    bill_due_date = calculate_bill_date(bill_year, bill_month) + relativedelta(months=1)
    return bill_due_date

def calculate_cons(cursor, username, bill_year, bill_month, index_value):
    energ_cons_cant = calculate_monthly_consumption(cursor, username, bill_year, bill_month, index_value)
    acciza_cant = calculate_monthly_consumption(cursor, username, bill_year, bill_month, index_value) / 1000
    certif_cant = acciza_cant
    oug_cant = - calculate_monthly_consumption(cursor, username, bill_year, bill_month, index_value)
    return {
        "energ_cons_cant": energ_cons_cant,
        "acciza_cant": acciza_cant,
        "certif_cant": certif_cant,
        "oug_cant": oug_cant
    }
    
def calculate_prices(cursor, username, bill_year, bill_month, index_value):
    energ_cons_val = calculate_cons(cursor, username, bill_year, bill_month, index_value)["energ_cons_cant"] * PRICE_PER_UNIT["energie_consumata"]
    energ_cons_tva = energ_cons_val * PRICE_PER_UNIT["tva"]
    acciza_val = calculate_cons(cursor, username, bill_year, bill_month, index_value)["acciza_cant"] * PRICE_PER_UNIT["acciza_necomerciala"]
    acciza_tva = acciza_val * PRICE_PER_UNIT["tva"]
    certif_val = calculate_cons(cursor, username, bill_year, bill_month, index_value)["certif_cant"] * PRICE_PER_UNIT["certificate_verzi"]
    certif_tva = certif_val * PRICE_PER_UNIT["tva"]
    oug_val = calculate_cons(cursor, username, bill_year, bill_month, index_value)["oug_cant"] * PRICE_PER_UNIT["oug_27"]
    oug_tva = oug_val * PRICE_PER_UNIT["tva"]
    total_fara_tva = energ_cons_val + acciza_val + certif_val + oug_val
    total_tva = energ_cons_tva + acciza_tva + certif_tva + oug_tva
    total_bill_value = total_fara_tva + total_tva
    return {
        "energ_cons_val": energ_cons_val,
        "energ_cons_tva": energ_cons_tva,
        "acciza_val": acciza_val,
        "acciza_tva": acciza_tva,
        "cerif_val": certif_val,
        "certif_tva": certif_tva,
        "oug_val": oug_val,
        "oug_tva": oug_tva,
        "total_fara_tva": total_fara_tva,
        "total_tva": total_tva,
        "total_bill_value": total_bill_value
    }

def get_index_input(cursor, username):
    bill_year = int(input("Introdu anul pentru care vrei sa adaugi indexul: "))
    bill_month = int(input("Introdu luna pentru care vrei sa adaugi indexul: "))
    while True:
        index_value = float(input(f"Introdu indexul pentru luna {get_romanian_month_name(bill_month)} {bill_year}: "))
        consumption = calculate_monthly_consumption(cursor, username, bill_year, bill_month, index_value)
        print(f"Conform acestui index, consumul pentru luna "
            f"{get_romanian_month_name(bill_month)} {bill_year} va fi de "
            f"{consumption} kWh.")
        check_index = input("Doresti sa continui cu acest index? (y/n) ")
        if check_index.lower() == "y":
            break
        elif check_index.lower() == "n":
            continue
    return bill_year, bill_month, index_value

def generate_bill_input():
    bill_year = int(input("Introdu anul pentru care vrei sa generezi factura PDF: "))
    bill_month = int(input("Introdu luna pentru care vrei sa generezi factura PDF: "))
    return bill_year, bill_month

def generate_excel_input():
    bill_year = int(input("Introdu anul pentru care vrei sa generezi exportul excel: "))
    return bill_year

def set_excel_name(username, bill_year, bill_serial):
    excel_name = f"export_consum_{username}-{bill_year}.xlsx"
    excel_folder = MAIN_FOLDER_ROOT / "Exporturi excel" / bill_serial
    if not os.path.exists(excel_folder):
        os.makedirs(excel_folder)
    return str(excel_folder / excel_name)

def export_excel_table(cursor, username, bill_year):
    cursor.execute("""SELECT username, bill_year, bill_month, bill_serial,
        bill_number, index_value, energ_cons_cant, energ_cons_pret, 
        energ_cons_val, energ_cons_tva, acciza_cant, acciza_pret, 
        acciza_val, acciza_tva, certif_cant, certif_pret, certif_val, 
        certif_tva, oug_cant, oug_pret, oug_val, oug_tva, total_fara_tva, 
        total_tva, total_bill_value FROM bills
        WHERE username = ? AND bill_year = ?
        ORDER BY bill_month ASC""",
        (username, bill_year))
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    df = pd.DataFrame(rows, columns=columns)
    bill_serial = ROMANIAN_COUNTIES_ABBR[get_client_info(username, cursor)["county"]]
    excel_name = set_excel_name(username, bill_year, bill_serial)
    df.to_excel(excel_name, index=False)
    print("-" * 60)
    print(f"Exportul excel pentru anul {bill_year} a fost generat cu succes!")

def provide_new_index(connection, cursor, username, bill_year, bill_month, index_value):
    cursor.execute("""
        INSERT INTO bills (user_id, username, bill_year, bill_month, bill_generated_date, bill_serial, 
        bill_number, bill_due_date, bill_start_date, bill_end_date,
        index_value, energ_cons_cant, energ_cons_pret, energ_cons_val, energ_cons_tva, acciza_cant,
        acciza_pret, acciza_val, acciza_tva, certif_cant, certif_pret, certif_val, certif_tva, oug_cant,
        oug_pret, oug_val, oug_tva, total_fara_tva, total_tva, total_bill_value)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (get_client_info(username, cursor)["id"],
        get_client_info(username, cursor)["username"],
        bill_year, bill_month,
        calculate_bill_date(bill_year, bill_month),
        ROMANIAN_COUNTIES_ABBR[get_client_info(username, cursor)["county"]], 
        f"{calculate_bill_date(bill_year, bill_month).strftime('%d%m%y')}{get_client_info(username, cursor)['id']}",
        calculate_bill_due_date(bill_year, bill_month), calculate_start_date(bill_year, bill_month), 
        calculate_end_date(bill_year, bill_month), index_value, 
        calculate_cons(cursor, username, bill_year, bill_month, index_value)["energ_cons_cant"],
        PRICE_PER_UNIT["energie_consumata"], 
        calculate_prices(cursor, username, bill_year, bill_month, index_value)["energ_cons_val"],
        calculate_prices(cursor, username, bill_year, bill_month, index_value)["energ_cons_tva"],
        calculate_cons(cursor, username, bill_year, bill_month, index_value)["acciza_cant"],
        PRICE_PER_UNIT["acciza_necomerciala"], 
        calculate_prices(cursor, username, bill_year, bill_month, index_value)["acciza_val"],
        calculate_prices(cursor, username, bill_year, bill_month, index_value)["acciza_tva"],
        calculate_cons(cursor, username, bill_year, bill_month, index_value)["certif_cant"],
        PRICE_PER_UNIT["certificate_verzi"], 
        calculate_prices(cursor, username, bill_year, bill_month, index_value)["cerif_val"],
        calculate_prices(cursor, username, bill_year, bill_month, index_value)["certif_tva"],
        calculate_cons(cursor, username, bill_year, bill_month, index_value)["oug_cant"],
        PRICE_PER_UNIT["oug_27"], 
        calculate_prices(cursor, username, bill_year, bill_month, index_value)["oug_val"],
        calculate_prices(cursor, username, bill_year, bill_month, index_value)["oug_tva"],
        calculate_prices(cursor, username, bill_year, bill_month, index_value)["total_fara_tva"],
        calculate_prices(cursor, username, bill_year, bill_month, index_value)["total_tva"],
        calculate_prices(cursor, username, bill_year, bill_month, index_value)["total_bill_value"]))
    connection.commit()
    print("-" * 60)
    print(f"Consumul pentru luna {get_romanian_month_name(bill_month)} {bill_year} a fost inregistrat cu succes!")