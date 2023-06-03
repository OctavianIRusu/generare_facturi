from pathlib import Path
from reportlab.graphics.barcode import code128
from reportlab.lib.colors import black, lightgrey, white, whitesmoke, green
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import cm
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Table, TableStyle

# Set the root folder path and icons folder path
MAIN_FOLDER_ROOT = Path(__file__).parent
ICONS_PATH = MAIN_FOLDER_ROOT / "icons"

# Define the page size and get the width and height values by tuple unpacking
PAGE_SIZE = LETTER
P_WIDTH, P_HEIGHT = PAGE_SIZE

# Define the file paths for the logo and various icon images used in the application
COMPANY_LOGO_FILE = "greenergy_icon.png"
LOCATION_ICON_FILE = "location_icon.png"
PHONE_ICON_FILE = "phone_icon.png"
EMAIL_ICON_FILE = "email_icon.png"

# Define a dictionary named COMPANY_INFO that stores information about the electrical company
COMPANY_INFO = {
    "name": "Greenergy",
    "street": "Bulevardul Ion C. Bratianu nr. 44",
    "city": "Bucuresti",
    "country": "Romania",
    "phone": "021-336 5503",
    "email": "contact@greenergy.ro"
}

def draw_img(canvas: Canvas, file_path: Path, x_origin: float, y_origin: float, img_width: float, img_height: float, mask):
    """
    Inserts an image within a canvas
    
    Args:
    - canvas (Canvas): The canvas where the image will be inserted
    - file_path (str): The path to the image file that will be inserted
    - xbl_origin (float): The x-coordinate of the bottom-left corner of the image (percentage of the page size, e.g. 0.85)
    - ybl_origin (float): The y-coordinate of the bottom-left corner of the image (percentage of the page size, e.g. 0.85)
    - img_width (float): The width of the image (percentage of the page size, e.g. 0.85)
    - img_height (float): The height of the image (percentage of the page size, e.g. 0.85)
    - mask (str): The mask to apply when drawing the image (optional)
    
    Raises:
    - OSError: If the specified file cannot be accessed or opened
    - ValueError: If any of the float arguments (`x_origin`, `y_origin`, `img_width`, `img_height`)
            have invalid values, such as negative values or values exceeding the canvas dimensions.
            
    Returns:
        None
    """
    try:
        if not 0 <= x_origin <= 1 or not 0 <= y_origin <= 1 or not 0 <= img_width <= 1 or not 0 <= img_height <= 1:
            raise ValueError("The position and dimension arguments must be float values between 0 and 1 (inclusive).")
        canvas.drawImage(file_path, x_origin * P_WIDTH, y_origin * P_HEIGHT, img_width * P_WIDTH, img_height * P_HEIGHT, mask)
    except OSError as oserr:
        print("An error occurred while accessing or opening the file:")
        print(oserr)
    except TypeError as terr:
        print("TypeError: Incorrect input parameter type.")
        print(terr)
    except Exception as err:
        print("Error: An unexpected error occured!")
        print(err)
    
def write_text_line(canvas: Canvas, text: str, font: str, size: int, text_color: str, x: float, y: float):
    """
    Writes a single line of text on the given canvas at the specified coordinates

    Args:
        canvas (Canvas): The canvas object on which to write the text
        text (str): The text to be written
        font (str): The font to be used for the text
        size (int): The font size of the text
        x (float): The x-coordinate of the starting position of the text as float (percentage of page size)
        y (float): The y-coordinate of the baseline position of the text as float (percentage of page size)

    Returns:
        None
    """
    try:
        canvas.setFont(font, size)
        canvas.setFillColor(text_color)
        canvas.drawString(x * P_WIDTH, y * P_HEIGHT, text)
    except TypeError as terr:
        print(f"Type error: {terr}")
    except ValueError as verr:
        print(f"Value error: {verr}")
    
