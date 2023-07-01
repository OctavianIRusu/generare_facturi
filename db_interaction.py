"""
This module contains functions for creating entries in SQLite database, which
contains an user table and a bills table. All the functions allow the 
interaction between user and database, in order to input values and extract 
informations for pdf or excel exports, and to monitor the energy consumption
per month for each user.

The module provides the following functions:

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

For more information, refer to the README file.
"""
import calendar
import csv
import logging
import os
import sqlite3
import subprocess
from datetime import date
from pathlib import Path

import pandas as pd
from dateutil.relativedelta import relativedelta

# setting up logging configurations and handlers
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

file_handler = logging.FileHandler('logs/db_interaction.log')
file_handler.setLevel(logging.ERROR)
file_handler.setFormatter(log_formatter)

logger.addHandler(file_handler)

# Set the visual separator for console printing
LINE_SEPARATOR = "-" * 80

# Set the root folder path and Romanian localities path
MAIN_FOLDER_ROOT = Path(__file__).parent
LOCALITY_LIST_FILE = MAIN_FOLDER_ROOT / "resources" / "lista_localitati.csv"

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

# Dictionary that stores the prices and current TVA value
PRICE_PER_UNIT = {
    "energie_consumata": 1.40182, "acciza_necomerciala": 6.05,
    "certificate_verzi": 71.68059, "oug_27": 0.90812
}
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
        tuple: A tuple containing two boolean values: authentication status
            and admin status.

    Raises:
        sqlite3.Error: If there is an error while executing the SQL statement.
    """
    try:
        logger.info("Checking user credentials in the database")
        cursor.execute("""SELECT role FROM users
                    WHERE username = ? AND password = ?""",
                       (username, password))
        result = cursor.fetchone()
        if result:
            role = result[0]
            if role == 'admin':
                logger.info("User '%s' successfully authenticated as 'admin'",
                            username)
                return True, True
            logger.info("User '%s' successfully authenticated", username)
            return True, False
        logger.warning("Authentication failed for user '%s'", username)
        return False, False
    except sqlite3.Error as sqerr:
        logger.exception(
            "An error occurred while executing the SQL statement")
        raise sqerr

def validate_new_user_county(file_path: str) -> str:
    """
    Checks if a location exists in the specified CSV file.

    Args:
        file_path (str): The path to the CSV file.

    Returns:
        str: The county name.

    Raises:
        FileNotFoundError: If the specified file does not exist.
        ValueError: If the searched value does not exist.
    """
    while True:
        county = input("Introdu judetul: ")
        logger.info("Checking if county '%s' exists in file '%s'",
                    county, file_path)
        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            for row in reader:
                if county.lower() in row[1].lower():
                    logger.info("Location '%s' found in file '%s'",
                                county, file_path)
                    return county
        logger.info("Location '%s' not found in file '%s'", county, file_path)
        print("Judetul specificat nu exista!")

def validate_new_user_locality(county: str, file_path: str) -> str:
    """
    Checks if a locality belongs to a specified county.

    Args:
        county (str): The county specified.
        file_path (str): The path to the CSV file.

    Returns:
        str: The locality name

    Raises:
        FileNotFoundError: If the specified file does not exist.
        ValueError: If the searched value does not exist.
    """
    while True:
        locality = input("Introdu localitatea: ")
        logger.info(
            "Checking if locality '%s' exists in county '%s'", locality, county)
        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            for row in reader:
                if (row[0].lower() == locality.lower() and
                    row[1].lower() == county.lower()):
                    logger.info("Locality '%s' belongs to county '%s'",
                                locality, county)
                    return locality
        logger.info("Locality '%s' does not belong to county '%s' in file '%s'",
                    locality, county, file_path)
        print(f"Localitatea specificata nu apartine de judetul {county}!")

def get_new_user_zipcode(locality, county, file_path) -> str:
    """
    Returns the ZIP code for a given locality in a given county from a CSV file.

    Args:
        locality (str): The name of the locality.
        county (str): The name of the county.
        file_path (str): The path to the CSV file.

    Returns:
        str: The ZIP code for the specified locality, or None if not found.

    Raises:
        FileNotFoundError: If the specified file does not exist.
        ValueError: If the searched value does not exist.    
    """
    logger.info("Retrieving ZIP code for locality '%s'", locality)
    with open(file_path, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        for row in reader:
            if (row[0].lower() == locality.lower() and
                row[1].lower() == county.lower()):
                logger.info("ZIP code '%s' retrieved for locality '%s'",
                            row[3], locality)
                return row[3]
    logger.error("No ZIP code found for locality '%s'", locality)
    print("Codul postal nu a putut fi atribuit!")

def validate_new_user_name():
    """
    Prompt the user to enter their first name and last name, and return the 
    formatted full name.

    Returns:
        str: The formatted full name entered by the user.
    """
    while True:
        name = input("Introdu prenume si nume: ").strip()
        logger.info("Prompted user to enter first and last name: %s", name)
        name_parts = name.split()
        if 2 <= len(name_parts) <= 3:
            formatted_name = ' '.join([part.capitalize()
                                      for part in name_parts])
            logger.info("Formatted full name: %s", formatted_name)
            return formatted_name
        logger.info("Invalid name entered: %s", name)
        print(LINE_SEPARATOR)
        print("Numele trebuie sa contina unul sau doua prenume si un nume!")

def validate_new_user_role():
    """
    Prompts the user to choose a user role (user/admin) and validates the input.

    Returns:
        str: The chosen user role.
    """
    while True:
        role = input("Alege tip user (user/admin): ")
        logger.info("Prompted user to choose a user role: %s", role)
        if role.lower() in ["user", "admin"]:
            logger.info("Valid user role chosen: %s", role)
            return role
        logger.info("Invalid user role entered: %s", role)
        print("Rolul ales poate fi doar 'user' sau 'admin!'")

def add_new_user(connection: sqlite3.Connection, cursor: sqlite3.Cursor):
    """
    Adds a new user to the database based on the provided information.

    Args:
        connection (sqlite3.Connection): A connection object.
        cursor (sqlite3.Cursor): A cursor object for executing SQL statements.

    Raises:
        sqlite3.Error: If an error occurs when SQL statement is executed.
    """
    try:
        logger.info("Starting to add a new user")
        formatted_name = validate_new_user_name()
        county = validate_new_user_county(LOCALITY_LIST_FILE)
        locality = validate_new_user_locality(county, LOCALITY_LIST_FILE)
        street = input("Introdu adresa (strada, nr, bloc, apartament): ")
        zipcode = get_new_user_zipcode(locality, county, LOCALITY_LIST_FILE)
        username = "".join([s.lower() for s in formatted_name.split()])
        password = username
        role = validate_new_user_role()

        logger.info("Executing SQL statement to add new user to the database")
        cursor.execute(
            '''INSERT INTO users
            (name, street, zipcode, city, county, username, password, role)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
            (formatted_name, street, zipcode, locality, county, username,
             password, role))
        connection.commit()
        print(LINE_SEPARATOR)
        print("Noul client a fost adaugat cu succes!")
        print(f"Date autentificare: username: {username}, parola: {password}.")
        logger.info("New user added successfully")
    except sqlite3.Error as sqerr:
        logger.exception(
            "Error occurred while accessing the database: %s", sqerr)
        print(f"Eroare la accesarea bazei de date: {sqerr}")
    except FileNotFoundError as fnferr:
        logger.exception(
            "Error occurred while accessing the locality list: %s", fnferr)
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
        logger.info("Searching for a user.")
        username = str(input("Introdu username-ul clientului: ")).lower()
        logger.info('Username entered: %s', username)
        cursor.execute('''SELECT COUNT(*) FROM users
                    WHERE username = ?''', (username,))
        result = cursor.fetchone()
        if result[0] == 0:
            logger.error("No client with this username: %s", username)
            print(f'Nu exista niciun client "{username}"!')
        else:
            logger.info("User found.")
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
        logger.info("Starting user address modification.")
        username = search_user(cursor)
        county = validate_new_user_county(LOCALITY_LIST_FILE)
        locality = validate_new_user_locality(county, LOCALITY_LIST_FILE)
        street = input("Introdu adresa (strada, nr, bloc, apartament): ")
        zipcode = get_new_user_zipcode(locality, county, LOCALITY_LIST_FILE)
        cursor.execute('''UPDATE users SET street = ?, zipcode = ?,
                       city = ?, county = ?
                       WHERE username = ?''',
                       (street, zipcode, locality, county, username))
        connection.commit()
        logger.info("User address updated successfully.")
        print(LINE_SEPARATOR)
        print("Informatiile au fost actualizate cu succes!")
    except LookupError as lerr:
        logger.exception("LookupError occurred: %s", str(lerr))
        print(lerr)
    except sqlite3.Error as sqerr:
        logger.exception("sqlite3.Error occurred: %s", str(sqerr))
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
    while True:
        print(LINE_SEPARATOR)
        username = search_user(cursor)
        logger.info("User selected for deletion: %s", username)
        while True:
            confirmation = input(
                f"Esti sigur ca doresti sa stergi user-ul {username}? y/n ")
            logger.info("Confirmation input: %s", confirmation)
            if confirmation.lower() == "n":
                logger.info("Deletion canceled.")
                break
            elif confirmation.lower() == "y":
                cursor.execute('''DELETE FROM users
                            WHERE username = ?''',
                                (username,))
                print(LINE_SEPARATOR)
                print("Clientul a fost sters cu succes!")
                connection.commit()
                connection.close()
                break
            print(LINE_SEPARATOR)
            print("""Alegere invalida! Alege 'y' sau 'n'.""")
        if confirmation.lower() == "y":
            break
    logger.info("Deletion process completed.")

def get_client_info(username: str, cursor: sqlite3.Cursor) -> dict:
    """
    Get client information from the database based on the provided username.

    Args:
        username (str): The username of the client.
        cursor (sqlite3.Cursor): A cursor object for executing SQL statements.

    Returns:
        dict: A dictionary containing the client information.

    Raises:
        sqlite3.Error: If there is an error during the execution of the SQL.
        TypeError: If there is no valid data extracted from database.
    """
    try:
        logger.info("Getting client information for username: %s", username)
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        try:
            columns = [desc[0] for desc in cursor.description]
            user_dict = dict(zip(columns, row))
            logger.info("Client info retrieved for username: %s", username)
            return user_dict
        except TypeError as terr:
            logger.exception("No client found with username: %s", username)
            raise terr
    except sqlite3.Error as sqerr:
        logger.exception("SQLite error occurred: %s", str(sqerr))
        raise sqerr

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
    logger.info("Getting bill info for username: %s, year: %s, month: %s",
                username, bill_year, bill_month)
    try:
        cursor.execute("""SELECT * FROM bills
                       WHERE username = ? AND bill_year = ?
                       AND bill_month = ?""",
                       (username, bill_year, bill_month))
        row = cursor.fetchone()
        try:
            columns = [desc[0] for desc in cursor.description]
            bill_info_dict = dict(zip(columns, row))
            logger.info("Bill info retrieved for user: %s, year: %s, month: %s",
                        username, bill_year, bill_month)
            return bill_info_dict
        except TypeError as terr:
            month_name = get_romanian_month_name(bill_month)
            logger.error("No bill found for username: %s, year: %s, month: %s",
                         username, bill_year, bill_month)
            raise TypeError(f"Nu exista nicio factura pentru luna "
                            f"{month_name} {bill_year}!") from terr
    except sqlite3.Error as sqerr:
        logger.error("SQLite error occurred: %s", str(sqerr))
        raise sqerr

def create_consumption_table(
        username: str, bill_year: int, bill_month: int,
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

    Raises:
        sqlite3.Error: If there is an error during the execution of the SQL.
    """
    try:
        logger.info("""Creating consumption table for user: 
                    %s, year: %s, month: %s""",
                    username, bill_year, bill_month)
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
        logger.info("""Consumption table created for user: 
                    %s, year: %s, month: %s""",
                    username, bill_year, bill_month)
        return CONSUMPTION_TABLE_CONTENT
    except sqlite3.Error as sqerr:
        print(f"Eroare la conectarea la baza de date: {sqerr}")
        logger.exception("""SQLite error occurred while creating consumption
                         table: %s""", str(sqerr))
        raise sqerr
    except (ValueError, KeyError, TypeError) as err:
        print(f"Eroare la obtinerea detaliilor de consum (tabel): {err}")
        logger.exception("""Error occurred while obtaining consumption
                         details: %s""", str(err))
        raise err

