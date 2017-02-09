"""
Amazon market lookup tool.  Written by David Wolf and Robert Voorheis
Version 0.1
"""

import pdb
import os
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import InvalidElementStateException
from selenium.common.exceptions import ElementNotVisibleException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import sqlite3
import re
import time
# make the script directory into the working directory
#abspath = os.path.abspath(__file__)
#dname = os.path.dirname(abspath)

os.chdir("Z:\\Independent Buyers\\Analysis\\Python\\")

condition_abbreviations = {
    "Used - Acceptable": "A",
    "Used - Very Good": "VG",
    "Used - Good": "G",
    "Used - Like New": "LN",
    "New": "N"
}


db = sqlite3.connect(':memory:')
c = db.cursor()
db.execute('''
    CREATE TABLE listings (
        isbn TEXT,
        listings_page INTEGER,
        position_in_page INTEGER,
        listing_id REAL,
        price_base REAL,
        price_shipping REAL,
        price_total REAL,
        condition TEXT,
        seller_id TEXT
        )''')

db.execute('''
    CREATE TABLE sellers (
        seller_id TEXT,
        seller_name TEXT,
        seller_rating_percentage REAL,
        seller_total_ratings REAL
        )
        ''')

db.execute('''
    CREATE TABLE cart (
        listing_id REAL,
        qty INTEGER
        )
    ''')

def ISBN_13_to_10(ISBN_13):
    s = 0
    for i, digit in zip(range(1,10), ISBN_13[3:-1]):
        s += (11-i) * int(digit)
        s %= 11
    check_digit = 11 - s
    return '{}{}'.format(ISBN_13[3:-1],check_digit)
        
def marketplace_scrape(isbn, page, maxprice=9999):
    time.sleep(0.5)
    listings = driver.find_elements_by_class_name('olpOffer')
    listingstoadd = []
    for ordinal, listing in zip(range(1000), listings):  # 1000 is arbitrarily large; zip stops at shorter of two lists
#        print(listing.text)
        try:
            listingid = listing.find_element_by_name("offeringID.1").get_attribute("value")
        except StaleElementReferenceException as e:
            print(e)
            continue
        
        c.execute("SELECT * FROM listings WHERE listing_id = ?", (listingid,))
        if len(c.fetchall()) > 0:
            continue
        try:
            pricebase = float(listing.find_element_by_class_name('olpOfferPrice').text.replace('$','').replace(',',''))
        except StaleElementReferenceException as e:
            print(e)
            continue
        if re.search("FREE", listing.find_element_by_class_name('olpShippingInfo').text):
            priceshipping=0.0
        else:
            priceshipping = float(listing.find_element_by_class_name('olpShippingPrice').text.replace('$',''))
        pricetotal = pricebase + priceshipping
        condition = condition_abbreviations[listing.find_element_by_class_name('olpCondition').text]
        sellerid = listing.find_element_by_class_name('olpSellerName').find_element_by_tag_name('a').get_attribute('href')[-14:]
        sellername = listing.find_element_by_class_name('olpSellerName').text
        print(sellername)
        seller_percent_text = listing.find_element_by_class_name('olpSellerColumn').find_element_by_tag_name('b').text
        if re.search("Just Launched", seller_percent_text):
            sellerpercent = 0
            sellerratings = 0
        else:
            sellerpercent = float(listing.find_element_by_class_name('olpSellerColumn').find_element_by_tag_name('b').text[:2].strip('%')) / 100
            sellerratings = int(listing.find_element_by_class_name('olpSellerColumn').text.split('. (')[1].split(' ')[0].replace(',',''))
        listingstoadd.append(ordinal)
        db.execute('INSERT INTO listings VALUES (?,?,?,?,?,?,?,?,?)', (isbn, page, ordinal, listingid, pricebase, priceshipping, pricetotal, condition, sellerid))

        c.execute("SELECT * FROM sellers WHERE seller_id =?",(sellerid,))
        if len(c.fetchall()) > 0: continue

        db.execute('INSERT INTO sellers VALUES (?,?,?,?)', (sellerid, sellername, sellerpercent, sellerratings))
    return listingstoadd


def addtocart(values):
    ordinal = 0
    count = 0
    while count < len(values):
