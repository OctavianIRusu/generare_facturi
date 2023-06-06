import time
from generate_bill import generate_pdf_bill, set_pdf_name
from bill_database import (open_database, perform_database_operation, 
    close_database, view_users, add_new_user, get_client_info, get_bill_info, 
    provide_new_index, get_index_input, authenticate, generate_bill_input, 
    create_consumption_table, generate_excel_input, export_excel_table)

def display_user_menu():
    print("1. Genereaza factura lunara in format PDF")
    print("2. Genereaza export excel cu consumul anual")
    print("3. Adauga index contor energie electrica")
    print("4. Delogare")

def display_admin_menu():
    print("1. Vezi clientii existenti")
    print("2. Adauga un client")
    print("3. Modifica informatiile pentru un client sau un index existent")
    print("4. Modifica un index existent")
    print("5. Sterge un client")
    print("6. Delogare")

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
        pass
    elif choice == 4:
        pass
    elif choice == 5:
        print("Stergere client din baza de date!")
    elif choice == 6:
        print(f"Ai fost delogat/a! La revedere, {username}!")
        quit()
    else:
        print("Optiune invalida. Incearca una dintre variantele 1-5.")
            
def handle_user_menu(choice, username, connection, cursor):            
    if choice == 1:
        # generare factura in pdf
        bill_year, bill_month = generate_bill_input()
        bill_serial = get_bill_info(username, bill_year, bill_month, cursor)["bill_serial"]
        bill_number = get_bill_info(username, bill_year, bill_month, cursor)["bill_number"]
        file_name = set_pdf_name(bill_serial, bill_number)
        client_info = get_client_info(username, cursor)
        bill_info = get_bill_info(username, bill_year, bill_month, cursor)
        bill_details = create_consumption_table(username, bill_year, bill_month, cursor)
        generate_pdf_bill(file_name, client_info, bill_info, bill_details)
    elif choice == 2:
        # generare export in excel
        bill_year = generate_excel_input()
        export_excel_table(cursor, username, bill_year)
    elif choice == 3:
        # adaugare index consum
        bill_year, bill_month, index_value = get_index_input(cursor, username)
        provide_new_index(connection, cursor, username, bill_year, bill_month, index_value)
    elif choice == 4:
        # delogare
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