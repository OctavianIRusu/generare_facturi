import time
from generate_bill import generate_pdf_bill
from bill_database import new_user, get_client_info, cursor

PDF_FILE_NAME = "factura_greenergy xx-xxxxxx.pdf"

# Define a dictionary that stores information about the client
CLIENT_INFO = get_client_info(3)

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

generate_pdf_bill(PDF_FILE_NAME, CLIENT_INFO, BILL_INFO, BILL_DETAILS)

def authenticate(username, password):
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

def handle_menu_choice(choice, is_admin, username):
    if is_admin:
        if choice == 1:
            # View records logic for admin
            print("Vizualizare intrari din baza de date!")
        elif choice == 2:
            # Add record logic for admin
            print("Adaugare intrare noua in baza de date!")
        elif choice == 3:
            # Update record logic for admin
            print("Modificare intrare existenta in baza de date!")
        elif choice == 4:
            # Delete record logic for admin
            print("Stergere intrare din baza de date!")
        elif choice == 5:
            print(f"Ai fost delogat! La revedere, {username}!")
            quit()
        else:
            print("Optiune invalida. Incearca una dintre variantele 1-5.")
    else:
        if choice == 1:
            # Generate PDF logic for user
            print("Genereaza ultima factura in format PDF!")
        elif choice == 2:
            # Generate Excel logic for user
            print("Genereaza un export xls cu consumul tau din anul curent!")
        elif choice == 3:
            # Add Energy Consumption logic for user
            print("Adauga indexul pentru luna curenta!")
        elif choice == 4:
            print(f"Ai fost delogat! La revedere, {username}!")
            quit()
        else:
            print("Optiune invalida. Incearca una dintre variantele 1-4.")

def main():
    print("Bine ai venit! Pentru a continua este necesara autentificarea!")
    username = input("Introduceti numele de utilizator: ")
    password = input("Introduceti parola: ")

    authenticated, is_admin = authenticate(username, password)
    if authenticated:
        if is_admin:
            print("-" * 20)
            print(f"Salut, {username}! Ai fost autentificat ca admin.")
            print("-" * 20)
            time.sleep(2)
            while True:
                display_admin_menu()
                print("-" * 20)
                choice = int(input("Alege optiunea din meniu (1-5): "))
                print("-" * 20)
                handle_menu_choice(choice, is_admin, username)
        else:
            print("-" * 20)
            print(f"Salut, {username}! Ai fost autentificat ca user.")
            print("-" * 20)
            time.sleep(2)
            while True:
                display_user_menu()
                print("-" * 20)
                choice = int(input("Alege optiunea din meniu (1-4): "))
                print("-" * 20)
                handle_menu_choice(choice, is_admin, username)
    else:
        print("Autentificare esuata! Nume de utilizator sau parola gresita!")

main()