#        pdb.set_trace()
        buttons = WebDriverWait(driver,10).until(EC.presence_of_all_elements_located((By.NAME,'submit.addToCart')))

        submit_button = buttons[ordinal]
        ordinal +=1
        if submit_button.is_displayed() == False:
            continue
        submit_button.click()
        count+=1
        time.sleep(0.5)
        driver.execute_script('window.history.go(-1)')
        time.sleep(0.5)



def countcart():
    items = driver.find_elements_by_class_name('sc-list-item-content')
    for i in range(len(items)):
        items = driver.find_elements_by_class_name('sc-list-item-content')
        item = items[i]
        listingid = item.find_element_by_xpath('..').get_attribute('data-encoded-offering')
        
        try:
            qty = int(item.find_element_by_class_name('sc-product-scarcity').text.split('Only ')[1].split(' left')[0])
        
        except NoSuchElementException:
            
            select = Select(item.find_element_by_tag_name('select'))
            
            try:
                select.select_by_value("10")
                qtyfield = item. find_element_by_name('quantityBox')
                qtyfield.clear()
                qtyfield.send_keys('999' + Keys.ENTER)
                time.sleep(2)
                items = driver.find_elements_by_class_name('sc-list-item-content')
                item = items[i]
                qty = int(item.find_element_by_class_name("a-alert-content").text.split("only ")[1].split(" of these")[0])
            except InvalidElementStateException:
                items = driver.find_element_by_id('activeCartViewForm').find_element_by_class_name(
                    'sc-list-body').find_elements_by_class_name('sc-list-item-content')

                item = items[i]
                select = Select(item.find_element_by_tag_name('select'))
                select.select_by_value("10")
                qty = int(select.all_selected_options[0].text)
            #qty = int(item.find_element_by_class_name('a-size-base').text.split('limit of ')[1].split(' per ')[0])
        db.execute('INSERT INTO cart VALUES (?,?)', (listingid, qty))

def clear_cart():
    more_items = True
    while more_items:
        try:
            driver.find_element_by_xpath("//input[@value='Delete']").click()
            time.sleep(0.5)
        except NoSuchElementException:
            more_items = False
        except WebDriverException:
            continue

#chromedriverpath = 'Z:\\Independent Buyers\\Analysis\\Python\\chromedriver.exe'
#driver = webdriver.Chrome(executable_path=chromedriverpath)
geckodriverpath = 'Z:\\Independent Buyers\\Analysis\\Python\\geckodriver.exe'
driver = webdriver.Firefox(executable_path=geckodriverpath)
isbns = []

with open('books.csv') as csv:
    for row in csv:
        isbns.append(row.strip('\n'))

f = open('output.txt','w')
for isbn in isbns:
    if len(isbn) == 13:
        isbn = ISBN_13_to_10(isbn)
    if len(isbn) != 10:
        f.write('{} is not a valid ISBN'.format(isbn))
        f.write('\n')
        continue
    max_pages = 5
    maxprice = 100
    page = 1
    more_pages = True
    listingsurl = 'https://www.amazon.com/gp/offer-listing/{}/ref=olp_f_used?f_usedGood=true&f_usedLikeNew=true&f_usedVeryGood=true&f_new=true'.format(isbn)
    driver.get(listingsurl)
    page_count = 0
    while more_pages and page_count < max_pages:
        page_count+=1
        time.sleep(0.5)
        listings_to_add = []
        while listings_to_add == []:
            listings_to_add = marketplace_scrape(isbn, listingsurl)
        print(listings_to_add)
        addtocart(listings_to_add)
        try:
            last = driver.find_element_by_class_name('a-last')
            if "a-disabled" in last.get_attribute('class'):
                more_pages = False
            else:
                last.click()
        except NoSuchElementException as e:
            print(e)
            more_pages = False
        
    driver.get('https://www.amazon.com/gp/cart/view.html')
    countcart()
    clear_cart()
    c = db.cursor()
    c.execute("""SELECT isbn, seller_name, condition, qty, price_base
                   FROM listings
                   JOIN cart
                     ON listings.listing_id = cart.listing_id
                   JOIN sellers
                     ON listings.seller_id = sellers.seller_id
                  WHERE listings.isbn = ?""",(isbn,))

    
    f.write(isbn)
    f.write('\n')
    for row in c.fetchall():
        f.write(",".join([str(x) for x in row]))
        f.write('\n')
    c.execute("SELECT * FROM listings")
    c.execute("SELECT * FROM cart")
    c.execute("SELECT * FROM sellers")

    f.write('\n')
    
f.close()
driver.close()