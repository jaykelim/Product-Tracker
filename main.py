import psycopg2
import requests
import time
import re
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
    try:
        r = requests.get(
            'https://leencustoms.com/collections/limited-releases')
        soup = BeautifulSoup(r.text, 'html.parser')
        products = soup.find_all("div", class_='grid-product__content')
        product_list = []
        for item in products:
            product_list.append((extract_data(item)))
        return product_list
    except requests.exceptions.HTTPError as errh:
        print("Http Error:", errh)
    except requests.exceptions.ConnectionError as errc:
        print("Error Connecting:", errc)
    except requests.exceptions.TooManyRedirects as errd:
        print("Too many redirects, waiting 15 seconds:", errd)
    except requests.exceptions.Timeout as errt:
        print("Timeout Error:", errt)
    except requests.exceptions.RequestException as err:
        print("OOps: Something Else", err)


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

# compares two lists


def compare(oldList, newList):
    deleteList = list(set(oldList) - set(newList))
    insertList = list(set(newList) - set(oldList))
    return deleteList, insertList


if __name__ == "__main__":
    try:
        print("Press ctrl^c to exit")
        while True:
            print("doing something here")
            p_list = get_live_products()
            db_list = get_db_list()
            delete_list, insert_list = compare(db_list, p_list)
            if len(delete_list) > 0:
                print("\nRemoving items from the list:")
                for item in delete_list:
                    print(item[0])
                delete_from_db(delete_list)

            if len(insert_list) > 0:
                print("\nInserting items into the list:")
                for item in insert_list:
                    print(item[0])

                insert_in_db(insert_list)

            for product in p_list:
                print(product[0])

            time.sleep(60)
    except KeyboardInterrupt:
        pass
