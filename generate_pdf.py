"""
This module contains functions for generating and customizing PDF invoices 
for the Greenergy company.

The module provides the following functions:

    set_pdf_name: Set the PDF file name based on the bill serial and number.
    draw_img: Inserts an image within the canvas.
    write_text_line: Inserts line of texts in the pdf page.
    generate_table: Inserts a table within the canvas.
    generate_barcode: Inserts a barcode
    generate_pdf_bill: The main function, that uses all the other functions
        and works with the data coming from database to create the format 
        and design of the pdf invoice
    
Please note that this module requires the following external libraries:
    
    reportlab: A library for generating PDF documents.
    
For more information, refer to the README file.
"""

import logging
import os
from pathlib import Path

from reportlab.graphics.barcode import code128
from reportlab.lib.colors import black, green, lightgrey, white, whitesmoke
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import cm
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Table, TableStyle

from db_interaction import LINE_SEPARATOR

# setting up logging configurations and handlers
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

file_handler = logging.FileHandler('logs/main.log')
file_handler.setLevel(logging.ERROR)
file_handler.setFormatter(log_formatter)

logger.addHandler(file_handler)

# Set the root folder path and icons folder path
MAIN_FOLDER_ROOT = Path(__file__).parent
ICONS_PATH = MAIN_FOLDER_ROOT / "icons"

# Define the page size and get the width and height values by tuple unpacking
PAGE_SIZE = LETTER
P_WIDTH, P_HEIGHT = PAGE_SIZE

# File paths for the logo and the icon images used in the application
COMPANY_LOGO_FILE = "greenergy_icon.png"
LOCATION_ICON_FILE = "location_icon.png"
PHONE_ICON_FILE = "phone_icon.png"
EMAIL_ICON_FILE = "email_icon.png"

# Dictionary that stores information about the electrical company
COMPANY_INFO = {
    "name": "Greenergy",
    "street": "Bulevardul Ion C. Bratianu nr. 44",
    "city": "Bucuresti",
    "country": "Romania",
    "phone": "021-336 5503",
    "email": "contact@greenergy.ro"
}

def set_pdf_name(bill_serial: str, bill_number: str):
    """
    Set the PDF file name based on the bill serial and number.

    Args:
        bill_serial (str): The bill serial number.
        bill_number (str): The bill number.

    Returns:
        str: The PDF file name.

    Raises:
        OSError: If there is an error creating the directory for PDF bills.
    """
    logger.info("Setting PDF file name for bill: %s-%s", bill_serial, bill_number)
    pdf_name = (f"factura_{COMPANY_INFO['name'].lower()}"
                f"_{bill_serial}-{bill_number}.pdf")
    pdf_bills_folder = MAIN_FOLDER_ROOT / "Facturi generate" / bill_serial
    try:
        if not os.path.exists(pdf_bills_folder):
            os.makedirs(pdf_bills_folder)
            logger.info("PDF bills folder created: %s", str(pdf_bills_folder))
    except OSError as oserr:
        logger.error("OSError occurred while creating the PDF bills folder: %s",
                     str(pdf_bills_folder))
        print(LINE_SEPARATOR)
        error_msg = f"Eroare la crearea folderului {str(pdf_bills_folder)}!"
        raise OSError(error_msg) from oserr
    return str(pdf_bills_folder / pdf_name)

def draw_img(
        canvas: Canvas, file_path: str, x_origin: float, y_origin: float,
        img_width: float, img_height: float):
    """
    Inserts an image within a canvas.

    Args:
        canvas (Canvas): The canvas where the image will be inserted.
        file_path (str): The path to the image file that will be inserted.
        x_origin (float): The x-coord. from bottom-left corner of the image.
        y_origin (float): The y-coord. from bottom-left corner of the image.
        img_width (float): The width of the image.
        img_height (float): The height of the image.

    Raises:
        ValueError: Invalid values for float arguments.
        OSError: If the specified file cannot be accessed or opened.
        TypeError: If any of the arguments is not of expected type.
        Exception: If any other unexpected error occurs during the execution.
    """
    logger.info("Inserting image: %s", file_path)
    if (not 0 <= x_origin <= 1 or not 0 <= y_origin <= 1
            or not 0 <= img_width <= 1 or not 0 <= img_height <= 1):
        raise ValueError(
            "Pozitia/dimensiunea trebuie sa fie de tip float (0-1).")
    canvas.drawImage(file_path, x_origin * P_WIDTH, y_origin * P_HEIGHT,
                     img_width * P_WIDTH, img_height * P_HEIGHT, "auto")
    logger.info("Image inserted successfully.")

