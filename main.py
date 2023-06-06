import time
from generate_bill import generate_pdf_bill, set_file_name
from bill_database import (open_database, perform_database_operation, 
    close_database, view_users, add_new_user, get_client_info, get_bill_info, 
    provide_new_index, get_index_input, authenticate, generate_bill_input, 
    create_consumption_table)

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
        time.sleep(1.5)
    elif choice == 2:
        add_new_user(connection, cursor)
        print("-" * 60)
        time.sleep(1.5)
    elif choice == 3:
        # Update record logic for admin
        print("Modificare informatii client/index existent in baza de date!")
    elif choice == 4:
        # Delete record logic for admin
        print("Stergere client din baza de date!")
    elif choice == 5:
        print(f"Ai fost delogat/a! La revedere, {username}!")
        quit()
    else:
        print("Optiune invalida. Incearca una dintre variantele 1-5.")
            
def handle_user_menu(choice, username, connection, cursor):            
    if choice == 1:
        bill_year, bill_month = generate_bill_input()
        bill_serial = get_bill_info(username, bill_year, bill_month, cursor)["bill_serial"]
        bill_number = get_bill_info(username, bill_year, bill_month, cursor)["bill_number"]
        file_name = set_file_name(bill_serial, bill_number)
        client_info = get_client_info(username, cursor)
        bill_info = get_bill_info(username, bill_year, bill_month, cursor)
        bill_details = create_consumption_table(username, bill_year, bill_month, cursor)
        generate_pdf_bill(file_name, client_info, bill_info, bill_details)
    elif choice == 2:
        # Generate Excel logic for user
        print("Genereaza un export xls cu consumul tau din anul curent!")
    elif choice == 3:
        bill_year, bill_month, index_value = get_index_input(cursor, username)
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
            time.sleep(1.5)
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
            time.sleep(1.5)
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