def get_romanian_month_name(bill_month: int) -> str:
    """
    Returns the Romanian name of a given month.

    Args:
        bill_month (int): The month for which to retrieve the Romanian name.

    Returns:
        str: The Romanian name of the month.

    Raises:
        ValueError: If the provided month is out of range.
    """
    logger.info("Retrieving Romanian month name for month: %s", bill_month)
    romanian_month_names = [
        "Ianuarie", "Februarie", "Martie", "Aprilie", "Mai", "Iunie", "Iulie",
        "August", "Septembrie", "Octombrie", "Noiembrie", "Decembrie"]
    try:
        romanian_month_name = romanian_month_names[bill_month - 1]
        logger.info("Romanian month name retrieved: %s", romanian_month_name)
        return romanian_month_name
    except IndexError as ierr:
        logger.exception(ierr)
        raise IndexError("Month must be between 1 and 12.") from ierr

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
    logger.info("""Calculating monthly consumption for username: 
                %s, year: %s, month: %s, index value: %s""",
                username, bill_year, bill_month, index_value)
    sql_statement = """SELECT index_value FROM bills
                    WHERE username = ? AND bill_year = ? AND bill_month = ?
                    ORDER BY bill_year DESC, bill_month DESC LIMIT 1"""
    try:
        if bill_month == 1:
            cursor.execute(sql_statement, (username, bill_year - 1, 12))
        else:
            cursor.execute(sql_statement, (username, bill_year, bill_month - 1))
        previous_entry = cursor.fetchone()
        if previous_entry:
            previous_index = previous_entry[0]
            monthly_consumption = index_value - previous_index
        else:
            monthly_consumption = index_value
        logger.info("Monthly consumption calculated: %s", monthly_consumption)
        return monthly_consumption
    except sqlite3.Error as sqerr:
        print(f"SQLite error occurred while opening database: {sqerr}")
        logger.error("SQLite error occurred while opening database: %s", sqerr)
        raise sqerr
    except ValueError as verr:
        logger.error("Invalid bill month or year: %s", str(verr))
        raise ValueError(f"An sau luna invalida: {verr}") from verr

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
    logger.info("Calculating bill period for year: %s, month: %s",
                bill_year, bill_month)
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
        logger.info("""Bill period calculated: Start Date: 
                    %s, End Date: %s, Generated Date: %s, Due Date: %s""",
                    bill_start_date, bill_end_date, bill_generated_date,
                    bill_due_date)
        return (bill_start_date, bill_end_date, 
                bill_generated_date, bill_due_date)
    except ValueError as verr:
        logger.error("Invalid bill month or year: %s", str(verr))
        raise ValueError(f"An sau luna invalida: {verr}") from verr

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
        tuple: A tuple containing the calculated consumption values.

    Raises:
        ValueError: If the provided username, bill month, bill year is invalid.
    """
    logger.info("""Calculating consumption values for username: 
                %s, bill_year: %s, bill_month: %s""",
                username, bill_year, bill_month)
    try:
        energ_cons_cant = calculate_monthly_consumption(
            cursor, username, bill_year, bill_month, index_value)
        acciza_cant = calculate_monthly_consumption(
            cursor, username, bill_year, bill_month, index_value) / 1000
        certif_cant = acciza_cant
        oug_cant = - calculate_monthly_consumption(
            cursor, username, bill_year, bill_month, index_value)
        logger.info("""Consumption values calculated: 
                    Energy: %s, Acciza: %s, Certif: %s, OUG: %s""",
                    energ_cons_cant, acciza_cant, certif_cant, oug_cant)
        return energ_cons_cant, acciza_cant, certif_cant, oug_cant
    except ValueError as verr:
        logger.error("Invalid data: %s", str(verr))
        raise ValueError(f"Date invalide la calculul consumului: {verr}") from verr

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
    logger.info("""Calculating prices for username: 
                %s, bill_year: %s, bill_month: %s""",
                username, bill_year, bill_month)
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

        logger.info("""Prices calculated: Energy Consumption Value: %s, 
                    Energy Consumption VAT: %s, Acciza Value: %s, 
                    Acciza VAT: %s, Certif Value: %s, Certif VAT: %s, 
                    OUG Value: %s, OUG VAT: %s, Total (Excluding VAT): %s, 
                    Total VAT: %s, Total Bill Value: %s""",
                    energ_cons_val, energ_cons_tva, acciza_val, acciza_tva,
                    certif_val, certif_tva, oug_val, oug_tva, total_fara_tva,
                    total_tva, total_bill_value)

        return (energ_cons_val, energ_cons_tva, acciza_val, acciza_tva,
                certif_val, certif_tva, oug_val, oug_tva, total_fara_tva,
                total_tva, total_bill_value)
    except ValueError as verr:
        logger.error("Invalid data: %s", verr)
        raise ValueError(f"Invalid data: {str(verr)}") from verr
    except TypeError as terr:
        logger.error("Invalid index_value: %s", terr)
        raise TypeError(f"Invalid index_value: {str(terr)}") from terr

def generate_bill_input(cursor: sqlite3.Cursor, username: str) -> tuple:
    """
    Prompts the user to enter the bill year and month for generating a PDF bill.

    Args:
        cursor (sqlite3.Cursor): The database cursor object.
        username (str): The username of the user.

    Returns:
        Tuple: A tuple containing the bill year and bill month.

    Raises:
        ValueError: If the provided bill year or bill month is not a valid 
            integer or out of range.
    """
    logger.info("Generating bill input for username: %s", username)
    try:
        cursor.execute("""SELECT bill_month, bill_year FROM bills
                       WHERE username = ?
                       ORDER BY bill_id ASC""", (username,))
        row = cursor.fetchall()
        if not row:
            raise ValueError(
                "Nu există facturi înregistrate în baza de date!")
        first_bill_month, first_bill_year = row[0]
        last_bill_month, last_bill_year = row[-1]
        ro_fbm = get_romanian_month_name(first_bill_month)
        ro_lbm = get_romanian_month_name(last_bill_month)
        years_set = {tuplu[1] for tuplu in row}
        if len(years_set) > 1:
            years_set_unpack = (", ".join(str(bill_year) for
                                bill_year in years_set))
        else:
            years_set_unpack = str(next(iter(years_set)))
        print(LINE_SEPARATOR)
        print(f"Poti genera facturi pentru perioada: {ro_fbm} {first_bill_year}"
              f" - {ro_lbm} {last_bill_year}")
        logger.info("Available bill period: %s %s - %s %s",
                    ro_fbm, first_bill_year, ro_lbm, last_bill_year)
        while True:
            try:
                print(LINE_SEPARATOR)
                bill_year = input(
                    "Introdu anul pentru care vrei sa generezi factura: ")
                if not bill_year.isdigit() or int(bill_year) not in years_set:
                    raise ValueError(
                        f"An invalid! Valori posibile: {years_set_unpack}.")
                break
            except ValueError as verr:
                logger.exception("Invalid bill year: %s", verr)
                print(verr)
        while True:
            try:
                months_set = ({month for month, year in row 
                              if year == int(bill_year)})
                if len(months_set) > 1:
                    months_set_unpack = (", ".join(str(month_year) for
                                         month_year in months_set))
                else:
                    months_set_unpack = str(next(iter(months_set)))
                print(LINE_SEPARATOR)
                bill_month = input("Introdu numarul lunii pentru care vrei sa "
                                   "generezi factura PDF: ")
                if (not bill_month.isdigit() or 
                    (int(bill_month), int(bill_year)) not in row):
                    raise ValueError(
                        f"Luna invalida! Valori posibile: {months_set_unpack}")
                break
            except ValueError as verr:
                logger.exception("Invalid bill month: %s", verr)
                print(verr)
        return int(bill_year), int(bill_month)
    except ValueError as verr:
        print(LINE_SEPARATOR)
        print(verr)
    except sqlite3.Error as sqerr:
        print(f"Eroare la conectarea la baza de date: {sqerr}")

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
        sqlite3.Error: If there is an error when executing the SQL statement.
    """
    logger.info("Updating index input")
    try:
        username = search_user(cursor)
        cursor.execute("""SELECT index_value, bill_month, bill_year
                       FROM bills WHERE username = ? 
                       ORDER BY bill_id DESC LIMIT 1""", (username,))
        result = cursor.fetchone()
        if result is None:
            logger.exception("No consumption records for client: '%s'", username)
            raise LookupError(
                f"Nu exista inregistrari de consum pentru '{username}'!")
        old_index, index_month, index_year = result
        ro_month = get_romanian_month_name(index_month)
        logger.info("Old index value: %s, Index month: %s, Index year: %s",
                    old_index, index_month, index_year)
        print(LINE_SEPARATOR)
        print(f"Poti modifica indexul lunii {ro_month} {index_year}!")
        print(f"Indexul existent este {old_index}!")
        while True:
            try:
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

                while True:
                    confirmation = input(
                        "Doresti sa continui cu acest index? (y/n) ")
                    if confirmation.lower() == "y":
                        logger.info("""Updated index input: Username: %s, 
                                    Index Year: %s, Index Month: %s, 
                                    New Index: %s""",
                                username, index_year, index_month, new_index)
                        print(f"Indexul a fost modificat de la {old_index} "
                              f"la {new_index}.")
                        break
                    elif confirmation.lower() == "n":
                        break
                    else:
                        print(LINE_SEPARATOR)
                        print("""Alegere invalida! Alege 'y' sau 'n'.""")
                if confirmation.lower() == "y":
                    return username, index_year, index_month, new_index
                if confirmation.lower() == "n":
                    continue
            except ValueError as verr:
                logger.exception("Invalid index value: %s", verr)
                print(LINE_SEPARATOR)
                print(verr)
    except LookupError as lerr:
        print(LINE_SEPARATOR)
        logger.exception("LookupError occurred: %s", lerr)
        print(lerr)
    except sqlite3.Error as sqerr:
        print(LINE_SEPARATOR)
        logger.exception("""SQLite error occurred while accessing 
                         the database: %s""", sqerr)
        print(sqerr)