def write_text_line(
        canvas: Canvas, text: str, font: str, size: int, text_color: str,
        x_value: float, y_value: float):
    """
    Writes a single line of text on the given canvas at specified coordinates.

    Args:
        canvas (Canvas): The canvas object on which to write the text.
        text (str): The text to be written.
        font (str): The font to be used for the text, e.g. "Times-Roman".
        size (int): The font size of the text, float accepted, e.g. "10".
        text_color (str): The color of the text (needs to be imported)
        x_value (float): The x-coordinate of the starting position of the text.
        y_value (float): The y-coordinate of the baseline position of the text.
    Raises:
        ValueError: If any of the float arguments (x, y) have invalid values.
        AttributeError: If the specified argument for text is not string.
        TypeError: If any of the arguments is not of expected type.
        KeyError: If the specified font does not exist in the library.
        Exception: If any other unexpected error occurs during the execution.
    """
    logger.info("Writing text: %s", text)
    if not 0 <= x_value <= 1 or not 0 <= y_value <= 1:
        raise ValueError(
            "Pozitia/dimensiunea trebuie sa fie de tip float (0-1).")
    canvas.setFont(font, size)
    canvas.setFillColor(text_color)
    canvas.drawString(x_value * P_WIDTH, y_value * P_HEIGHT, text)
    logger.info("Text written successfully.")

def generate_table(canvas: Canvas, content: dict):
    """
    Generates a table on a canvas based on the provided content.

    Args:
        canvas: The canvas object on which to draw the table.
        content (dict): A dictionary containing the table data.

    Raises:
        TypeError: If the arguments are not of expected type.
        KeyError: If the `content` dictionary does not have the required keys.
        ValueError: If any invalid values result for column/row dimensions.
        Exception: If any other unexpected error occurs during the execution.
    """
    logger.info("Generating table.")
    headers = list(content.keys())
    rows = list(zip(*content.values()))
    data = [headers] + rows

    # create the table given the columns width and rows height
    col_widths = [0.15 * P_WIDTH, 0.1 * P_WIDTH, 0.1 *
                  P_WIDTH, 0.15 * P_WIDTH, 0.15 * P_WIDTH, 0.15 * P_WIDTH]
    row_heights = [0.058 * P_HEIGHT, 0.045 * P_HEIGHT,
                   0.045 * P_HEIGHT, 0.045 * P_HEIGHT, 0.045 * P_HEIGHT]
    table = Table(data, rowHeights=row_heights, colWidths=col_widths)
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
    table.setStyle(TableStyle(table_style))
    table.wrapOn(canvas, P_WIDTH * 0.75, P_HEIGHT)
    x_value = 0.1 * P_WIDTH
    y_value = 0.238 * P_HEIGHT
    table.drawOn(canvas, x_value, y_value)
    logger.info("Table generated successfully.")

def generate_barcode(
        canvas: Canvas, barcode_value: str, x_position: float,
        y_position: float):
    """
    Generates a barcode on a canvas at the specified position.

    Args:
        canvas: The canvas object on which to draw the barcode.
        barcode_value (str): The value of the barcode to be generated.
        canvas_object (Canvas): The canvas object on which to draw the barcode.
        x (float): The factor for adjusting the x position of the barcode.

    Raises:
        TypeError: If the arguments are not of expected type.
        ValueError: If any of the float arguments have invalid values.
    """
    logger.info("Generating barcode.")
    try:
        if not isinstance(canvas, Canvas):
            raise TypeError(
                "Parametrul 'canvas' trebuie sa fie de tipul Canvas.")
        canvas.setFillColor("black")
        bill_barcode = code128.Code128(
            barcode_value, barWidth=1, barHeight=1 * cm, humanReadable=True)
        bill_barcode.drawOn(canvas, (P_WIDTH - bill_barcode.width) / x_position,
                            y_position * P_HEIGHT)
        logger.info("Barcode generated successfully.")
    except TypeError as terr:
        logger.error("TypeError occurred: %s", terr)
        print(f"Eroare: {terr}")
        raise terr
    except ValueError as verr:
        logger.error("ValueError occurred: %s", str(verr))
        print(f"Eroare: {verr}")
        raise verr

