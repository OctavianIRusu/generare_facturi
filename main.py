"""
main.py

This module provides classes and functions for displaying menus and handling 
user input.

Usage:
1. Create an instance of MenuHandler.
2. Call the main() method to start the application.
3. The user is prompted for login credentials.
4. Depending on the user type, the corresponding menu is displayed.
5. The user selects an option from the menu, and the action is executed.
6. The process continues until the user chooses to logout.

Dependencies:
- The module requires a database connection and appropriate database operations.

For more information, refer to the README file.
"""
import sqlite3
import subprocess
import sys
import time

from bill_database import (LINE_SEPARATOR, add_new_user, authenticate,
                           close_database, create_consumption_table,
                           delete_user, export_excel_table,
                           generate_bill_input, generate_excel_input,
                           get_bill_info, get_client_info, get_index_input,
                           modify_user_address, open_database,
                           perform_database_operation, provide_index,
                           update_index)
from exceptions import AuthenticationError
from generate_bill import generate_pdf_bill, set_pdf_name


class MenuHandler:
    """
    A class that handles the menu options and actions for the billing application.

    Attributes:
        connection (object): The database connection object.
        cursor (object): The database cursor object.
    """

    def __init__(self):
        self.connection = open_database()
        self.cursor = perform_database_operation(self.connection)
        self.username = ""
        self.is_admin = False

    def display_menu(self, menu_title, menu_options):
        """
        Display the menu options.

        Args:
            menu_title (str): The menu type, depending on user role.
            menu_options (dict): Dictionary of menu options depending on role.
        """
        print(menu_title)
        for key, value in menu_options.items():
            print(f"{key}. {str(value)}")
        print(LINE_SEPARATOR)

    def display_user_menu(self):
        """
        Display the user menu options.
        """
        menu_title = "Meniu utilizator: "
        menu_options = {
            1: "Genereaza factura in format PDF",
            2: "Genereaza export excel cu consumul anual",
            3: "Adauga index contor energie electrica",
            4: "Delogare"
        }
        self.display_menu(menu_title, menu_options)

    def display_admin_menu(self):
        """
        Display the admin menu options.
        """
        menu_title = "Meniu administrator: "
        menu_options = {
            1: "Adauga un client",
            2: "Modifica informatiile unui client existent",
            3: "Modifica un index existent",
            4: "Sterge un client",
            5: "Delogare"
        }
        self.display_menu(menu_title, menu_options)

    def handle_menu(self, menu_actions):
        """
        Handle the selected option from the menu.

        Args:
            menu_actions (dict): Dictionary mapping menu options to actions.
        """
        while True:
            time.sleep(0.5)
            print(LINE_SEPARATOR)
            if self.is_admin:
                self.display_admin_menu()
            else:
                self.display_user_menu()
            try:
                choice = input("Alege optiunea din meniu: ")
                if not choice.isdigit() or int(choice) not in menu_actions:
                    raise ValueError(
                        f"Introdu un numar intre 1 si {len(menu_actions)}!")
                choice = int(choice)
                menu_action = menu_actions[choice]
                menu_action()
            except ValueError as verr:
                print(LINE_SEPARATOR)
                print(f"Eroare: {verr}")

    def handle_user_menu(self):
        """
        Handle the user menu options.

        This method sets up a dictionary `menu_actions` with numeric choices 
        as keys and corresponding menu actions as values. 
        It then calls the `handle_menu` method with the `menu_actions` 
        dictionary as an argument.
        """
        menu_actions = {
            1: self.generate_pdf_bill_menu_action,
            2: self.generate_excel_table_menu_action,
            3: self.add_index_menu_action,
            4: self.logout_menu_action,
        }
        try:
            self.handle_menu(menu_actions)
        except ValueError as verr:
            print(LINE_SEPARATOR)
            print(f"Eroare: {verr}")

    def handle_admin_menu(self):
        """
        Handle the admin menu options.

        This method sets up a dictionary with numeric choices as keys and
        corresponding menu actions as values. It then calls the `handle_menu`
        method with the `menu_actions` dictionary as an argument.
        """
        menu_actions = {
            1: self.add_new_user_menu_action,
            2: self.modify_user_info_menu_action,
            3: self.modify_index_menu_action,
            4: self.delete_user_menu_action,
            5: self.logout_menu_action,
        }
        try:
            self.handle_menu(menu_actions)
        except ValueError as verr:
            print(LINE_SEPARATOR)
            print(f"Eroare: {verr}")

    def generate_pdf_bill_menu_action(self):
        """
        Generate a PDF bill for the user's selected month.

        This method prompts the user to enter the year and month for which 
        they want to generate a bill. It retrieves the bill serial and number 
        for the specified month and year from the database. Then it sets the 
        file name for the generated PDF bill based on the bill serial and number.
        It retrieves the client information, bill information, and bill details 
        from the database. Finally, it generates the PDF bill using the 
        retrieved information.
        """
        try:
            bill_year, bill_month = generate_bill_input(self.cursor, self.username)
            bill_info = get_bill_info(
                self.username, bill_year, bill_month, self.cursor)
            bill_serial = bill_info["bill_serial"]
            bill_number = bill_info["bill_number"]
            file_name = set_pdf_name(bill_serial, bill_number)
            client_info = get_client_info(self.username, self.cursor)
            bill_details = create_consumption_table(
                self.username, bill_year, bill_month, self.cursor)
            generate_pdf_bill(file_name, client_info, bill_info, bill_details)
            subprocess.Popen(["start", "", file_name], shell=True)
        except OSError:
            print("Eroare sistem! Nu s-a putut crea calea catre fisierul pdf!")
        except KeyboardInterrupt:
            print(f"\n{LINE_SEPARATOR}")
            print("***Programul a fost întrerupt de utilizator!***")

    def generate_excel_table_menu_action(self):
        """
        Generates an Excel table and exports it based on user input.

        This method prompts the user to enter a bill year and generates an 
        Excel table based on the provided year. It then exports the generated 
        table that contains the energy consumptio for the specified year.
        """
        try:
            bill_year = generate_excel_input()
            export_excel_table(self.cursor, self.username, bill_year)
        except ValueError:
            print("Eroare: Date invalide! Nu s-a putut genera exportul!")
        except OSError:
            print("Eroare sistem! Nu s-a putut crea calea catre fisierul excel!")
        except KeyboardInterrupt:
            print(f"\n{LINE_SEPARATOR}")
            print("***Programul a fost întrerupt de utilizator!***")

    def add_index_menu_action(self):
        """
        Adds a new index value for a specific bill year and month.

        This method prompts the user to enter the bill year, bill month, 
        and index value. It then adds the provided index value to the database
        for the corresponding year and month.
        """
        try:
            bill_year, bill_month, index_value = get_index_input(
                self.cursor, self.username)
            provide_index(
                self.connection, self.cursor, self.username, bill_year,
                bill_month, index_value)
        except ValueError as verr:
            print(LINE_SEPARATOR)
            print(str(verr))
        except KeyboardInterrupt as kierr:
            print(f"\n{LINE_SEPARATOR}")
            print(str(kierr))
        except TypeError as terr:
            print(LINE_SEPARATOR)
            print(str(terr))

    def logout_menu_action(self):
        """
        Performs the logout action.

        Closes the database, prints a logout message and exits the program.
        """
        try:
            close_database(self.connection)
            print(LINE_SEPARATOR)
            print(f"Ai fost delogat/a! La revedere, {self.username}!")
            print(LINE_SEPARATOR)
            sys.exit()
        except KeyboardInterrupt:
            print(f"\n{LINE_SEPARATOR}")
            print(str("!Programul a fost întrerupt de utilizator!"))
        except sqlite3.Error as sqerr:
            print(sqerr)

    def add_new_user_menu_action(self):
        """
        Executes the action for adding a new user to the system.

        This method calls the `add_new_user` function, passing the database 
        connection and cursor as parameters. The `add_new_user` function 
        performs the necessary steps to add a new user to the system.
        """
        try:
            add_new_user(self.connection, self.cursor)
        except sqlite3.Error as sqerr:
            print(LINE_SEPARATOR)
            print(sqerr)
        except ValueError as verr:
            print(LINE_SEPARATOR)
            print(verr)
        except KeyboardInterrupt:
            print(f"\n{LINE_SEPARATOR}")
            print(str("!Programul a fost întrerupt de utilizator!"))

    def modify_user_info_menu_action(self):
        """
        Executes the action for modifying a specific field in the users table 
        of the SQLite database.

        This method calls the `modify_user_info` function, prompts the admin to
        select a field and enter a new value for that field, and then updates 
        the specified field in the users table with the new value.
        """
        try:
            modify_user_address(self.connection, self.cursor)
        except ValueError:
            print(LINE_SEPARATOR)
            print("Operatie nereusita, datele furnizate sunt invalide!")
        except LookupError as lerr:
            print(LINE_SEPARATOR)
            print(str(lerr))
        except KeyboardInterrupt:
            print(f"\n{LINE_SEPARATOR}")
            print(str("!Programul a fost întrerupt de utilizator!"))

    def modify_index_menu_action(self):
        """
        Executes the action for modifying the consumption index for a specific
        user for the last month.
        """
        try:
            update_index(self.connection, self.cursor)
        except KeyboardInterrupt as kierr:
            print(f"\n{LINE_SEPARATOR}")
            print(str(kierr))
        except ValueError:
            print(LINE_SEPARATOR)
            print("Operatie nereusita, datele furnizate sunt invalide!")
        except LookupError as lerr:
            print(LINE_SEPARATOR)
            print(str(lerr))

    def delete_user_menu_action(self):
        """
        Performs the deletion of an user based on the username.
        """
        try:
            delete_user(self.connection, self.cursor)
        except LookupError as lerr:
            print(LINE_SEPARATOR)
            print(str(lerr))
        except KeyboardInterrupt as kierr:
            print(LINE_SEPARATOR)
            print(str(kierr))
        except RuntimeError as rterr:
            print(LINE_SEPARATOR)
            print(str(rterr))

    def main(self):
        """
        Main function to run the application.
        """
        print(LINE_SEPARATOR)
        print("Bine ai venit! Pentru a continua este necesara autentificarea!")
        while True:
            try:
                print(LINE_SEPARATOR)
                self.username = input("Introduceti numele de utilizator: ")
                password = input("Introduceti parola: ")
                time.sleep(0.5)
                authenticated, self.is_admin = authenticate(
                    self.username, password, self.cursor)
                print(LINE_SEPARATOR)
                if authenticated:
                    print(f"Salut, {self.username}! Ai fost autentificat/a ca "
                          f"{'administrator' if self.is_admin else 'user'}.")
                    if self.is_admin:
                        self.handle_admin_menu()
                    else:
                        self.handle_user_menu()
                else:
                    raise AuthenticationError("Username sau parola gresita!")
            except AuthenticationError as aerr:
                print(aerr)
                continue
            except sqlite3.Error:
                print(LINE_SEPARATOR)
                print(str("Eroare: Baza de date nu a putut fi accesata!"))
            except KeyboardInterrupt:
                print(f"\n{LINE_SEPARATOR}")
                print("***Programul a fost întrerupt de utilizator!***")
                sys.exit()

if __name__ == "__main__":
    menu_handler = MenuHandler()
    menu_handler.main()
