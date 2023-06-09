# Energy Billing Application

The Energy Billing Application is a command-line utility that helps manage
energy consumption and generate monthly bills for users. It utilizes a SQLite 
database to store user information, consumption data, and billing details.

# Features

### User Authentication:

The application supports user authentication, ensuring that only authorized 
users can access and modify the billing information.

- #### User Menu: Once authenticated, users can perform the following tasks:

  **Generate Monthly Bill*:

  Users can generate a monthly bill in PDF format, including detailed 
  consumption information and billing totals.

  **Export Annual Consumption*:

  Users can export their annual consumption data to an Excel file for further 
  analysis and record-keeping.

  **Add Energy Meter Index*:

  Users can enter their monthly energy meter index to update their consumption 
  records and calculate accurate bills.

  **Logout*:

  Users can logout from the application.
- #### Admin Menu: Admin users have additional administrative options, including:

  **Add New Client*:

  Admins can add new clients to the system, providing their user information
  like address and their role in the app.

  **Modify Address*:

  Admins can modify client address information.

  **Modify Consumption Index*:

  Admins can correct client index value if any errors occured.

  **Delete Client*:

  Admins can delete a client from the database.

  **Logout*:

  Admins can logout from the application.

# Getting Started

To use the Energy Billing Application, follow these steps:

1. Install the required dependencies by running
   *pip install -r requirements.txt*.
2. Run the main.py file to start the application.
3. When prompted, enter your username and password to log in. 
   For admin users, only administrative options will be available.
4. Choose from the menu options to generate bills, export consumption data, 
   add meter index, or perform other administrative tasks.

# Dependencies

The Energy Billing Application relies on the following dependencies:

- Python 3.x
- SQLite3
- pandas
- matplotlib
- ReportLab

#### Ensure that these dependencies are installed before running the application.

# Notes

The application assumes that a SQLite database file named *energy_billing.db* 
is present in the same directory as the code files. If the database file is 
missing, the application will create a new one but you will lose current
information, and you have to manually input an admin user and after that
configure other clients.

For generating PDF bills, the application uses the ReportLab library.

# App features testing

For app testing purpose you can use the following defined users in the db:
- user role:
  - username: silviutanase
  - password: silviutanase
- admin role:
  - username: ivangiurgiu
  - password: ivangiurgiu