def generate_pdf_bill(
        file_name: str, client_info: dict, bill_info: dict, bill_details: dict):
    """
    Generates a PDF bill document based on the provided information.

    Args:
        file_name (str): The name of the PDF file to be generated.
        client_info (dict): A dictionary containing info about the client.
        bill_info (dict): A dictionary containing info about the bill.
        bill_details (dict): A dictionary containing the consumption details.

    Raises:
        TypeError: If the arguments are not of the expected type.
        ValueError: If the float argument has invalid value.
    """
    try:
        # Create a canvas object with the given file_name and pagesize
        bill_canvas = Canvas(file_name, pagesize=PAGE_SIZE)

        # Insert the logo and different icons in the canvas
        draw_img(bill_canvas, ICONS_PATH / COMPANY_LOGO_FILE,
                 0.645, 0.8, 0.159, 0.143)
        draw_img(bill_canvas, ICONS_PATH / LOCATION_ICON_FILE,
                 0.111, 0.862, 0.011, 0.014)
        draw_img(bill_canvas, ICONS_PATH / PHONE_ICON_FILE,
                 0.111, 0.826, 0.011, 0.013)
        draw_img(bill_canvas, ICONS_PATH / EMAIL_ICON_FILE,
                 0.111, 0.806, 0.014, 0.007)

        # Insert horizontal lines/rectangle to visually separate the content
        bill_canvas.setStrokeColor(lightgrey)
        bill_canvas.setFillColor(lightgrey)
        bill_canvas.line(0.1 * P_WIDTH, 0.578 * P_HEIGHT, 0.9 * P_WIDTH,
                         0.578 * P_HEIGHT)
        bill_canvas.line(0.1 * P_WIDTH, 0.233 * P_HEIGHT, 0.9 * P_WIDTH,
                         0.233 * P_HEIGHT)
        bill_canvas.rect(0.1 * P_WIDTH, 0.154 * P_HEIGHT, 0.8 * P_WIDTH,
                         0.028 * P_HEIGHT, fill=1)

        # Insert the information text about the company
        write_text_line(bill_canvas, COMPANY_INFO["name"], "Times-Roman",
                        25, "green", 0.143, 0.926)
        write_text_line(bill_canvas, COMPANY_INFO["street"], "Times-Roman",
                        12, "black", 0.143, 0.877)
        write_text_line(bill_canvas, COMPANY_INFO["city"], "Times-Roman",
                        12, "black", 0.143, 0.862)
        write_text_line(bill_canvas, COMPANY_INFO["country"], "Times-Roman",
                        12, "black", 0.143, 0.847)
        write_text_line(bill_canvas, COMPANY_INFO["phone"], "Times-Roman",
                        12, "black", 0.143, 0.826)
        write_text_line(bill_canvas, COMPANY_INFO["email"], "Times-Roman",
                        12, "black", 0.143, 0.806)

        # Insert the information about the current bill
        write_text_line(bill_canvas, "Factura fiscala", "Times-Bold", 13,
                        "black", 0.625, 0.741)
        write_text_line(bill_canvas,
                        f"Seria {bill_info['bill_serial']} nr. "
                        f"{bill_info['bill_number']}",
                        "Times-Roman", 12, "black", 0.625, 0.719)
        write_text_line(bill_canvas, bill_info['bill_generated_date'],
                        "Times-Roman", 12, "black", 0.746, 0.699)
        write_text_line(bill_canvas, bill_info['bill_due_date'], "Times-Roman",
                        12, "black", 0.758, 0.680)
        write_text_line(bill_canvas,
                        f"{bill_info['bill_start_date']} - "
                        f"{bill_info['bill_end_date']}",
                        "Times-Roman", 12, "black", 0.625, 0.643)
        write_text_line(bill_canvas, "Data facturii:", "Times-Bold", 12,
                        "black", 0.625, 0.699)
        write_text_line(bill_canvas, "Data scadenta:", "Times-Bold", 12,
                        "black", 0.625, 0.680)
        write_text_line(bill_canvas, "Perioada de facturare:", "Times-Bold",
                        12, "black", 0.625, 0.662)

        # Insert the information about the client
        write_text_line(bill_canvas, client_info["name"].upper(), "Times-Bold",
                        13, "black", 0.143, 0.741)
        write_text_line(bill_canvas, client_info["street"], "Times-Roman", 12,
                        "black", 0.143, 0.719)
        write_text_line(bill_canvas,
                        f"{client_info['zipcode']}, {client_info['city'].upper()}, "
                        f"Judetul {client_info['county']}",
                        "Times-Roman", 12, "black", 0.143, 0.699)
        write_text_line(bill_canvas, f"Cod client: {client_info['id']}",
                        "Times-Roman", 12, "black", 0.143, 0.680)

        # Insert the information about the bill value
        write_text_line(bill_canvas, "Detalii factura curenta:", "Times-Bold",
                        24, "green", 0.111, 0.588)
        write_text_line(bill_canvas, "Din ce este compus consumul tau?",
                        "Times-Bold", 15, "green", 0.111, 0.500)
        write_text_line(bill_canvas,
                        f"{COMPANY_INFO['name'].upper()} HOME ELECTRIC",
                        "Times-Bold", 14, "black", 0.111, 0.556)
        write_text_line(bill_canvas, f"{bill_info['total_bill_value']:.2f}  lei",
                        "Times-Bold", 14, "black", 0.769, 0.556)
        write_text_line(bill_canvas, "Total", "Times-Bold",
                        10, "black", 0.15, 0.204)
        write_text_line(bill_canvas, f"{bill_info['total_fara_tva']:.2f}",
                        "Times-Bold", 10, "black", 0.657, 0.204)
        write_text_line(bill_canvas, f"{bill_info['total_tva']:.2f}",
                        "Times-Bold", 10, "black", 0.813, 0.204)
        write_text_line(bill_canvas, "Total de plata, TVA inclus [Lei]",
                        "Times-Roman", 12, "black", 0.11, 0.164)
        write_text_line(bill_canvas, f"{bill_info['total_bill_value']:.2f}",
                        "Times-Roman", 12, "black", 0.808, 0.164)

        # Insert the text under the barcodes
        write_text_line(bill_canvas, "Cod de bare pentru factura curenta",
                        "Times-Bold", 9, "black", 0.165, 0.05)
        write_text_line(bill_canvas, "Cod de bare pentru total de plata (sold)",
                        "Times-Bold", 9, "black", 0.6, 0.05)

        # Insert the table containing the details about consumption and prices
        generate_table(bill_canvas, bill_details)

        # Create strings for barcode generation
        current_bill_barcode = (
            f"{bill_info['bill_number']}{bill_info['total_bill_value']:.2f}")
        total_value_barcode = (
            f"{bill_info['bill_number']}{bill_info['total_bill_value']:.2f}")

        # Insert the barcodes in image format in the canvas
        generate_barcode(bill_canvas, current_bill_barcode, 6, 0.085)
        generate_barcode(bill_canvas, total_value_barcode, 1.2, 0.085)

        # Save the modifications for the pdf export
        bill_canvas.showPage()
        bill_canvas.save()
        print("-" * 65)
        print("Factura a fost generata cu succes!")
    except AttributeError as aerr:
        logger.exception(aerr)
        print(LINE_SEPARATOR)
        print(aerr)
    except TypeError as terr:
        logger.exception(terr)
        print(LINE_SEPARATOR)
        print(terr)
    except ValueError as verr:
        logger.exception(verr)
        print(LINE_SEPARATOR)
        print(verr)
    except KeyError as kerr:
        logger.exception(kerr)
        print(LINE_SEPARATOR)
        print(kerr)
    except OSError as oserr:
        logger.exception(oserr)
        print(LINE_SEPARATOR)
        print(oserr)
