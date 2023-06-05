import sqlite3
from pathlib import Path

# Set the root folder path and database path
ROOT = Path(__file__).parent
DB_FILE = ROOT / "bill_database.sqlite"

# Create a connection to the database
connection = sqlite3.connect(DB_FILE)
cursor = connection.cursor()

# Create a table if it doesn't exist
cursor.execute('''
    CREATE TABLE IF NOT EXISTS entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        street TEXT NOT NULL,
        zipcode TEXT NOT NULL,
        city TEXT NOT NULL,
        county TEXT NOT NULL,
        username TEXT NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL
    )
''')

def new_user():
    name = input("Enter name: ")
    street = input("Enter street: ")
    zipcode = input("Enter zipcode: ")
    city = input("Enter city: ")
    county = input("Enter county: ")
    username = input("Enter username: ")
    password = input("Enter password: ")
    role = input("Enter role (user/admin): ")
    
    cursor.execute('''
        INSERT INTO entries (name, street, zipcode, city, county, username, password, role)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (name, street, zipcode, city, county, username, password, role))
    connection.commit()
    print("Entry created successfully!")
    connection.close()  


def get_client_info(id):
    
    cursor.execute("SELECT * FROM users")
    rows = cursor.fetchall()

    users = []
    for row in rows:
        entry = {
            "id": row[0],
            "name": row[1],
            "street": row[2],
            "zipcode": row[3],
            "city": row[4],
            "county": row[5]
        }
        users.append(entry)
        

    return users[id]