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
        name TEXT,
        street TEXT,
        zipcode TEXT,
        city TEXT,
        county TEXT
    )
''')

def new_user():
    name = input("Enter name: ")
    street = input("Enter street: ")
    zipcode = input("Enter zipcode: ")
    city = input("Enter city: ")
    county = input("Enter county: ")
    
    cursor.execute('''
        INSERT INTO entries (name, street, zipcode, city, county)
        VALUES (?, ?, ?, ?, ?)
    ''', (name, street, zipcode, city, county))
    connection.commit()
    print("Entry created successfully!")


def get_client_info(id):
    
    cursor.execute("SELECT * FROM entries")
    rows = cursor.fetchall()

    entries = []
    for row in rows:
        entry = {
            "id": row[0],
            "name": row[1],
            "street": row[2],
            "zipcode": row[3],
            "city": row[4],
            "county": row[5]
        }
        entries.append(entry)
        

    return entries[id]

connection.close()

