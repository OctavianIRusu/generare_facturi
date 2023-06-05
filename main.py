import time
from generate_bill import generate_pdf_bill
from bill_database import open_database, perform_database_operation, close_database, view_users, add_new_user, get_client_info

PDF_FILE_NAME = "factura_greenergy xx-xxxxxx.pdf"

# Define a dictionary that stores identification information about the current bill
BILL_INFO = {
    "serie": "CJ",
    "numar": "310423001",
    "bill_date": "27.04.2023",
    "due_date": "29.05.2023",
    "date_interval": "01.03.2023 - 31.03.2023"
}

# Define a dictionary that stores the detailed information about the consumption and price
BILL_DETAILS = {
    "Produse si servicii": ["Energie consumata", "Acciza necomerciala", "Certificate verzi", "OUG 27"],
    "Cantitate": [89, 0.089, 0.089, -89],
    "U.M.": ["kWh", "MWh", "MWh", "kWh"],
    "Pret unitar fara TVA": [1.40182, 6.05000, 71.68059, 0.90812],
    "Valoare fara TVA": [124.76, 0.54, 6.38, -80.82],
    "Valoare TVA (19%)": [23.7, 0.1, 1.21, -15.36]
}


def authenticate(username, password, cursor):
    cursor.execute("SELECT role FROM users WHERE username = ? AND password = ?", (username, password))
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
    print("3. Adauga index pentru luna curenta")
    print("4. Delogare")

def display_admin_menu():
    print("1. Vezi clientii existenti")
    print("2. Adauga un client")
    print("3. Modifica informatiile pentru un client existent")
    print("4. Sterge un client")
    print("5. Delogare")

def handle_menu_choice(choice, is_admin, username, connection, cursor):
    if is_admin:
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
            print("Optiune invalida. Incearca una dintre variantele 1-5.")
    else:
        if choice == 1:
            generate_pdf_bill(PDF_FILE_NAME, get_client_info(username, cursor), BILL_INFO, BILL_DETAILS)
        elif choice == 2:
            # Generate Excel logic for user
            print("Genereaza un export xls cu consumul tau din anul curent!")
        elif choice == 3:
            # Add Energy Consumption logic for user
            print("Adauga indexul pentru luna curenta!")
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
                handle_menu_choice(choice, is_admin, username, connection, cursor)
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
                handle_menu_choice(choice, is_admin, username, connection, cursor)
    else:
        print("Autentificare esuata! Nume de utilizator sau parola gresita!")

    close_database(connection)
main()