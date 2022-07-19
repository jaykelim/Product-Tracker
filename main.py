import psycopg2
import requests
import time
from bs4 import BeautifulSoup
from config import MYSQL

# Extract relevant data from element set


def extract_data(item):
    p_name = item.find(
        "div", class_='grid-product__title grid-product__title--body').text
    p_stock = not bool(item.select("div[class*='sold-out']"))
    p_url = "https://leencustoms.com/"+item.find("a")['href']
    p_price = item.find("div", class_='grid-product__price').text[0:-1]
    str = item.find("div", {
                    "class": "grid__image-ratio grid__image-ratio--square lazyload"})['data-bgset']
    p_image = re.findall('//(.+?) ', str)[2]
    return p_name, p_stock, p_url, p_price, p_image

# Retrieves the current products from website


def get_live_products() -> list:
    r = requests.get('https://leencustoms.com/collections/limited-releases')
    soup = BeautifulSoup(r.text, 'html.parser')
    products = soup.find_all("div", class_='grid-product__content')
    product_list = []
    for item in products:
        product_list.append((organize_data(item)))
    return product_list


# Retrieves the current table in DB
def get_db_list() -> list:
    con = psycopg2.connect(host=MYSQL.HOST,
                           port=MYSQL.PORT,
                           user=MYSQL.USER,
                           password=MYSQL.PASSWORD,
                           database="leen_customs_limited_pins")
    # Get a database cursor
    cur = con.cursor()
    # Select all rows from products table
    cur.execute("""
      SELECT * FROM leen_products
      """)
    products = cur.fetchall()
    cur.close()
    con.close()
    return products


if __name__ == "__main__":
    try:
        while True:
            print("Press ctrl^c to exit")
            time.sleep(5)
    except KeyboardInterrupt:
        pass
