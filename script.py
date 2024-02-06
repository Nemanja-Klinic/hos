import requests
from bs4 import BeautifulSoup,NavigableString

base_url = "https://www.halooglasi.com"
db_path = './products.db'
maxPrice = 450
RED = '\033[91m'
GREEN = '\033[92m'
RESET = '\033[0m'

import sqlite3

class Product:
    def __init__(self, id, title, link, price, location, image_source):
        self.id = id
        self.title = title
        self.link = link
        self.price = price
        self.location = location
        self.image_source = image_source

def create_table(cursor):
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            title TEXT,
            link TEXT,
            price TEXT ,
            location TEXT,
            image_source TEXT
        )
    ''')

def insert_product(cursor, product):
    cursor.execute('''
        INSERT INTO products (
            id, title, link, price, location, image_source
        ) VALUES (?, ?, ?, ?, ?, ?)
    ''', (product.id, product.title, product.link, product.price, product.location, product.image_source))

def fetch_products(cursor):
    cursor.execute('SELECT * FROM products')
    return cursor.fetchall()

def product_exists(cursor, product_id):
    cursor.execute('SELECT 1 FROM products WHERE id = ?', (product_id,))
    return cursor.fetchone() is not None

def clear_table(cursor):
    try:
        cursor.execute("DELETE FROM products")
        cursor.connection.commit()
    except Exception as e:
        print(f"Error while clearing the table: {e}")
        cursor.connection.rollback()

conn = sqlite3.connect(db_path)

cursor = conn.cursor()

create_table(cursor)


#CLEAR TABLE
#clear_table(cursor)

#DUMMY DATA
#sample_product = Product(1, 'product_title', 'product_link', 'product_price', 'product_location', 'product_banner_src')
#insert_product(cursor, sample_product)

conn.commit()

# products = fetch_products(cursor)
# for product in products:
#     print(product)



import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def send_email(subject, products):
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    smtp_username = "halooglasiScrapperTool@gmail.com"
    smtp_password = "kytl jjvp klct cwes"

    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta http-equiv="X-UA-Compatible" content="IE=edge">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Product Details</title>
    </head>
    <body>
        <h1>Product Details</h1>
    """

    for product in products:
        html_content += (
            f'<div style="margin-bottom: 100px; border: 1px solid gray; margin: 10px; padding: 10px;">'
            f'<h2>{product.title}</h2>'
            f'<img src="{product.image_source}" alt="Product Image" style="width: 100%;">'
            f'<div>{product.price}</div>'
            f'<div>{product.location}</div>'
            f'<small>{product.link}<small>'
            '</div>'
        )

    html_content += """
    </body>
    </html>
    """

    sender_email = "halooglasiScrapperTool@gmail.com"  # Replace with your email
    receiver_emails = ["klinicnemanja@gmail.com", "nelica.stojadinovic@gmail.com"]  # Replace with the recipient's email

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = ", ".join(receiver_emails)
    message["Subject"] = subject

    message.attach(MIMEText(html_content, "html"))

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(smtp_username, smtp_password)
        for receiver_email in receiver_emails:
          message.replace_header("To", receiver_email)
          server.sendmail(sender_email, receiver_email, message.as_string())

# Example usage
#project_info = "Details about your project..."
#send_email("Project Information", project_info)

import sqlite3
products_to_send = []

conn = sqlite3.connect(db_path)

cursor = conn.cursor()

for pageCnt in range(1, 100):
    url = f"https://www.halooglasi.com/nekretnine/izdavanje-stanova/beograd?cena_d_to={maxPrice}&page={pageCnt}"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    product_elements = soup.find_all('div', class_=lambda x: x and 'product-item' in x)

    if not len(product_elements):
        print("All the data has been processed successfully")
        break

    for div in product_elements:
        product_id = div.get('id')
        product_banner = div.select_one('figure img')
        product_title_element = div.select_one('h3.product-title')
        product_price = div.select_one('[data-value]')
        product_location = div.select_one('ul.subtitle-places')
        product_details = div.find_all('span', class_='legend')

        if product_exists(cursor, product_id):
            break

        if product_id:
            product_id = product_id
        if product_banner:
            product_banner_src = product_banner['src']
        if product_title_element:
            product_title = product_title_element.text
            product_link = base_url + product_title_element.select_one('a').get('href')
        if product_price:
            product_price = product_price.text
        else:
            product_price = 0
        if product_location:
            product_location = product_location.text
        if product_details:
            details_list = []
            for details in product_details:
                details_title = details.get_text(strip=True)
                det = details.find_parent('div')
                details_value = ''.join(det.strings).split()[0]
                details_list.append(details_value)
        product = Product(product_id, product_title, product_link, product_price, product_location, product_banner_src)
        products_to_send.append(product)
        print("----->new product found")
        insert_product(cursor, product)
    conn.commit()
    print(GREEN + f"Page {pageCnt} processed successfully." + RESET)

conn.close()

if len(products_to_send) != 0:
    send_email('Novi oglasi: ', products_to_send)
else:
    print(GREEN + "Found nothing while processing. Email not sent" + RESET)