def update_index(connection: sqlite3.Connection, cursor: sqlite3.Cursor):
    """
    Updates the index value and recalculates the corresponding consumption values

    Args:
        connection (sqlite3.Connection): A connection object.
        cursor (sqlite3.Cursor): The database cursor object.

    Raises:
        ValueError: If there is an error in the input or calculations.
        sqlite3.Error: If there is an error when executing the SQL statement.
    """
    logger.info("Updating index")
    try:
        username, index_year, index_month, new_index = update_index_input(
            cursor)
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
        logger.info("Index updated successfully")
    except ValueError as verr:
        logger.exception("ValueError occurred: %s", verr)
        raise ValueError(f"Eroare: {verr}") from verr
    except LookupError as lerr:
        logger.exception("LookupError occurred: %s", lerr)
        print(str(lerr))
    except sqlite3.Error as sqerr:
        logger.exception("""SQLite error occurred while accessing 
                         the database: %s""", sqerr)
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
    logger.info("Getting index input for user: %s", username)
    try:
        cursor.execute("""SELECT bill_month, bill_year, index_value FROM bills
                       WHERE username = ?
                       ORDER BY bill_id DESC""", (username,))
        row = cursor.fetchone()
        if row:
            last_bill_month, last_bill_year, last_bill_index = row
            ro_last_bill_month = get_romanian_month_name(last_bill_month)
            if last_bill_month == 12:
                current_bill_month = 1
                current_bill_year = last_bill_year + 1
                print(f"Ultima luna pentru care s-a inregistrat consumul: "
                      f"{ro_last_bill_month} {last_bill_year}")
                print(f"Ultimul index inregistrat: {last_bill_index} kWh")
                logger.info("Last recorded consumption month: %s %s",
                            ro_last_bill_month, last_bill_year)
                logger.info("Last recorded index: %s kWh", last_bill_index)
            else:
                current_bill_month = last_bill_month + 1
                current_bill_year = last_bill_year
                print(f"Ultima luna pentru care s-a inregistrat consumul: "
                      f"{ro_last_bill_month} {last_bill_year}")
                print(f"Ultimul index inregistrat: {last_bill_index} kWh")
                logger.info("Last recorded consumption month: %s %s",
                            ro_last_bill_month, last_bill_year)
                logger.info("Last recorded index: %s kWh", last_bill_index)
        else:
            current_bill_month = 1
            current_bill_year = 2020
            print("Nu exista inregistrari anterioare ale consumului!")
            logger.info("No previous consumption records found")
        ro_current_bill_month = get_romanian_month_name(current_bill_month)
        while True:
            try:
                print(LINE_SEPARATOR)
                index_value = input(f"Introdu indexul pentru luna "
                                    f"{ro_current_bill_month} "
                                    f"{current_bill_year}: ")
                if not index_value.isdigit():
                    raise ValueError(
                        "Indexul trebuie sa fie o valoare numerica!")
                index_value = float(index_value)
                consumption = calculate_monthly_consumption(
                    cursor, username, current_bill_year, current_bill_month,
                    index_value)
                if consumption < 0:
                    raise ValueError("Consumul nu poate fi negativ!")
                print(f"Conform acestui index, consumul pentru luna "
                      f"{ro_current_bill_month} {current_bill_year} va fi de "
                      f"{consumption} kWh.")
                while True:
                    confirmation = input(
                        "Doresti sa continui cu acest index? (y/n) ")
                    if confirmation.lower() == "y":
                        break
                    elif confirmation.lower() == "n":
                        break
                    else:
                        print(LINE_SEPARATOR)
                        print("""Alegere invalida! Alege 'y' sau 'n'.""")
                if confirmation.lower() == "y":
                    break
                if confirmation.lower() == "n":
                    continue
            except ValueError as verr:
                logger.exception("ValueError occurred: %s", verr)
                print(verr)
        logger.info("Index input obtained successfully")
        return current_bill_year, current_bill_month, index_value
    except sqlite3.Error as sqerr:
        logger.exception("""SQLite error occurred while accessing the 
                         database: %s""", sqerr)
        print(LINE_SEPARATOR)
        print(f"Eroare la conectarea la baza de date: {sqerr}")

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
        sqlite3.Error: If there is an error when executing the SQL statement.
    """
    logger.info("Providing index for user: %s, year: %d, month: %d, index: %f",
                username, bill_year, bill_month, index_value)

    try:
        bill_user_id = get_client_info(username, cursor)["id"]
        bill_user_username = get_client_info(username, cursor)["username"]
        bill_start_date, bill_end_date, bill_generated_date, bill_due_date = (
            calculate_bill_period(bill_year, bill_month))
        bill_no_date = bill_generated_date.strftime('%d%m%y')
        bill_no_id = str(get_client_info(username, cursor)["id"]).zfill(6)
        bill_no = f"{bill_no_date}{bill_no_id}"
        bill_serial = RO_COUNTIES_ABBR[get_client_info(username, cursor)[
            "county"]]
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
        logger.info("Index provided and bill details calculated successfully")
        print(LINE_SEPARATOR)
        print(f"Consumul pentru luna {ro_bill_month} {bill_year} "
              f"a fost inregistrat cu succes!")
    except ValueError as verr:
        logger.exception("ValueError occurred: %s", verr)
        print(verr)
        raise ValueError from verr
    except sqlite3.Error as sqerr:
        logger.error("""SQLite error occurred while accessing the database: 
                     %s""", sqerr)
        print(sqerr)
        raise sqlite3.Error from sqerr

def generate_excel_input(cursor: sqlite3.Cursor, username: str) -> int:
    """
    Prompts the user to enter the bill year for generating an Excel export.

    Args:
        cursor (sqlite3.Cursor): The database cursor object.
        username (str): The username of the user.

    Returns:
        int: The bill year entered by the user.

    Raises:
        ValueError: If the provided bill year is not integer or is out of range.
    """
    logger.info("Generating Excel input for user: %s", username)
    try:
        cursor.execute("""SELECT bill_year FROM bills
                       WHERE username = ?
                       ORDER BY bill_id ASC""", (username,))
        row = cursor.fetchall()
        if not row:
            raise ValueError(
                "Nu există facturi înregistrate în baza de date!")
        if len(row) > 1:
            export_years_set = {tuplu[0] for tuplu in row}
            export_years = ", ".join(str(year) for year in export_years_set)
            print(f"Poti genera exportul pentru anii: {export_years}")
            while True:
                try:
                    print(LINE_SEPARATOR)
                    bill_year = int(input(
                        "Introdu anul pentru care vrei sa generezi exportul excel: "))
                    if bill_year not in export_years_set:
                        raise ValueError(
                            f"An invalid! Valori posibile: {export_years}")
                    break
                except ValueError as verr:
                    logger.exception("ValueError occurred: %s", verr)
                    print(LINE_SEPARATOR)
                    print(verr)
        else:
            export_years = str(next(iter(export_years_set)))
            print(f"Poti genera exportul xlsx pentru anul {export_years}")
            bill_year = int(export_years)
        logger.info("Excel input generated successfully")
        return int(bill_year)
    except sqlite3.Error as sqerr:
        logger.error("""SQLite error occurred while accessing the database: 
                     %s""", sqerr)
        print(f"Eroare la conectarea la baza de date: {sqerr}")
        raise sqlite3.Error from sqerr

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
        OSError: If there is an error creating the directory for export file.
    """
    logger.info("Setting Excel export name for user: %s", username)
    excel_name = f"export_consum_{username}-{bill_year}.xlsx"
    excel_folder = MAIN_FOLDER_ROOT / "Exporturi excel" / bill_serial
    try:
        if not os.path.exists(excel_folder):
            os.makedirs(excel_folder)
    except OSError as oserr:
        logger.exception("OSError occurred while creating the folder: %s",
                         str(excel_folder))
        print(LINE_SEPARATOR)
        error_msg = f"Eroare la crearea folderului {str(excel_folder)}!"
        raise OSError(error_msg) from oserr
    excel_path = str(excel_folder / excel_name)
    logger.info("Excel export name set successfully: %s", excel_path)
    return excel_path