def generate_table(canvas, content: dict):
    """
    Generates a table on a canvas based on the provided content of dictionary type

    Args:
        canvas: The canvas object on which to draw the table.
        content (dict): A dictionary containing the table data. The keys represent
            the headers of the table, and the values are lists representing the rows.

    Returns:
        None
    """
    headers = list(content.keys())
    rows = list(zip(*content.values()))
    data = [headers] + rows

    # create the table given the columns width and rows height
    col_widths = [0.18 * P_WIDTH, 0.1 * P_WIDTH, 0.1 * P_WIDTH, 0.15 * P_WIDTH, 0.15 * P_WIDTH, 0.15 * P_WIDTH]
    row_heights = [0.058 * P_HEIGHT, 0.045 * P_HEIGHT, 0.045 * P_HEIGHT, 0.045 * P_HEIGHT, 0.045 * P_HEIGHT]
    table = Table(data, rowHeights=row_heights, colWidths=col_widths)
    
    # define the table style
    table_style = [
        ('BACKGROUND', (0, 0), (-1, 0), whitesmoke),
        ('TEXTCOLOR', (0, 0), (-1, 0), black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Times-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Times-Roman'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('BACKGROUND', (0, 1), (-1, -1), white),
        ('GRID', (0, 0), (-1, -1), 1, white),
    ]

    # apply the table style
    table.setStyle(TableStyle(table_style))
    
    # draw the table on canvas
    table_width, table_height = table.wrapOn(canvas, P_WIDTH * 0.75, P_HEIGHT)
    x = (P_WIDTH - table_width) / 2
    y = 0.238 * P_HEIGHT
    table.drawOn(canvas, x, y)
    
def generate_barcode(barcode_value, canvas_object, x):
    canvas_object.setFillColor("black")
    bill_barcode = code128.Code128(barcode_value, barWidth=1, barHeight=1 * cm, humanReadable=True)
    bill_barcode.drawOn(canvas_object, (P_WIDTH - bill_barcode.width)/x, 0.085 * P_HEIGHT)

def generate_pdf_bill(file_name: str, client_info: dict, bill_info: dict, bill_details: dict):    

    # Create a canvas object with the given file_name and pagesize
    bill_canvas = Canvas(file_name, pagesize=PAGE_SIZE)
    
    # Insert the logo and different icons in the canvas
    draw_img(bill_canvas, ICONS_PATH / COMPANY_LOGO_FILE, 0.645, 0.8, 0.159, 0.143, "auto")
    draw_img(bill_canvas, ICONS_PATH / LOCATION_ICON_FILE, 0.111, 0.862, 0.011, 0.014, "auto")
    draw_img(bill_canvas, ICONS_PATH / PHONE_ICON_FILE, 0.111, 0.826, 0.011, 0.013, "auto")
    draw_img(bill_canvas, ICONS_PATH / EMAIL_ICON_FILE, 0.111, 0.806, 0.014, 0.007, "auto")

    # Insert horizontal lines and a rectangle to visually separate and highlight the content
    bill_canvas.setStrokeColor(lightgrey)
    bill_canvas.setFillColor(lightgrey)
    bill_canvas.line(0.1 * P_WIDTH, 0.578 * P_HEIGHT, 0.9 * P_WIDTH, 0.578 * P_HEIGHT)
    bill_canvas.line(0.1 * P_WIDTH, 0.233 * P_HEIGHT, 0.9 * P_WIDTH, 0.233 * P_HEIGHT)
    bill_canvas.rect(0.1 * P_WIDTH, 0.154 * P_HEIGHT, 0.8 * P_WIDTH, 0.028 * P_HEIGHT, fill=1)

    # Insert the information text about the company
    write_text_line(bill_canvas, COMPANY_INFO["name"], "Times-Roman", 25, "green", 0.143, 0.926)
    write_text_line(bill_canvas, COMPANY_INFO["street"], "Times-Roman", 12, "black", 0.143, 0.877)  
    write_text_line(bill_canvas, COMPANY_INFO["city"], "Times-Roman", 12, "black", 0.143, 0.862)  
    write_text_line(bill_canvas, COMPANY_INFO["country"], "Times-Roman", 12, "black", 0.143, 0.847)  
    write_text_line(bill_canvas, COMPANY_INFO["phone"], "Times-Roman", 12, "black", 0.143, 0.826)  
    write_text_line(bill_canvas, COMPANY_INFO["email"], "Times-Roman", 12, "black", 0.143, 0.806)  

    # Insert the information about the current bill
    write_text_line(bill_canvas, "Factura fiscala", "Times-Bold", 13, "black", 0.625, 0.741)
    write_text_line(bill_canvas, f"Seria {bill_info['serie']} nr. {bill_info['numar']}", "Times-Roman", 12, "black", 0.625, 0.719)
    write_text_line(bill_canvas, bill_info['bill_date'], "Times-Roman", 12, "black", 0.746, 0.699)
    write_text_line(bill_canvas, bill_info['due_date'], "Times-Roman", 12, "black", 0.758, 0.680)
    write_text_line(bill_canvas, bill_info['date_interval'], "Times-Roman", 12, "black", 0.625, 0.643)
    write_text_line(bill_canvas, "Data facturii:", "Times-Bold", 12, "black", 0.625, 0.699)
    write_text_line(bill_canvas, "Data scadenta:", "Times-Bold", 12, "black", 0.625, 0.680)
    write_text_line(bill_canvas, "Perioada de facturare:", "Times-Bold", 12, "black", 0.625, 0.662)

    # Insert the information about the client
    write_text_line(bill_canvas, client_info["name"].upper(), "Times-Bold", 13, "black", 0.143, 0.741)
    write_text_line(bill_canvas, client_info["street"], "Times-Roman", 12, "black", 0.143, 0.719)
    write_text_line(bill_canvas, f"{client_info['zipcode']}, {client_info['city'].upper()}, Judetul {client_info['county']}", "Times-Roman", 12, "black", 0.143, 0.699)

    # Insert the information about the bill value
    write_text_line(bill_canvas, "Detalii factura curenta:", "Times-Bold", 24, "green", 0.111, 0.588)
    write_text_line(bill_canvas, "Din ce este compus consumul tau?", "Times-Bold", 15, "green", 0.111, 0.500)
    write_text_line(bill_canvas, f"{COMPANY_INFO['name'].upper()} HOME ELECTRIC", "Times-Bold", 14, "black", 0.111, 0.556)
    write_text_line(bill_canvas, "60.51  lei", "Times-Bold", 14, "black", 0.769, 0.556)
    write_text_line(bill_canvas, "Total", "Times-Bold", 10, "black", 0.15, 0.204)
    write_text_line(bill_canvas, "50.86", "Times-Bold", 10, "black", 0.670, 0.204)
    write_text_line(bill_canvas, "9.65", "Times-Bold", 10, "black", 0.825, 0.204)
    write_text_line(bill_canvas, "Total de plata, TVA inclus [Lei]", "Times-Roman", 12, "black", 0.11, 0.164)
    write_text_line(bill_canvas, "60.51", "Times-Roman", 12, "black", 0.818, 0.164)

    # Insert the text under the barcodes
    write_text_line(bill_canvas, "Cod de bare pentru factura curenta", "Times-Bold", 9, "black", 0.19, 0.05)
    write_text_line(bill_canvas, "Cod de bare pentru total de plata (sold)", "Times-Bold", 9, "black", 0.6, 0.05)

    # Insert the table containing the details about bill consumption and price calculations
    generate_table(bill_canvas, bill_details)
    
    # Create strings for barcode generation, one for the current bill and one for total payment (including overdue)
    CURRENT_BILL_VALUE_BARCODE = f"{bill_info['bill_date'].replace('.','')}{bill_info['numar']}{6051}"
    TOTAL_VALUE_BARCODE = f"{bill_info['bill_date'].replace('.','')}{bill_info['numar']}{6051}"

    # Insert the barcodes in image format in the canvas
    generate_barcode(CURRENT_BILL_VALUE_BARCODE, bill_canvas, 5)
    generate_barcode(TOTAL_VALUE_BARCODE, bill_canvas, 1.2)

    # Save the modifications for the pdf export
    bill_canvas.showPage()
    bill_canvas.save()
