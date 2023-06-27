"""
This module contains functions for creating entries in SQLite database, which
contains an user table and a bills table. All the functions interact both with
user and database, in order to input values and extract informations for pdf or
excel exports, and to monitor the energy consumption per month for every user.

The module provides the following functions:

    open_database, perform_database_operation, close_database: These functions
        handle the database interaction by opening, creating the cursor and
        closing the connection once the necessary database operations have
        been performed.
    authenticate: Authenticates a user based on the provided username and 
        password by checking against a user table in a SQLite database.
    add_new_user, delete_user, modify_user_info: Functions that need admin
        rights in order to modify the users entries in the users table.
    get_client_info, get_bill_info: Functions which interact with the database
        in order to collect all the client and consumption information for
        a specific time stamp, and being used to create exports.
    create_consumption_table, get_romanian_month_name, calculate_cons,
    calculate_monthly_consumption, calculate_bill_date, calculate_start_date,
    calculate_end_date, calculate_bill_due_date, calculate_prices: All these
        functions are tools used to fill all the needed information in the bills
        table in the database, and are used lately for filling the information
        in the pdf invoice and excel export.
    get_index_input, generate_bill_input, provide_index: Functions used in
        user interaction with the database, by which the user provides new
        information related to energy consumption.
    generate_excel_input, set_excel_name, export_excel_table: Functions used to
        get the consumption information in excel format for a whole year.
        
Please note that this module requires the following external libraries:
    
    pandas: A library for manipulating and analyzing structured data, 
        such as numerical tables and time series data
    sqlite3: A libray that provides an interface to the SQLite database engine. 
        It allows you to interact with SQLite databases using SQL queries 
        and perform various operations such as creating tables, inserting data,
        querying data, and modifying data.
"""

import calendar
import os
import sqlite3
import subprocess
from datetime import date
from pathlib import Path
import csv

import pandas as pd
from dateutil.relativedelta import relativedelta

LINE_SEPARATOR = "-" * 80

# Set the root folder path and database path
MAIN_FOLDER_ROOT = Path(__file__).parent
DB_FILE = MAIN_FOLDER_ROOT / "bill_database.sqlite"
LOCALITY_LIST_FILE = MAIN_FOLDER_ROOT / "lista_localitati.csv"

# Dictionary that maps Romanian counties to their corresponding abbreviations
RO_COUNTIES_ABBR = {
    "Alba": "AB", "Arad": "AR", "Arges": "AG", "Bacau": "BC", "Bihor": "BH",
    "Bistrita-Nasaud": "BN", "Botosani": "BT", "Brasov": "BV", "Braila": "BR",
    "Buzau": "BZ", "Caras-Severin": "CS", "Calarasi": "CL", "Cluj": "CJ",
    "Constanta": "CT", "Covasna": "CV", "Dambovita": "DB", "Dolj": "DJ",
    "Galati": "GL", "Giurgiu": "GR", "Gorj": "GJ", "Harghita": "HR",
    "Hunedoara": "HD", "Ialomita": "IL", "Iasi": "IS", "Ilfov": "IF",
    "Maramures": "MM", "Mehedinti": "MH", "Mures": "MS", "Neamt": "NT",
    "Olt": "OT", "Prahova": "PH", "Satu Mare": "SM", "Salaj": "SJ",
    "Sibiu": "SB", "Suceava": "SV", "Teleorman": "TR", "Timis": "TM",
    "Tulcea": "TL", "Vaslui": "VS", "Valcea": "VL", "Vrancea": "VN"
}

# Dictionary that stores the price per unit for various charge categories
PRICE_PER_UNIT = {
    "energie_consumata": 1.40182, "acciza_necomerciala": 6.05,
    "certificate_verzi": 71.68059, "oug_27": 0.90812
}

# Current TVA value
TVA = 0.19

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