def export_excel_table(cursor: sqlite3.Cursor, username: str):
    """
    Export the bill data for a specific year from database to an Excel file.

    Args:
        cursor (sqlite3.Cursor): The SQLite cursor.
        username (str): The username associated with the bills.

    Raises:
        OSError: If there is an error creating the directory for the file.
    """
    logger.info("Exporting bill data to Excel for user: %s", username)
    try:
        bill_year = generate_excel_input(cursor, username)
        if isinstance(bill_year, int):
            cursor.execute(
                """SELECT username, bill_year, bill_month, bill_serial,
                bill_number, index_value, energ_cons_cant, energ_cons_pret,
                energ_cons_val, energ_cons_tva, acciza_cant, acciza_pret,
                acciza_val, acciza_tva, certif_cant, certif_pret, certif_val,
                certif_tva, oug_cant, oug_pret, oug_val, oug_tva,
                total_fara_tva, total_tva, total_bill_value
                FROM bills WHERE username = ? AND bill_year = ?
                ORDER BY bill_month ASC""", (username, bill_year))
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            data_frame = pd.DataFrame(rows, columns=columns)

            bill_serial = RO_COUNTIES_ABBR[get_client_info(username, cursor)[
                "county"]]
            excel_name = set_excel_name(username, bill_year, bill_serial)
            try:
                if not os.path.exists(os.path.dirname(excel_name)):
                    os.makedirs(os.path.dirname(excel_name))
                data_frame.to_excel(excel_name, index=False)
                subprocess.Popen(["start", "", excel_name], shell=True)
                logger.info("""Excel export for user %s and year %d generated 
                            successfully: %s""", username, bill_year, excel_name)
                print(LINE_SEPARATOR)
                print(
                    f"Exportul pentru anul {bill_year} a fost generat cu succes!")
            except OSError as oserr:
                logger.error("""OSError occurred while creating the Excel 
                             file: %s""", str(excel_name))
                error_msg = f"Eroare la crearea fisierului {str(excel_name)}!"
                raise OSError(error_msg) from oserr
        else:
            logger.error("Invalid bill year entered for user: %s", username)
            raise ValueError("An invalid!")
    except sqlite3.Error as sqerr:
        logger.error("""SQLite error occurred while exporting bill data to 
                     Excel: %s""", str(sqerr))
        print(LINE_SEPARATOR)
        print(f"Eroare la conectarea la baza de date: {sqerr}")
    except ValueError as verr:
        logger.error("""ValueError occurred while exporting bill data to 
                     Excel: %s""", str(verr))
        print(LINE_SEPARATOR)
        print(verr)
