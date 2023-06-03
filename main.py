from generate_bill import generate_pdf_bill

PDF_FILE_NAME = "factura_greenergy xx-xxxxxx.pdf"

# Define a dictionary that stores information about the client
CLIENT_INFO = {
    "name": "George Adrian",
    "street": "Strada 9 Mai nr. 28",
    "zipcode": "450060",
    "city": "Cluj-Napoca",
    "county": "Cluj"
}

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
try:
    generate_pdf_bill(PDF_FILE_NAME, CLIENT_INFO, BILL_INFO, BILL_DETAILS)
except TypeError as terr:
    print(f"")