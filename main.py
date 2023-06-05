import time
from datetime import date
from generate_bill import generate_pdf_bill
from bill_database import (open_database, perform_database_operation, 
    close_database, get_romanian_month_name, view_users, add_new_user, 
    get_client_info, provide_new_index, calculate_cons)

PDF_FILE_NAME = "factura_greenergy xx-xxxxxx.pdf"

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

def display_user_menu():
    print("1. Genereaza factura in format PDF")
    print("2. Genereaza export xls cu consumul din anul curent")
    print("3. Adauga index contor energie electrica")
    print("4. Delogare")

def display_admin_menu():
    print("1. Vezi clientii existenti")
    print("2. Adauga un client")
    print("3. Modifica informatiile pentru un client existent")
    print("4. Sterge un client")
    print("5. Delogare")

def handle_admin_menu(choice, username, connection, cursor):
    if choice == 1:
        view_users(cursor)
        print("-" * 60)
        time.sleep(2)
    elif choice == 2:
        add_new_user(connection, cursor)
        print("-" * 60)
        time.sleep(2)
    elif choice == 3:
        # Update record logic for admin
        print("Modificare intrare existenta in baza de date!")
    elif choice == 4:
        # Delete record logic for admin
        print("Stergere intrare din baza de date!")
    elif choice == 5:
        print(f"Ai fost delogat/a! La revedere, {username}!")
        quit()
    else:
        print("Optiune invalida. Incearca una dintre variantele 1-5.")\
            
def handle_user_menu(choice, username, connection, cursor):            
    if choice == 1:
        generate_pdf_bill(PDF_FILE_NAME, get_client_info(username, cursor), BILL_INFO, BILL_DETAILS)
    elif choice == 2:
        # Generate Excel logic for user
        print("Genereaza un export xls cu consumul tau din anul curent!")
    elif choice == 3:
        bill_year = int(input("Introdu anul pentru care vrei sa adaugi indexul: "))
        bill_month = int(input("Introdu luna pentru care vrei sa adaugi indexul: "))
        while True:
            index_value = float(input(f"Introdu indexul pentru luna {get_romanian_month_name(bill_month)} {bill_year}: "))
            cons_data = calculate_cons(cursor, username, bill_year, bill_month, index_value)
            consumption = cons_data['energ_cons_cant']
            print(f"Conform acestui index, consumul pentru luna "
                f"{get_romanian_month_name(bill_month)} {bill_year} va fi de "
                f"{consumption} kWh.")
            check_index = input("Doresti sa continui cu acest index? (y/n) ")
            if check_index.lower() == "y":
                break
            elif check_index.lower() == "n":
                continue
        provide_new_index(cursor, connection, username, bill_year, bill_month, index_value)
    elif choice == 4:
        print(f"Ai fost delogat/a! La revedere, {username}!")
        quit()
    else:
        print("Optiune invalida. Incearca una dintre variantele 1-4.")

def main():
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
            print("-" * 60)
            time.sleep(2)
            while True:
                print("-" * 60)
                display_admin_menu()
                print("-" * 60)
                choice = int(input("Alege optiunea din meniu (1-5): "))
                print("-" * 60) 
                handle_admin_menu(choice, username, connection, cursor)
        else:
            print("-" * 60)
            print(f"Salut, {username}! Ai fost autentificat/a ca user.")
            print("-" * 60)
            time.sleep(2)
            while True:
                print("-" * 60)
                display_user_menu()
                print("-" * 60)
                choice = int(input("Alege optiunea din meniu (1-4): "))
                print("-" * 60) 
                handle_user_menu(choice, username, connection, cursor)
    else:
        print("Autentificare esuata! Nume de utilizator sau parola gresita!")

    close_database(connection)
main()