def open_database() -> sqlite3.Connection:
    """
    Opens a connection to the SQLite database.

    Returns:
    connection (sqlite3.Connection): A connection object.

    Raises:
    sqlite3.Error: If there is an error while establishing database connection.
    """
    connection = sqlite3.connect(DB_FILE)
    return connection

def perform_database_operation(connection: sqlite3.Connection) -> sqlite3.Cursor:
    """
    Creates a cursor object from the given database connection.

    Args:
    connection (sqlite3.Connection): A connection object.
    
    Returns:
    cursor (sqlite3.Cursor): A cursor object for the given connection.
    """
    
    cursor = connection.cursor()
    return cursor

def close_database(connection: sqlite3.Connection):
    """
    Closes the connection to the SQLite database.

    Args:
    connection (sqlite3.Connection): A connection object.

    Raises:
    sqlite3.Error: If there is an error while closing the database connection.
    """

    try:
        connection.close()
    except sqlite3.Error as sqerr:
        raise sqlite3.Error(f"Eroare la inchiderea bazei de date!") from sqerr

def authenticate(
    username: str, password: str,
    cursor: sqlite3.Cursor) -> tuple[bool, bool]:
    """
    Authenticates a user based on the provided username and password by 
    checking against a user table in a SQLite database.

    Args:
    username (str): The username provided by the user.
    password (str): The password provided by the user.
    cursor (sqlite3.Cursor): A cursor object for executing SQL statements.

    Returns:
        tuple: A tuple containing two values: authentication and admin status.

    Raises:
        sqlite3.Error: If there is an error while executing the SQL statement.
    """
    cursor.execute(
        """SELECT role FROM users
        WHERE username = ? AND password = ?""", (username, password))
    result = cursor.fetchone()
    if result:
        role = result[0]
        if role == 'admin':
            return True, True
        return True, False
    return False, False

def check_location_exists(location, file_path):
    """
    Checks if a county exists in the specified CSV file.

    Args:
        location (str): The county/locality name to search for.
        file_path (str): The path to the CSV file.

    Returns:
        bool: True if the location exists, False otherwise.

    Raises:
        FileNotFoundError: If the specified file does not exist.
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        for row in reader:
            if location.capitalize() in row:
                return True
    return False

def get_zipcode(location, file_path):
    """
    Retrieves the ZIP code associated with a given locality from a CSV file.

    Args:
        locality (str): The name of the locality.
        file_path (str): The path to the CSV file.

    Returns:
        str: The ZIP code for the specified locality, or None if not found.
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        for row in reader:
            if row[0] == location.capitalize():
                return row[3]
    return None

