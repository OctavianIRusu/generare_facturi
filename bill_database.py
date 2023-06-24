import calendar
import os
import sqlite3
from datetime import date
from pathlib import Path

import pandas as pd
from dateutil.relativedelta import relativedelta

# Set the root folder path and database path
MAIN_FOLDER_ROOT = Path(__file__).parent
DB_FILE = MAIN_FOLDER_ROOT / "bill_database.sqlite"

# Dictionary that maps Romanian counties to their corresponding abbreviations
RO_COUNTIES_ABBR = {
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
CONSUMPTION_TABLE_CONTENT = {
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


def open_database() -> sqlite3.Connection:
    """
    Opens a connection to the SQLite database.

    Returns:
    connection (sqlite3.Connection): A connection object representing 
        the connection to the database.

    Raises:
    sqlite3.Error: If there is an error while establishing database connection.
    """

    try:
        connection = sqlite3.connect(DB_FILE)
        return connection
    except sqlite3.Error as sqerr:
        print(f"SQLite error occurred while opening the database: {sqerr}")


def perform_database_operation(
        connection: sqlite3.Connection) -> sqlite3.Cursor:
    """
    Creates a cursor object from the given database connection.

    Args:
    connection (sqlite3.Connection): A connection object representing 
        the connection to the database.

    Returns:
    cursor (sqlite3.Cursor): A cursor object for the given connection.

    Raises:
    TypeError: If the provided connection is not of type sqlite3.Connection.
    """

    if not isinstance(connection, sqlite3.Connection):
        raise TypeError("Invalid object. Expected sqlite3.Connection.")

    try:
        cursor = connection.cursor()
        return cursor
    except sqlite3.Error as sqerr:
        print(f"SQLite error occurred while opening the database: {sqerr}")


def close_database(connection: sqlite3.Connection):
    """
    Closes the connection to the SQLite database.

    Args:
    connection (sqlite3.Connection): A connection object representing
        the connection to the database

    Raises:
    TypeError: If the provided connection is not of type sqlite3.Connection.
    sqlite3.Error: If there is an error while closing the database connection.
    """

    if not isinstance(connection, sqlite3.Connection):
        raise TypeError("Invalid object. Expected sqlite3.Connection.")

    try:
        connection.close()
    except sqlite3.Error as sqerr:
        print(f"SQLite error occurred while opening the database: {sqerr}")


def authenticate(
        username: str, password: str,
        cursor: sqlite3.Cursor) -> tuple[bool, bool]:
    """
    Authenticates a user based on the provided username and password by 
    checking against a user table in a SQLite database.

    Args:
    username (str): The username of the user.
    password (str): The password of the user.
    cursor (sqlite3.Cursor): A cursor object for executing SQL statements.

    Returns:
    tuple: A tuple containing two boolean values:
        The first value represents the authentication status:
            (True for successful authentication, False otherwise).
        The second value represents the admin status:
            (True if the authenticated user is an admin, False otherwise).

    Raises:
    TypeError: If the provided cursor is not of type sqlite3.Cursor.
    sqlite3.Error: If there is an error while executing the SQL statement 
        or fetching the result.
    """
    if not isinstance(cursor, sqlite3.Cursor):
        raise TypeError("Invalid cursor object. Expected sqlite3.Cursor.")

    try:
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
    except sqlite3.Error as sqerr:
        print(f"SQLite error occurred while opening the database: {sqerr}")


def add_new_user(connection: sqlite3.Connection, cursor: sqlite3.Cursor):
    """
    Adds a new user to the database based on the provided information.

    Args:
        connection (sqlite3.Connection): 
            A connection object to the SQLite database.
        cursor (sqlite3.Cursor): A cursor object for executing SQL statements.

    Raises:
        sqlite3.Error: If there is an error during the execution of the SQL 
            statement.
    """
    try:
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
        print("-" * 65)
        print("Noul client a fost adaugat cu succes!")
    except sqlite3.Error as sqerr:
        print(f"SQLite error occurred while opening the database: {sqerr}")

def delete_user(connection: sqlite3.Connection, cursor: sqlite3.Cursor):
    """
    Remove a user from the database based on the username.

    Args:
        connection (sqlite3.Connection): 
            A connection object to the SQLite database.
        cursor (sqlite3.Cursor): A cursor object for executing SQL statements.
    
    Raises:
        LookupError: If there is no user found in the database with the
            specified username
        KeyboardInterrupt: If the confirmation of deletion is canceled
        sqlite3.Error: If there is an error during the execution of the SQL 
            statement.
    """
    try:
        username = str(input("Introdu username-ul clientului pe care doresti sa il elimini: "))
        cursor.execute('''SELECT COUNT(*) FROM users
                       WHERE username = ?''',
                       (username,))
        result = cursor.fetchone()
        if result[0] == 0:
            raise LookupError("Nu a fost gasit niciun client cu acest username!")
        while True:
            confirmation = input(f"Esti sigur ca doresti sa stergi user-ul {username}? y/n ")
            if confirmation.lower() == "n":
                raise KeyboardInterrupt("Stergere anulata!")
            if confirmation.lower() == "y":
                cursor.execute('''DELETE FROM users
                            WHERE username = ?''',
                            (username,))
                print("-" * 65)
                print("Clientul a fost sters cu succes!")
                connection.commit()
                connection.close()
                break
            else:
                print("""Alegere invalida! Alege intre 'y' si 'n'.""")
    except sqlite3.Error as sqerr:
        raise RuntimeError("An error occurred while accessing the database.") from sqerr

def get_client_info(username: str, cursor: sqlite3.Cursor) -> dict:
    """
    Get client information from the database based on the provided username.

    Args:
        username (str): The username of the client.
        cursor (sqlite3.Cursor): A cursor object for executing SQL statements.

    Returns:
        dict or None: A dictionary containing the client information 
            if the username is found in the database.
            The keys of the dictionary represent the column names from the 
            'users' table, and the values represent the corresponding data 
            for the client. 
            If the username is not found in the database, None is returned.

    Raises:
        sqlite3.Error: If there is an error during the execution of the SQL 
            statement.
    """
    try:
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        if row:
            columns = [desc[0] for desc in cursor.description]
            user_dict = dict(zip(columns, row))
            return user_dict
        else:
            return None
    except sqlite3.Error as sqerr:
        print(f"SQLite error occurred while opening the database: {sqerr}")


def get_bill_info(
        username: str,
        bill_year: int, bill_month: int,
        cursor: sqlite3.Cursor) -> dict:
    """
    Get bill information from the database based on the provided username, 
    bill year, and bill month.

    Args:
        username (str): The username associated with the bill.
        bill_year (int): The year of the bill.
        bill_month (int): The month of the bill.
        cursor (sqlite3.Cursor): A cursor object for executing SQL statements.

    Returns:
        dict or None: A dictionary containing the bill information if a 
            matching bill is found in the database. The keys of the dictionary 
            represent the column names from the 'bills' table, and the values 
            represent the corresponding data for the bill.
            If no matching bill is found, None is returned.

    Raises:
        sqlite3.Error: If there is an error during the execution of the SQL 
            statement.
    """
    try:
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
    except sqlite3.Error as sqerr:
        print(f"SQLite error occurred while opening the database: {sqerr}")


def create_consumption_table(
        username: str,
        bill_year: int, bill_month: int,
        cursor: sqlite3.Cursor) -> dict:
    """
    Creates a consumption table for a specific username and bill.

    Args:
        username (str): The username associated with the bill.
        bill_year (int): The year of the bill.
        bill_month (int): The month of the bill.
        cursor: A cursor object for executing SQL statements.

    Returns:
        Dict: A dictionary representing the consumption table.
            The keys of the dictionary represent the table column names,
            and the values are lists containing the corresponding data.

    Raises:
        sqlite3.Error: If there is an error during the execution of the SQL 
            statement.
    """
    try:
        cons_dict = get_bill_info(username, bill_year, bill_month, cursor)
        CONSUMPTION_TABLE_CONTENT["Cantitate"] = [
            f"{cons_dict['energ_cons_cant']:.2f}",
            f"{cons_dict['acciza_cant']:.2f}",
            f"{cons_dict['certif_cant']:.2f}",
            f"{cons_dict['oug_cant']:.2f}",
        ]
        CONSUMPTION_TABLE_CONTENT["Pret unitar fara TVA"] = [
            f"{PRICE_PER_UNIT['energie_consumata']:.2f}",
            f"{PRICE_PER_UNIT['acciza_necomerciala']:.2f}",
            f"{PRICE_PER_UNIT['certificate_verzi']:.2f}",
            f"{PRICE_PER_UNIT['oug_27']:.2f}"
        ]
        CONSUMPTION_TABLE_CONTENT["Valoare fara TVA"] = [
            f"{cons_dict['energ_cons_val']:.2f}",
            f"{cons_dict['acciza_val']:.2f}",
            f"{cons_dict['certif_val']:.2f}",
            f"{cons_dict['oug_val']:.2f}",
        ]
        CONSUMPTION_TABLE_CONTENT["Valoare TVA (19%)"] = [
            f"{cons_dict['energ_cons_tva']:.2f}",
            f"{cons_dict['acciza_tva']:.2f}",
            f"{cons_dict['certif_tva']:.2f}",
            f"{cons_dict['oug_tva']:.2f}",
        ]
        return CONSUMPTION_TABLE_CONTENT
    except sqlite3.Error as sqerr:
        print(f"SQLite error occurred while opening the database: {sqerr}")


def get_romanian_month_name(bill_month: int) -> str:
    """
    Returns the Romanian name of a given month.

    Args:
        bill_month (int): The month for which to retrieve the Romanian name.

    Returns:
        str: The Romanian name of the month.

    Raises:
        ValueError: If the provided month is out of range (not between 1 and 12).
    """
    try:
        romanian_month_names = ["Ianuarie", "Februarie", "Martie", "Aprilie",
                                "Mai", "Iunie", "Iulie", "August", "Septembrie", "Octombrie",
                                "Noiembrie", "Decembrie"]
        return romanian_month_names[bill_month - 1]
    except IndexError:
        raise ValueError("Invalid month. Month must be between 1 and 12.")


def calculate_monthly_consumption(
        cursor: sqlite3.Cursor,
        username: str,
        bill_year: int, bill_month: int, index_value: float) -> float:
    """
    Calculates the monthly consumption based on the provided index value.

    Args:
        cursor: The SQLite cursor object.
        username (str): The username of the user.
        bill_year (int): The year of the bill.
        bill_month (int): The month of the bill.
        index_value (float): The current index value.

    Returns:
        float: The calculated monthly consumption.

    Raises:
        sqlite3.Error: If there is an error executing the SQL query.
        ValueError: If the provided bill month or year is out of range.
    """
    try:
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
    except sqlite3.Error as sqerr:
        print(f"SQLite error occurred while opening the database: {sqerr}")
    except ValueError as verr:
        raise ValueError(f"Invalid bill month or year: {str(verr)}")


def calculate_bill_date(bill_year: int, bill_month: int) -> date:
    """
    Calculates the bill generation date based on the provided bill year and month.

    Args:
        bill_year (int): The year of the bill.
        bill_month (int): The month of the bill.

    Returns:
        date: The calculated bill generation date.

    Raises:
        ValueError: If the provided bill month or year is out of range.
    """
    try:
        next_month = bill_month + 1
        if next_month > 12:
            next_month = 1
            bill_year += 1
        bill_generated_date = date(bill_year, next_month, 1)
        return bill_generated_date
    except ValueError as verr:
        raise ValueError(f"Invalid bill month or year: {str(verr)}")


def calculate_start_date(bill_year: int, bill_month: int) -> date:
    """
    Calculates the start date of the billing period based on the provided 
    bill year and month.

    Args:
        bill_year (int): The year of the bill.
        bill_month (int): The month of the bill.

    Returns:
        date: The calculated start date of the billing period.

    Raises:
        ValueError: If the provided bill month or year is out of range.
    """
    try:
        bill_start_date = date(bill_year, bill_month, 1)
        return bill_start_date
    except ValueError as verr:
        raise ValueError(f"Invalid bill month or year: {str(verr)}")


def calculate_end_date(bill_year: int, bill_month: int) -> date:
    """
    Calculates the end date of the billing period based on the provided 
    bill year and month.

    Args:
        bill_year (int): The year of the bill.
        bill_month (int): The month of the bill.

    Returns:
        date: The calculated end date of the billing period.

    Raises:
        ValueError: If the provided bill month or year is out of range.
    """
    try:
        bill_end_date = date(
            bill_year, bill_month,
            calendar.monthrange(year=bill_year, month=bill_month)[1])
        return bill_end_date
    except ValueError as verr:
        raise ValueError(f"Invalid bill month or year: {str(verr)}")


def calculate_bill_due_date(bill_year: int, bill_month: int) -> date:
    """
    Calculates the due date of the bill based on the provided year and month.

    Args:
        bill_year (int): The year of the bill.
        bill_month (int): The month of the bill.

    Returns:
        date: The calculated due date of the bill.

    Raises:
        ValueError: If the provided bill month or year is out of range.
    """
    try:
        bill_due_date = (calculate_bill_date(bill_year, bill_month)
                         + relativedelta(months=1))
        return bill_due_date
    except ValueError as verr:
        raise ValueError(f"Invalid bill month or year: {str(verr)}")


def calculate_cons(
        cursor: sqlite3.Cursor,
        username: str,
        bill_year: int, bill_month: int, index_value: float) -> dict:
    """
    Calculates the consumption values based on the provided parameters.

    Args:
        cursor (sqlite3.Cursor): The database cursor object.
        username (str): The username of the user.
        bill_year (int): The year of the bill.
        bill_month (int): The month of the bill.
        index_value (float): The index value for consumption calculation.

    Returns:
        dict: A dictionary containing the calculated consumption values.

    Raises:
        ValueError: If the provided username, bill month, bill year is invalid.
        TypeError: If the index_value is not a valid float value.
    """
    try:
        energ_cons_cant = calculate_monthly_consumption(
            cursor, username, bill_year, bill_month, index_value)
        acciza_cant = calculate_monthly_consumption(
            cursor, username, bill_year, bill_month, index_value) / 1000
        certif_cant = acciza_cant
        oug_cant = - calculate_monthly_consumption(
            cursor, username, bill_year, bill_month, index_value)
        return {
            "energ_cons_cant": energ_cons_cant,
            "acciza_cant": acciza_cant,
            "certif_cant": certif_cant,
            "oug_cant": oug_cant
        }
    except ValueError as verr:
        raise ValueError(f"Invalid username, bill month, or bill year: {verr}")


def calculate_prices(
        cursor: sqlite3.Cursor,
        username: str,
        bill_year: int, bill_month: int, index_value: float) -> dict:
    """
    Calculates the prices for each consumption component and the total bill 
    value based on the provided parameters.

    Args:
        cursor (sqlite3.Cursor): The database cursor object.
        username (str): The username of the user.
        bill_year (int): The year of the bill.
        bill_month (int): The month of the bill.
        index_value (float): The index value for consumption calculation.

    Returns:
        dict: A dictionary containing the calculated prices and total bill value.

    Raises:
        ValueError: If the provided username, bill month, or bill year is invalid.
        TypeError: If the index_value is not a valid float value.
    """
    try:
        consumption = calculate_cons(
            cursor, username, bill_year, bill_month, index_value)

        energ_cons_val = (consumption["energ_cons_cant"]
                          * PRICE_PER_UNIT["energie_consumata"])
        energ_cons_tva = energ_cons_val * PRICE_PER_UNIT["tva"]

        acciza_val = (consumption["acciza_cant"]
                      * PRICE_PER_UNIT["acciza_necomerciala"])
        acciza_tva = acciza_val * PRICE_PER_UNIT["tva"]

        certif_val = (consumption["certif_cant"]
                      * PRICE_PER_UNIT["certificate_verzi"])
        certif_tva = certif_val * PRICE_PER_UNIT["tva"]

        oug_val = consumption["oug_cant"] * PRICE_PER_UNIT["oug_27"]
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
    except ValueError as verr:
        raise ValueError(
            f"Invalid username/ bill month/ bill year: {str(verr)}")
    except TypeError as terr:
        raise TypeError(f"Invalid index_value: {str(terr)}")


def get_index_input(cursor: sqlite3.Cursor, username: str) -> tuple:
    """
    Prompts the user to enter the bill year, bill month, and index value 
    for consumption calculation.

    Args:
        cursor (sqlite3.Cursor): The database cursor object.
        username (str): The username of the user.

    Returns:
        Tuple: A tuple containing the bill year, bill month, and index value.

    Raises:
        ValueError: If the provided bill year or bill month is not integer.
        ValueError: If the provided index value is not a valid float.
        ValueError: If the provided bill month is out of range.
        ValueError: If the provided bill year is not within the valid range
            (2020 to current year).
    """
    try:
        bill_year = int(
            input("Introdu anul pentru care vrei sa adaugi indexul: "))
        bill_month = int(
            input("Introdu luna pentru care vrei sa adaugi indexul: "))

        if not 1 <= bill_month <= 12:
            raise ValueError(
                "Invalid month. Please enter a value between 1 and 12.")

        current_year = date.today().year
        if not 2020 <= bill_year <= current_year:
            raise ValueError(
                f"Invalid Year. Please enter a value between 2020 and {current_year}.")

        while True:
            index_value = float(input(
                f"""Introdu indexul pentru luna {get_romanian_month_name(bill_month)} {bill_year}: """))
            consumption = calculate_monthly_consumption(cursor, username,
                                                        bill_year, bill_month, index_value)
            print(f"Conform acestui index, consumul pentru luna "
                  f"{get_romanian_month_name(bill_month)} {bill_year} va fi de "
                  f"{consumption} kWh.")
            check_index = input("Doresti sa continui cu acest index? (y/n) ")
            if check_index.lower() == "y":
                break
            elif check_index.lower() == "n":
                continue
        return bill_year, bill_month, index_value
    except TypeError as terr:
        print(f"Invalid index value: {str(terr)}")


def generate_bill_input() -> tuple:
    """
    Prompts the user to enter the bill year and bill month for generating a
    PDF bill.

    Returns:
        Tuple: A tuple containing the bill year and bill month.

    Raises:
        ValueError: If the provided bill year or bill month is not a valid integer.
        ValueError: If the provided bill month is out of range (not between 1 and 12).
    """
    try:
        bill_year = int(input(
            "Introdu anul pentru care vrei sa generezi factura PDF: "))
        bill_month = int(input(
            "Introdu luna pentru care vrei sa generezi factura PDF: "))

        if not 1 <= bill_month <= 12:
            raise ValueError("""Invalid month. 
                    Please enter a value between 1 and 12.""")

        current_year = date.today().year
        if not 2020 <= bill_year <= current_year:
            raise ValueError(f"""Invalid Year. 
                    Please enter a value between 2020 and {current_year}.""")

        return bill_year, bill_month
    except TypeError as terr:
        print(terr)


def generate_excel_input() -> int:
    """
    Prompts the user to enter the bill year for generating an Excel export.

    Returns:
        int: The bill year entered by the user.

    Raises:
        ValueError: If the provided bill year is not integer or is out of range.
    """
    bill_year = int(input(
        "Introdu anul pentru care vrei sa generezi exportul excel: "))
    current_year = date.today().year
    if not 2020 <= bill_year <= current_year:
        raise ValueError(f"""Invalid Year. 
                Please enter a value between 2020 and {current_year}.""")
    return bill_year


def set_excel_name(username: str, bill_year: int, bill_serial: str) -> str:
    """
    Sets the name and path for the Excel export file.

    Args:
        username (str): The username associated with the export.
        bill_year (int): The bill year associated with the export.
        bill_serial (str): The bill serial associated with the export.

    Returns:
        str: The full path of the Excel export file.

    Raises:
        OSError: If there is an error creating the directory for the export file.
    """
    try:
        excel_name = f"export_consum_{username}-{bill_year}.xlsx"
        excel_folder = MAIN_FOLDER_ROOT / "Exporturi excel" / bill_serial

        if not os.path.exists(excel_folder):
            os.makedirs(excel_folder)

        return str(excel_folder / excel_name)
    except OSError as oserr:
        raise OSError(
            f"""Error creating directory for the Excel export: {str(oserr)}""")


def export_excel_table(cursor: sqlite3.Cursor, username: str, bill_year: int):
    """
    Export the bill data for a specific year from database to an Excel file.

    Args:
        cursor (sqlite3.Cursor): The SQLite cursor.
        username (str): The username associated with the bills.
        bill_year (int): The year for which the bills should be exported.

    Raises:
        OSError: If there is an error creating the directory for the file.
    """
    try:
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

        bill_serial = (
            RO_COUNTIES_ABBR[get_client_info(username, cursor)["county"]])
        excel_name = set_excel_name(username, bill_year, bill_serial)

        if not os.path.exists(os.path.dirname(excel_name)):
            os.makedirs(os.path.dirname(excel_name))

        df.to_excel(excel_name, index=False)
        print("-" * 60)
        print(
            f"Exportul excel pentru anul {bill_year} a fost generat cu succes!")
    except OSError as oserr:
        raise OSError(f"""Error creating directory for the Excel export: 
            {str(oserr)}""")


def provide_new_index(
        connection: sqlite3.Connection, cursor: sqlite3.Cursor,
        username: str, bill_year: int, bill_month: int, index_value: float):
    """
    Insert a new index value and calculate and insert the corresponding bill 
    details into the database.

    Args:
        connection (sqlite3.Connection): The SQLite database connection.
        cursor (sqlite3.Cursor): The SQLite cursor.
        username (str): The username associated with the index value and bill.
        bill_year (int): The year of the bill.
        bill_month (int): The month of the bill.
        index_value (float): The new index value.

    Raises:
        ValueError: If the bill month or year is invalid.
        sqlite3.Error: If there is an error executing the SQL statement.
    """
    try:
        bill_generated_date = calculate_bill_date(bill_year, bill_month)
        bill_due_date = calculate_bill_due_date(bill_year, bill_month)
        bill_start_date = calculate_start_date(bill_year, bill_month)
        bill_end_date = calculate_end_date(bill_year, bill_month)

        cons_data = calculate_cons(
            cursor, username, bill_year, bill_month, index_value)
        price_data = calculate_prices(
            cursor, username, bill_year, bill_month, index_value)

        cursor.execute("""
            INSERT INTO bills (
                user_id, username, bill_year, bill_month, bill_generated_date, 
                bill_serial, bill_number, bill_due_date, bill_start_date, 
                bill_end_date, index_value, energ_cons_cant, energ_cons_pret, 
                energ_cons_val, energ_cons_tva, acciza_cant, acciza_pret, 
                acciza_val, acciza_tva, certif_cant, certif_pret, certif_val, 
                certif_tva, oug_cant, oug_pret, oug_val, oug_tva, 
                total_fara_tva, total_tva, total_bill_value
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            get_client_info(username, cursor)["id"],
            get_client_info(username, cursor)["username"],
            bill_year,
            bill_month,
            bill_generated_date,
            RO_COUNTIES_ABBR[get_client_info(username, cursor)["county"]],
            "{}{}".format(bill_generated_date.strftime('%d%m%y'),
                          str(get_client_info(username, cursor)['id']).zfill(6)),
            bill_due_date,
            bill_start_date,
            bill_end_date,
            index_value,
            cons_data["energ_cons_cant"],
            PRICE_PER_UNIT["energie_consumata"],
            price_data["energ_cons_val"],
            price_data["energ_cons_tva"],
            cons_data["acciza_cant"],
            PRICE_PER_UNIT["acciza_necomerciala"],
            price_data["acciza_val"],
            price_data["acciza_tva"],
            cons_data["certif_cant"],
            PRICE_PER_UNIT["certificate_verzi"],
            price_data["cerif_val"],
            price_data["certif_tva"],
            cons_data["oug_cant"],
            PRICE_PER_UNIT["oug_27"],
            price_data["oug_val"],
            price_data["oug_tva"],
            price_data["total_fara_tva"],
            price_data["total_tva"],
            price_data["total_bill_value"]
        ))
        connection.commit()
        print("-" * 65)
        print("Consumul pentru luna {} {} a fost inregistrat cu succes!".
              format(get_romanian_month_name(bill_month), bill_year))
    except ValueError as verr:
        raise ValueError(f"Invalid bill month or year: {str(verr)}")

    except sqlite3.Error as sqerr:
        raise sqlite3.Error(f"SQLite error occurred: {str(sqerr)}")
