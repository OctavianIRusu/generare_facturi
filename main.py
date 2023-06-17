import sqlite3
import time

from bill_database import (add_new_user, authenticate, close_database,
                           create_consumption_table, export_excel_table,
                           generate_bill_input, generate_excel_input,
                           get_bill_info, get_client_info, get_index_input,
                           open_database, perform_database_operation,
                           provide_new_index)
from generate_bill import generate_pdf_bill, set_pdf_name


def display_user_menu():
    """
    Display the user menu options.
    """
    print("1. Genereaza factura lunara in format PDF")
    print("2. Genereaza export excel cu consumul anual")
    print("3. Adauga index contor energie electrica")
    print("4. Delogare")

def display_admin_menu():
    """
    Display the admin menu options.
    """
    print("1. Adauga un client")
    print("2. Modifica informatiile pentru un client sau un index existent")
    print("3. Modifica un index existent")
    print("4. Sterge un client")
    print("5. Delogare")
           
def handle_user_menu(
            choice: int, username: str, 
            connection: sqlite3.Connection, cursor: sqlite3.Cursor):
    """
    Handle the selected option from the user menu.

    Args:
        choice (int): The selected option from the menu.
        username (str): The username of the user.
        connection: The database connection.
        cursor: The database cursor.

    Raises:
        ValueError: If the user enters an invalid choice.
    """
    try:
        if choice == 1:
            bill_year, bill_month = generate_bill_input()
            bill_serial = get_bill_info(
                username, bill_year, bill_month, cursor)["bill_serial"]
            bill_number = get_bill_info(
                username, bill_year, bill_month, cursor)["bill_number"]
            file_name = set_pdf_name(bill_serial, bill_number)
            client_info = get_client_info(username, cursor)
            bill_info = get_bill_info(username, bill_year, bill_month, cursor)
            bill_details = create_consumption_table(
                username, bill_year, bill_month, cursor)
            generate_pdf_bill(file_name, client_info, bill_info, bill_details)
        elif choice == 2:
            bill_year = generate_excel_input()
            export_excel_table(cursor, username, bill_year)
        elif choice == 3:
            bill_year, bill_month, index_value = (
                get_index_input(cursor, username))
            provide_new_index(
                connection, cursor, username, bill_year, bill_month, index_value)
        elif choice == 4:
            print(f"Ai fost delogat/a! La revedere, {username}!")
            quit()
        else:
            raise ValueError("""Optiune invalida. 
                             Incearca una dintre variantele 1-4.""")
    except ValueError as verr:
        print(str(verr))

def handle_admin_menu(
            choice: int, username: str, 
            connection: sqlite3.Connection, cursor: sqlite3.Cursor):
    """
    Handle the selected option from the admin menu.

    Args:
        choice (int): The selected option from the menu.
        username (str): The username of the admin.
        connection: The database connection.
        cursor: The database cursor.

    Raises:
        ValueError: If the user enters an invalid choice.
    """
    try:
        if choice == 1:
            add_new_user(connection, cursor)
            print("-" * 60)
            time.sleep(1.5)
        elif choice == 2:
            pass
        elif choice == 3:
            pass
        elif choice == 4:
            print("Stergere client din baza de date!")
        elif choice == 5:
            print(f"Ai fost delogat/a! La revedere, {username}!")
            quit()
        else:
            raise ValueError("""Optiune invalida. 
                             Incearca una dintre variantele 1-5.""")
    except ValueError as verr:
        print(str(verr))

def main():
    """
    Main function to run the application.

    Raises:
        ValueError: If the user enters an invalid choice.
    """
    connection = open_database()
    cursor = perform_database_operation(connection)
    
    print("Bine ai venit! Pentru a continua este necesara autentificarea!")
    username = input("Introduceti numele de utilizator: ")
    password = input("Introduceti parola: ")

    authenticated, is_admin = authenticate(username, password, cursor)
    if authenticated:
        if is_admin:
            print("-" * 60)
            print(f"Salut, {username}! Ai fost autentificat/a ca admin.")
            while True:
                print("-" * 60)
                time.sleep(1.5)
                display_admin_menu()
                print("-" * 60)
                choice = int(input("Alege optiunea din meniu (1-5): "))
                print("-" * 60) 
                handle_admin_menu(choice, username, connection, cursor)
        else:
            print("-" * 60)
            print(f"Salut, {username}! Ai fost autentificat/a ca user.")
            while True:
                print("-" * 60)
                time.sleep(1.5)
                display_user_menu()
                print("-" * 60)
                choice = int(input("Alege optiunea din meniu (1-4): "))
                print("-" * 60) 
                handle_user_menu(choice, username, connection, cursor)
    else:
        print("Autentificare esuata! Nume de utilizator sau parola gresita!")

    close_database(connection)
    
main()