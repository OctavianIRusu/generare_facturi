from generate_bill import generate_pdf_bill
from bill_database import new_user, get_client_info

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