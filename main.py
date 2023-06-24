"""
main.py

This module provides classes and functions for displaying menus and handling 
user input.

Classes:
- MenuHandler: Handles the display and interaction of menus for both users 
and administrators.

Exceptions:
- AuthenticationError: Raised when authentication fails during login.

Functions:
- open_database(): Opens a connection to the database.
- perform_database_operation(): Performs a database operation using the 
provided connection.
- close_database(): Closes the database connection.

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
import sys
import time

from bill_database import (add_new_user, authenticate, close_database,
                           create_consumption_table, delete_user,
                           export_excel_table, generate_bill_input,
                           generate_excel_input, get_bill_info,
                           get_client_info, get_index_input, open_database,
                           perform_database_operation, provide_new_index)
from generate_bill import generate_pdf_bill, set_pdf_name

class AuthenticationError(Exception):
    """
    Exception raised for authentication errors.

    Attributes:
        message (str): The error message describing the authentication error.

    Methods:
        __init__(self, message): Initialize the AuthenticationError instance.
        __str__(self): Return a string representation of the exception.
    """

    def __init__(self, message):
        """
        Initialize the AuthenticationError instance.

        Args:
            message (str): The error message describing the authentication error.
        """
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        """
        Return a string representation of the exception.

        Returns:
            str: The error message of the exception.
        """
        return self.message

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

    def display_menu(self, menu_options, menu_title):
        """
        Display the menu options.

        Args:
            menu_options (list): List of menu options.
        """
        print(menu_title)
        for key, value in menu_options.items():
            print(f"{key}. {str(value)}")
        print("-" * 65)

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
        self.display_menu(menu_options, menu_title)

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
        self.display_menu(menu_options, menu_title)

    def handle_menu(self, menu_actions):
        """
        Handle the selected option from the menu.

        Args:
            menu_actions (dict): Dictionary mapping menu options to actions.
        """
        while True:
            time.sleep(1)
            print("-" * 65)
            if self.is_admin:
                self.display_admin_menu()
            else:
                self.display_user_menu()
            try:
                choice = input("Alege optiunea din meniu: ")
                if not choice.isdigit() or int(choice) not in menu_actions:
                    raise ValueError(f"Introdu un numar intre 1 si {len(menu_actions)}!")
                choice = int(choice)
                menu_action = menu_actions[choice]
                menu_action()
            except ValueError as verr:
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
        self.handle_menu(menu_actions)

    def handle_admin_menu(self):
        """
        Handle the admin menu options.

        This method sets up a dictionary `menu_actions` with numeric choices 
        as keys and corresponding menu actions as values. 
        It then calls the `handle_menu` method with the `menu_actions` 
        dictionary as an argument.
        """
        menu_actions = {
            1: self.add_new_user_menu_action,
            2: self.modify_user_info_menu_action,
            3: self.modify_index_menu_action,
            4: self.delete_user_menu_action,
            5: self.logout_menu_action,
        }
        self.handle_menu(menu_actions)

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

        If a TypeError occurs, it is likely due to missing consumption records 
        for the selected month. In such cases, an error message is displayed 
        indicating that consumption data is not available.
        """
        while True:
            try:
                bill_year, bill_month = generate_bill_input()
                break
            except TypeError:
                print("Eroare: Date invalide! Nu s-a putut genera factura!")
                print("-" * 65)
            try:
                bill_serial = get_bill_info(
                    self.username, bill_year, bill_month, self.cursor)["bill_serial"]
                bill_number = get_bill_info(
                    self.username, bill_year, bill_month, self.cursor)["bill_number"]
            except TypeError:
                print("Eroare!")
        file_name = set_pdf_name(bill_serial, bill_number)
        client_info = get_client_info(self.username, self.cursor)
        bill_info = get_bill_info(
            self.username, bill_year, bill_month, self.cursor)
        bill_details = create_consumption_table(
            self.username, bill_year, bill_month, self.cursor)
        generate_pdf_bill(file_name, client_info, bill_info, bill_details)


    def generate_excel_table_menu_action(self):
        bill_year = generate_excel_input()
        export_excel_table(self.cursor, self.username, bill_year)

    def add_index_menu_action(self):
        try:
            bill_year, bill_month, index_value = get_index_input(
                self.cursor, self.username)
            provide_new_index(
                self.connection, self.cursor, self.username, bill_year,
                bill_month, index_value)
        except ValueError as err:
            print("-" * 65)
            print(str(err))

    def logout_menu_action(self):
        """
        Performs the logout action.

        Prints a logout message with the username and exits the program.
        """
        print(f"Ai fost delogat/a! La revedere, {self.username}!")
        sys.exit()
        
    def add_new_user_menu_action(self):
        add_new_user(self.connection, self.cursor)

    def modify_user_info_menu_action(self):
        pass

    def modify_index_menu_action(self):
        pass

    def delete_user_menu_action(self):
        """
        Performs the deletion of an user based on the username.
        """
        try:
            delete_user(self.connection, self.cursor)
        except LookupError as lerr:
            print("-" * 65)
            print(str(lerr))
        except KeyboardInterrupt as kierr:
            print("-" * 65)
            print(str(kierr))
        except RuntimeError as rterr:
            print("-" * 65)
            print(str(rterr))

    def main(self):
        """
        Main function to run the application.
        """
        print("-" * 65)
        print("Bine ai venit! Pentru a continua este necesara autentificarea!")
        print("-" * 65)
        username = input("Introduceti numele de utilizator: ")
        password = input("Introduceti parola: ")
        time.sleep(1)

        try:
            authenticated, self.is_admin = authenticate(
                username, password, self.cursor)
            print("-" * 65)

            if authenticated:
                print(
                    f"Salut, {username}! Ai fost autentificat/a ca {'administrator' if self.is_admin else 'user'}.")
                self.username = username

                if self.is_admin:
                    self.handle_admin_menu()
                else:
                    self.handle_user_menu()
            else:
                raise AuthenticationError(
                    "Autentificare esuata! Username sau parola gresita!")
        except AuthenticationError as aerr:
            print(str(aerr))
            sys.exit()

        close_database(self.connection)


if __name__ == "__main__":
    menu_handler = MenuHandler()
    menu_handler.main()