import psycopg2
import requests
import time
import re
import sms
from time import strftime
from bs4 import BeautifulSoup
from config import INFO
from datetime import datetime
from pytz import timezone

# Extract relevant data from element set

refresh_rate = 30


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
    con = psycopg2.connect(host=INFO.HOST,
                           port=INFO.PORT,
                           user=INFO.USER,
                           password=INFO.PASSWORD,
                           database="leen_customs_limited_pins")
    # Get a database cursor
    cur = con.cursor()
    # Select all rows from products table
    try:
        cur.execute("""
      SELECT * FROM leen_products
      """)
        products = cur.fetchall()
    except:
        print("Could not fetch data from db")
        sms.send("Could not fetch data from db")
    finally:
        cur.close()
        con.close()
    return products

# compares two lists


def compare(oldList, newList):
    fmt = "%Y-%m-%d %H:%M:%S"
    now_time = datetime.now(timezone('US/Eastern'))
    print("\n(" + now_time.strftime(fmt) +
          ") Comparing old list vs new list...")
    deleteList = list(set(oldList) - set(newList))
    insertList = list(set(newList) - set(oldList))
    print("# of deletes:", len(deleteList))
    print("# of inserts:", len(insertList))
    return deleteList, insertList


def delete_from_db(delete_list):
    con = psycopg2.connect(host=MYSQL.HOST,
                           port=MYSQL.PORT,
                           user=MYSQL.USER,
                           password=MYSQL.PASSWORD,
                           database="leen_customs_limited_pins")
    # Get a database cursor
    cur = con.cursor()
    # Select all rows from products table
    for product in delete_list:
        prod_url = product[2]
        print("deleting: "+prod_url)
        cur.execute("""
          DELETE FROM leen_products WHERE url = %s""",
                    (
                        prod_url
                    )
                    )

    con.commit()
    cur.close()
    con.close()


def insert_in_db(insert_list):
    con = psycopg2.connect(host=MYSQL.HOST,
                           port=MYSQL.PORT,
                           user=MYSQL.USER,
                           password=MYSQL.PASSWORD,
                           database="leen_customs_limited_pins")
    # Get a database cursor
    cur = con.cursor()
    # Select all rows from products table
    for product in insert_list:
        #p_name, p_stock, p_url, p_price, p_image = extract_data(product)
        cur.execute("""
        INSERT INTO leen_products (name, stock, url, price, image_url)
        VALUES (%s, %s, %s, %s, %s)
        """,
                    (
                        product[0],
                        product[1],
                        product[2],
                        product[3],
                        product[4]
                    )
                    )

    con.commit()
    cur.close()
    con.close()


if __name__ == "__main__":
    try:
        print("Press ctrl^c to exit")
        while True:
            p_list = get_live_products()
            db_list = get_db_list()
            delete_list, insert_list = compare(db_list, p_list)
            if len(delete_list) > 0:
                print("\nRemoving items from the list:")
                for item in delete_list:
                    print(item[0])
                    sms.send("New item added: "+item[2])
                delete_from_db(delete_list)

            if len(insert_list) > 0:
                print("\nInserting items into the list:")
                for item in insert_list:
                    print(item[0])
                insert_in_db(insert_list)

            # for product in p_list:
            #     print(product[0])

            time.sleep(refresh_rate)
    except Exception():
        sms.send("error: ")
    except KeyboardInterrupt:
        pass