def add_new_user(connection: sqlite3.Connection, cursor: sqlite3.Cursor):
    """
    Adds a new user to the database based on the provided information.

    Args:
        connection (sqlite3.Connection): A connection object.
        cursor (sqlite3.Cursor): A cursor object for executing SQL statements.

    Raises:
        sqlite3.Error: If an error occurs when SQL statement is executed.
    """
    while True:
        try:
            name = input("Introdu prenume si nume: ")
            name_parts = name.strip().split()
            formatted_name = ' '.join([part.capitalize() for part in name_parts])
            if len(name_parts) < 2:
                raise ValueError("Numele trebuie sa contina un prenume si un nume!")
            break
        except ValueError as verr:
            print(LINE_SEPARATOR)
            print(verr)
            print(LINE_SEPARATOR)
    while True:
        try:
            county = input("Introdu judetul: ")
            if not check_location_exists(county, LOCALITY_LIST_FILE):
                raise ValueError("Judetul furnizat nu exista!")
            break
        except ValueError as verr:
            print(LINE_SEPARATOR)
            print(verr)
            print(LINE_SEPARATOR)
    while True:
        try:
            city = input("Introdu localitatea: ")
            if not check_location_exists(city, LOCALITY_LIST_FILE):
                raise ValueError("Localitatea furnizata nu exista!")
            break
        except ValueError as verr:
            print(LINE_SEPARATOR)
            print(verr)
            print(LINE_SEPARATOR)

    street = input("Introdu adresa (strada, nr, bloc, apartament): ")
    zipcode = get_zipcode(city, LOCALITY_LIST_FILE)
    username = "".join([s.lower() for s in name.split()])
    password = username
    role = input("Alege tip user (user/admin): ")
    try:
        if role.lower() not in ["user", "admin"]:
            raise ValueError("Rolul ales poate fi doar 'user' sau 'admin'!")
        cursor.execute('''INSERT INTO users (
            name, street, zipcode, city, county, username, password, role)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
            (formatted_name, street, zipcode, city, county, username, password, role))
        connection.commit()
        print(LINE_SEPARATOR)
        print("Noul client a fost adaugat cu succes!")
        print(f"Date de autentificare: username: {username}, parola: {password}.")
    except sqlite3.Error as sqerr:
        print(f"Eroare la accesarea bazei de date: {sqerr}")
    except FileNotFoundError as fnferr:
        print(f"Lista cu localitati nu a putut fi accesata: {fnferr}")

def search_user(cursor: sqlite3.Cursor):
    """
    Searches for a user in the 'users' table based on the username.

    Args:
        cursor (sqlite3.Cursor): The cursor object for executing SQL queries.
    
    Returns:
        username (str): The username of the existing client.
        
    Raises:
        LookupError: If no client with the given username is found in the table.
    """
    while True:
        username = str(input("Introdu username-ul clientului: "))
        cursor.execute('''SELECT COUNT(*) FROM users
                       WHERE username = ?''', (username,))
        result = cursor.fetchone()
        if result[0] == 0:
            raise LookupError(f'Nu exista niciun client "{username}"!')
        break
    return username

def modify_user_address(connection: sqlite3.Connection, cursor: sqlite3.Cursor):
    """
    Modifies a specific field in the users table of the SQLite database.

    Args:
        connection (sqlite3.Connection): A connection object.
        cursor (sqlite3.Cursor): The cursor object for executing SQL queries.

    Raises:
        sqlite3.Error: If there is an error while executing the SQL statement.
    """
    try:
        username = search_user(cursor)
        street = input("Introdu numele noii strazi: ")
        zipcode = input("Introdu noul cod postal: ")
        city = input("Introdu noua localitate: ")
        county = input("Introdu noul judet: ")
        cursor.execute('''UPDATE users SET street = ?, zipcode = ?,
                       city = ?, county = ?
                       WHERE username = ?''',
                       (street, zipcode, city, county, username))
        connection.commit()
        print(LINE_SEPARATOR)
        print("Informatiile au fost actualizate cu succes!")
    except LookupError as lerr:
            print(lerr)
    except sqlite3.Error as sqerr:
        print(f"Eroare la accesarea bazei de date: {sqerr}")

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
        username = search_user(cursor)
        while True:
            confirmation = input(f"Esti sigur ca doresti sa stergi user-ul {username}? y/n ")
            if confirmation.lower() == "n":
                raise KeyboardInterrupt("Stergere anulata!")
            if confirmation.lower() == "y":
                cursor.execute('''DELETE FROM users
                            WHERE username = ?''',
                            (username,))
                print(LINE_SEPARATOR)
                print("Clientul a fost sters cu succes!")
                connection.commit()
                connection.close()
                break
            print("""Alegere invalida! Alege 'y' sau 'n'.""")
    except sqlite3.Error as sqerr:
        raise RuntimeError("An error occurred while accessing the database.") from sqerr

def get_client_info(username: str, cursor: sqlite3.Cursor) -> dict:
    """
    Get client information from the database based on the provided username.

    Args:
        username (str): The username of the client.
        cursor (sqlite3.Cursor): A cursor object for executing SQL statements.

    Returns:
        dict: A dictionary containing the client information if the username 
            is found in the database. The keys of the dictionary represent 
            the column names from the 'users' table, and the values represent 
            the corresponding data for the client. 

    Raises:
        sqlite3.Error: If there is an error during the execution of the SQL 
            statement.
        TypeError: If data is missing in database or if there is no valid 
            data extracted from database.
    """
    try:
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        try:
            columns = [desc[0] for desc in cursor.description]
            user_dict = dict(zip(columns, row))
            return user_dict
        except TypeError:
            print(f'Eroare: Nu exista niciun client cu username-ul "{username}"!')
    except sqlite3.Error as sqerr:
        print(f"SQLite error occurred while opening the database: {sqerr}")

def get_bill_info(
    username: str, bill_year: int, bill_month: int,
    cursor: sqlite3.Cursor) -> dict:
    """
    Get bill information from the database for a specific month.

    Args:
        username (str): The username associated with the bill.
        bill_year (int): The year of the bill.
        bill_month (int): The month of the bill.
        cursor (sqlite3.Cursor): A cursor object for executing SQL statements.

    Returns:
        dict: A dictionary containing the bill information.

    Raises:
        sqlite3.Error: If an error occurs during the execution of the SQL code.
        TypeError: If there is no valid data extracted from database.
    """
    try:
        cursor.execute("""SELECT * FROM bills
                       WHERE username = ? AND bill_year = ? AND bill_month = ?""",
                       (username, bill_year, bill_month))
        row = cursor.fetchone()
        try:
            columns = [desc[0] for desc in cursor.description]
            bill_info_dict = dict(zip(columns, row))
            return bill_info_dict
        except TypeError:
            month_name = get_romanian_month_name(bill_month)
            print(f"Eroare: Nu exista nicio factura pentru luna {month_name} {bill_year}!")
    except sqlite3.Error as sqerr:
        print(f"Eroare la conectarea la baza de date: {sqerr}")

def create_consumption_table(
        username: str,
        bill_year: int, 
        bill_month: int,
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
        print(f"Eroare la conectarea la baza de date: {sqerr}")
    except (ValueError, KeyError, TypeError) as err:
        print(f"Eroare la obtinerea detaliilor de consum (tabel): {err}")

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
    romanian_month_names = [
        "Ianuarie", "Februarie", "Martie", "Aprilie", "Mai", "Iunie", "Iulie",
        "August", "Septembrie", "Octombrie", "Noiembrie", "Decembrie"]
    try:
        return romanian_month_names[bill_month - 1]
    except IndexError as ierr:
        raise IndexError(
            "Invalid month. Month must be between 1 and 12.") from ierr

def calculate_monthly_consumption(
    cursor: sqlite3.Cursor, username: str, bill_year: int, bill_month: int,
    index_value: float) -> float:
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
        raise ValueError(f"Invalid bill month or year: {str(verr)}") from verr

def calculate_bill_period(bill_year: int, bill_month: int) -> date:
    """
    Calculates the start and end date of the billing period and also the
    generation date and due date of the bill.

    Args:
        bill_year (int): The year of the bill.
        bill_month (int): The month of the bill.

    Returns:
        tuple: A tuple of dates that contains the billing period and bill
        generation and due date.

    Raises:
        ValueError: If the provided bill month or year is out of range.
    """
    try:
        bill_start_date = date(bill_year, bill_month, 1)
        last_day = calendar.monthrange(year=bill_year, month=bill_month)[1]
        bill_end_date = date(bill_year, bill_month, last_day)
        next_month = bill_month + 1
        if next_month > 12:
            next_month = 1
            bill_year += 1
        bill_generated_date = date(bill_year, next_month, 1)
        bill_due_date = bill_generated_date + relativedelta(months=1)
        return bill_start_date, bill_end_date, bill_generated_date, bill_due_date
    except ValueError as verr:
        raise ValueError(f"Invalid bill month or year: {str(verr)}") from verr

def calculate_cons(cursor: sqlite3.Cursor, username: str, bill_year: int,
                   bill_month: int, index_value: float) -> dict:
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
    """
    try:
        energ_cons_cant = calculate_monthly_consumption(
            cursor, username, bill_year, bill_month, index_value)
        acciza_cant = calculate_monthly_consumption(
            cursor, username, bill_year, bill_month, index_value) / 1000
        certif_cant = acciza_cant
        oug_cant = - calculate_monthly_consumption(
            cursor, username, bill_year, bill_month, index_value)
        return energ_cons_cant, acciza_cant, certif_cant, oug_cant
    except ValueError as verr:
        raise ValueError(f"Invalid data: {verr}") from verr

def calculate_prices(cursor: sqlite3.Cursor, username: str, bill_year: int,
                     bill_month: int, index_value: float) -> tuple:
    """
    Calculates the prices for each consumption parameter and total bill value.

    Args:
        cursor (sqlite3.Cursor): The database cursor object.
        username (str): The username of the user.
        bill_year (int): The year of the bill.
        bill_month (int): The month of the bill.
        index_value (float): The index value for consumption calculation.

    Returns:
        tuple: A tuple containing the calculated prices and total bill value.

    Raises:
        ValueError: If username, bill month, or bill year is invalid.
        TypeError: If the index_value is not a valid float value.
    """
    try:
        energ_cons_cant, acciza_cant, certif_cant, oug_cant = (
            calculate_cons(cursor, username, bill_year, bill_month, index_value))
        energie_consumata, acciza_necomerciala, certificate_verzi, oug_27 = (
            PRICE_PER_UNIT.values())
        energ_cons_val = energ_cons_cant * energie_consumata
        energ_cons_tva = energ_cons_val * TVA
        acciza_val = acciza_cant * acciza_necomerciala
        acciza_tva = acciza_val * TVA
        certif_val = certif_cant * certificate_verzi
        certif_tva = certif_val * TVA
        oug_val = oug_cant * oug_27
        oug_tva = oug_val * TVA
        total_fara_tva = energ_cons_val + acciza_val + certif_val + oug_val
        total_tva = energ_cons_tva + acciza_tva + certif_tva + oug_tva
        total_bill_value = total_fara_tva + total_tva
        return (energ_cons_val, energ_cons_tva, acciza_val, acciza_tva, 
                certif_val, certif_tva, oug_val, oug_tva, total_fara_tva,
                total_tva, total_bill_value)
    except ValueError as verr:
        raise ValueError(f"Invalid data: {str(verr)}") from verr
    except TypeError as terr:
        raise TypeError(f"Invalid index_value: {str(terr)}") from terr

def generate_bill_input() -> tuple:
    """
    Prompts the user to enter the bill year and month for generating a PDF bill.

    Returns:
        Tuple: A tuple containing the bill year and bill month.

    Raises:
        ValueError: If the provided bill year or bill month is not a valid integer.
        ValueError: If the provided bill month is out of range (not between 1 and 12).
    """
    try:
        current_year = date.today().year
        bill_year = input("Introdu anul pentru care vrei sa generezi factura PDF: ")
        if not bill_year.isdigit() or not 2020 <= int(bill_year) <= current_year:
            raise ValueError(f"An invalid! Introdu o valoare intre 2020 si {current_year}!")
        bill_month = input("Introdu numarul lunii pentru care vrei sa generezi factura PDF: ")
        if not bill_month.isdigit() or not 1 <= int(bill_month) <= 12:
            raise ValueError("Luna invalida! Introdu o valoare intre 1 si 12!")
        return int(bill_year), int(bill_month)
    except ValueError as verr:
        print(LINE_SEPARATOR)
        print(verr)

def update_index_input(cursor: sqlite3.Cursor):
    """
    Prompts the admin to enter the client username and new index value for 
    consumption calculation.

    Args:
        connection (sqlite3.Connection): A connection object.
        cursor (sqlite3.Cursor): The database cursor object.

    Raises:
        LookupError: If there is no user with the specified username.
        ValueError: If the index is not numeric or returns negative consumption.
        KeyboardInterrupt: If the user does not confirm the new index value.
        sqlite3.Error: If there is a communication issue with the database.
    """
    try:
        username = search_user(cursor)
        cursor.execute("""SELECT index_value, bill_month, bill_year
                       FROM bills WHERE username = ? 
                       ORDER BY bill_id DESC LIMIT 1""", (username,))
        result = cursor.fetchone()
        if result is None:
            raise LookupError(
                f"Nu s-a gasit niciun client cu username-ul '{username}'!")
        old_index, index_month, index_year = result
        ro_month = get_romanian_month_name(index_month)
        print(LINE_SEPARATOR)
        print(f"Poti modifica indexul lunii {ro_month} {index_year}!")
        print(f"Indexul existent este {old_index}!")
        while True:
            print(LINE_SEPARATOR)
            new_index = input("Introdu noul index: ")
            if not new_index.isdigit():
                raise ValueError("Indexul este o valoare numerica!")
            new_index = float(new_index)
            consumption = calculate_monthly_consumption(
                cursor, username, index_year, index_month, new_index)
            if consumption < 0:
                raise ValueError("Consumul nu poate fi negativ!")
            print(f"Conform acestui index, consumul pentru luna "
                  f"{ro_month} {index_year} va fi de "
                  f"{consumption} kWh.")
            confirmation = input("Doresti sa continui cu acest index? (y/n) ")
            if confirmation.lower() == "y":
                print(f"Indexul a fost modificat de la {old_index} la {new_index}.")
                return username, index_year, index_month, new_index
            if confirmation.lower() == "n":
                raise KeyboardInterrupt("Operatie anulata!")
            print("""Alegere invalida! Alege 'y' sau 'n'.""")
            print(LINE_SEPARATOR)
    except LookupError as lerr:
        print(str(lerr))
    except sqlite3.Error as sqerr:
        raise RuntimeError("An error occurred while accessing the database.") from sqerr

def update_index(connection: sqlite3.Connection, cursor: sqlite3.Cursor):
    """
    Updates the index value and recalculates the corresponding consumption values

    Args:
        connection (sqlite3.Connection): A connection object.
        cursor (sqlite3.Cursor): The database cursor object.

    Raises:
        ValueError: If there is an error in the input or calculations.
        sqlite3.Error: If there is a communication issue with the database.
    """
    try:
        username, index_year, index_month, new_index = update_index_input(cursor)
        energ_cons_cant, acciza_cant, certif_cant, oug_cant = (
            calculate_cons(cursor, username, index_year, index_month, new_index))
        energie_consumata, acciza_necomerciala, certificate_verzi, oug_27 = (
            PRICE_PER_UNIT.values())
        (energ_cons_val, energ_cons_tva, acciza_val, acciza_tva, certif_val,
         certif_tva, oug_val, oug_tva, total_fara_tva, total_tva,
         total_bill_value) = calculate_prices(
            cursor, username, index_year, index_month, new_index)
        cursor.execute(
            """ UPDATE bills SET index_value = ?, energ_cons_cant = ?,
            energ_cons_pret = ?, energ_cons_val = ?, energ_cons_tva = ?,
            acciza_cant = ?, acciza_pret = ?, acciza_val = ?,acciza_tva = ?,
            certif_cant = ?, certif_pret = ?, certif_val = ?, certif_tva = ?,
            oug_cant = ?, oug_pret = ?, oug_val = ?, oug_tva = ?,
            total_fara_tva = ?, total_tva = ?, total_bill_value = ?
            WHERE username = ? AND bill_year = ? AND bill_month = ?""",
            (new_index, energ_cons_cant, energie_consumata, energ_cons_val,
             energ_cons_tva, acciza_cant, acciza_necomerciala, acciza_val,
             acciza_tva, certif_cant, certificate_verzi, certif_val,
             certif_tva, oug_cant, oug_27, oug_val, oug_tva, total_fara_tva,
             total_tva, total_bill_value, username, index_year, index_month))
        connection.commit()
    except ValueError as verr:
        raise ValueError(f"Eroare: {verr}") from verr
    except LookupError as lerr:
        print(str(lerr))
    except sqlite3.Error as sqerr:
        raise RuntimeError("Eroare la accesarea bazei de date!") from sqerr

def get_index_input(cursor: sqlite3.Cursor, username: str) -> tuple:
    """
    Prompts the user to enter necessary info for consumption calculation.

    Args:
        cursor (sqlite3.Cursor): The database cursor object.
        username (str): The username of the user.

    Returns:
        Tuple: A tuple containing the bill year, bill month, and index value.

    Raises:
        ValueError: If the provided bill year, month or index value are not valid.
    """
    try:
        current_year = date.today().year
        bill_year = int(input("Introdu anul pentru care vrei sa adaugi indexul: "))
        if not 2020 <= bill_year <= current_year:
            raise ValueError(f"An invalid! Introdu o valoare intre 2020 si {current_year}!")
        bill_month = int(input("Introdu luna pentru care vrei sa adaugi indexul: "))
        if not 1 <= bill_month <= 12:
            raise ValueError("Luna invalida! Introdu o valoare intre 1 si 12!")
        while True:
            ro_month = get_romanian_month_name(bill_month)
            index_value = input(f"Introdu indexul pentru luna {ro_month} {bill_year}: ")
            if not index_value.isdigit():
                raise ValueError("Indexul este o valoare numerica!")
            index_value = float(index_value)
            consumption = calculate_monthly_consumption(
                cursor, username, bill_year, bill_month, index_value)
            if consumption < 0:
                raise ValueError("Consumul nu poate fi negativ!")
            print(f"Conform acestui index, consumul pentru luna "
                  f"{ro_month} {bill_year} va fi de "
                  f"{consumption} kWh.")
            confirmation = input("Doresti sa continui cu acest index? (y/n) ")
            if confirmation.lower() == "y":
                break
            if confirmation.lower() == "n":
                raise KeyboardInterrupt("Operatie anulata!")
            print("""Alegere invalida! Alege 'y' sau 'n'.""")
        return bill_year, bill_month, index_value
    except ValueError as verr:
        print(verr)

def provide_index(
    connection: sqlite3.Connection, cursor: sqlite3.Cursor, username: str,
    bill_year: int, bill_month: int, index_value: float, ):
    """
    Insert a new index value and calculate the corresponding bill details into
    the database.

    Args:
        connection (sqlite3.Connection): The SQLite database connection.
        cursor (sqlite3.Cursor): The SQLite cursor.
        username (str): The username associated with the index value and bill.
        bill_year (int): The year of the bill.
        bill_month (int): The month of the bill.
        index_value (float): The new index value.

    Raises:
        sqlite3.Error: If there is an error executing the SQL statement.
    """
    try:
        bill_user_id = get_client_info(username, cursor)["id"]
        bill_user_username = get_client_info(username, cursor)["username"]
        bill_start_date, bill_end_date, bill_generated_date, bill_due_date = (
            calculate_bill_period(bill_year, bill_month))
        bill_no_date = bill_generated_date.strftime('%d%m%y')
        bill_no_id = str(get_client_info(username, cursor)['id']).zfill(6)
        bill_no = f"{bill_no_date}{bill_no_id}"
        bill_serial = RO_COUNTIES_ABBR[get_client_info(username, cursor)["county"]]
        energ_cons_cant, acciza_cant, certif_cant, oug_cant = (
            calculate_cons(cursor, username, bill_year, bill_month, index_value))
        (energ_cons_val, energ_cons_tva, acciza_val, acciza_tva, certif_val,
         certif_tva, oug_val, oug_tva, total_fara_tva, total_tva,
         total_bill_value) = calculate_prices(
             cursor, username, bill_year, bill_month, index_value)
        energie_consumata, acciza_necomerciala, certificate_verzi, oug_27 = (
            PRICE_PER_UNIT.values())
        ro_bill_month = get_romanian_month_name(bill_month)

        cursor.execute("""INSERT INTO bills (
            user_id, username, bill_year, bill_month, bill_generated_date,
            bill_serial, bill_number, bill_due_date, bill_start_date,
            bill_end_date, index_value, energ_cons_cant, energ_cons_pret,
            energ_cons_val, energ_cons_tva, acciza_cant, acciza_pret,
            acciza_val, acciza_tva, certif_cant, certif_pret, certif_val,
            certif_tva, oug_cant, oug_pret, oug_val, oug_tva,
            total_fara_tva, total_tva, total_bill_value)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (bill_user_id, bill_user_username, bill_year, bill_month,
             bill_generated_date, bill_serial, bill_no, bill_due_date,
             bill_start_date, bill_end_date, index_value, energ_cons_cant,
             energie_consumata, energ_cons_val, energ_cons_tva, acciza_cant,
             acciza_necomerciala, acciza_val, acciza_tva, certif_cant,
             certificate_verzi, certif_val, certif_tva, oug_cant, oug_27,
             oug_val, oug_tva, total_fara_tva, total_tva, total_bill_value))
        connection.commit()
        print(LINE_SEPARATOR)
        print(f"Consumul pentru luna {ro_bill_month} {bill_year}"
              f"a fost inregistrat cu succes!")
    except ValueError as verr:
        raise ValueError(f"Eroare: {verr}") from verr
    except sqlite3.Error as sqerr:
        raise sqlite3.Error(f"Eroare: Consumul a fost inregistrat deja pentru "
                            f"luna {ro_bill_month} {bill_year}") from sqerr

def generate_excel_input() -> int:
    """
    Prompts the user to enter the bill year for generating an Excel export.

    Returns:
        int: The bill year entered by the user.

    Raises:
        ValueError: If the provided bill year is not integer or is out of range.
    """
    try:
        bill_year = int(input(
            "Introdu anul pentru care vrei sa generezi exportul excel: "))
        current_year = date.today().year
        if not 2020 <= int(bill_year) <= current_year:
            raise ValueError()
        return int(bill_year)
    except ValueError as verr:
        raise ValueError(f"An invalid! Introdu o valoare intre 2020 si "
                         f"{current_year}!") from verr

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
    excel_name = f"export_consum_{username}-{bill_year}.xlsx"
    excel_folder = MAIN_FOLDER_ROOT / "Exporturi excel" / bill_serial
    try:
        if not os.path.exists(excel_folder):
            os.makedirs(excel_folder)
    except OSError as oserr:
        print(LINE_SEPARATOR)
        error_msg = f"Eroare la crearea folderului {str(excel_folder)}!"
        raise OSError(error_msg) from oserr
    return str(excel_folder / excel_name)

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
                       acciza_val, acciza_tva, certif_cant, certif_pret,
                       certif_val, certif_tva, oug_cant, oug_pret, oug_val,
                       oug_tva, total_fara_tva, total_tva, total_bill_value
                       FROM bills WHERE username = ? AND bill_year = ?
                       ORDER BY bill_month ASC""", (username, bill_year))
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        data_frame = pd.DataFrame(rows, columns=columns)

        bill_serial = RO_COUNTIES_ABBR[get_client_info(username, cursor)["county"]]
        excel_name = set_excel_name(username, bill_year, bill_serial)
        try:
            if not os.path.exists(os.path.dirname(excel_name)):
                os.makedirs(os.path.dirname(excel_name))
            data_frame.to_excel(excel_name, index=False)
            subprocess.Popen(["start", "", excel_name], shell=True)
        except OSError as oserr:
            error_msg = f"Eroare la crearea fisierului {str(excel_name)}!"
            raise OSError(error_msg) from oserr
    except sqlite3.Error as sqerr:
        print(LINE_SEPARATOR)
        print(f"Eroare la conectarea la baza de date: {sqerr}")
    print(LINE_SEPARATOR)
    print(f"Exportul excel pentru anul {bill_year} a fost generat cu succes!")
