import calendar
from datetime import date
from dateutil.relativedelta import relativedelta
import sqlite3
from pathlib import Path

# Set the root folder path and database path
ROOT = Path(__file__).parent
DB_FILE = ROOT / "bill_database.sqlite"

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

PRICE_PER_UNIT = {
    "energie_consumata": 1.40182,
    "acciza_necomerciala": 6.05,
    "certificate_verzi": 71.68059,
    "oug_27": 0.90812,
    "tva": 0.19
}

connection = sqlite3.connect(DB_FILE)
cursor = connection.cursor()

def open_database():
    connection = sqlite3.connect(DB_FILE)
    return connection
    
def perform_database_operation(connection):
    cursor = connection.cursor()
    return cursor

def close_database(connection):
    connection.close()

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
    
    cursor.execute('''
        INSERT INTO users (name, street, zipcode, city, county, username, password, role)
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

def get_romanian_month_name(bill_month):
    romanian_month_names = [
        "Ianuarie", "Februarie", "Martie", "Aprilie", "Mai", "Iunie",
        "Iulie", "August", "Septembrie", "Octombrie", "Noiembrie", "Decembrie"
    ]
    
    return romanian_month_names[bill_month - 1] if 1 <= bill_month <= 12 else "Luna invalida!"

def calculate_monthly_consumption(cursor, username, bill_year, bill_month, index_value):
    if bill_month == 1:
        cursor.execute("""SELECT index_value
                   FROM bills
                   WHERE user_name = ? AND bill_year = ? AND bill_month = ?
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
        "total_tva": total_tva
    }
    
def provide_new_index(cursor, connection, username, bill_year, bill_month, index_value):
    cursor.execute("""
        INSERT INTO bills (user_id, user_name, bill_year, bill_month, bill_generated_date, bill_serial, 
        bill_number, bill_due_date, bill_start_date, bill_end_date,
        index_value, energ_cons_cant, energ_cons_pret, energ_cons_val, energ_cons_tva, acciza_cant,
        acciza_pret, acciza_val, acciza_tva, certif_cant, certif_pret, certif_val, certif_tva, oug_cant,
        oug_pret, oug_val, oug_tva)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (get_client_info(username, cursor)["id"],
        get_client_info(username, cursor)["name"],
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
        ))
    connection.commit()