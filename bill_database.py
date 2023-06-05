import sqlite3
from pathlib import Path

# Set the root folder path and database path
ROOT = Path(__file__).parent
DB_FILE = ROOT / "bill_database.sqlite"

# Create a connection to the database
def open_database():
    connection = sqlite3.connect(DB_FILE)
    return connection
    
def perform_database_operation(connection):
    cursor = connection.cursor()
    return cursor

def close_database(connection):
    connection.close()

def view_users(cursor):
    cursor.execute('''
        SELECT * FROM users                   
    ''')
    rows = cursor.fetchall()
    for row in rows:
        print(row)

def add_new_user(connection, cursor):
    name = input("Introdu prenume si nume: ")
    street = input("Introdu adresa (strada, nr, bloc, apartament): ")
    zipcode = input("Introdu codul postal: ")
    city = input("Introdu localitatea: ")
    county = input("Introdu judetul: ")
    username = input("Introdu un nume de utilizator: ")
    password = input("Introdu o parola: ")
    role = input("Alege tip user (user/admin): ")
    
    cursor.execute('''
        INSERT INTO users (name, street, zipcode, city, county, username, password, role)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (name, street, zipcode, city, county, username, password, role))
    connection.commit()
    print("-" * 60)
    print("Client nou adaugat cu succes!")


def get_client_info(username, cursor):
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    if row:
        columns = [desc[0] for desc in cursor.description]
        user_dict = dict(zip(columns, row))
        return user_dict
    else:
        return None