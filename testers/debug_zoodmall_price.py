"""Debug ZoodMall price extraction to see actual HTML elements"""
import sys
import os
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'best_price_lebanon.settings')

import django
django.setup()

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from bs4 import BeautifulSoup
import re

# Initialize Chrome
chrome_options = Options()
chrome_options.add_argument('--headless=new')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--disable-blink-features=AutomationControlled')

service = Service('/usr/local/bin/chromedriver')
driver = webdriver.Chrome(service=service, options=chrome_options)

# Load the product page
url = 'https://www.zoodmall.com.lb/en/product/35484455/samsung-galaxy-a56-ctc-256g8ram-with-one-year-warranty-gift/'
print(f"\n{'='*70}")
print(f"Loading: {url}")
print(f"{'='*70}\n")

driver.get(url)

# Wait for price to load
try:
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "span.price__actual, div.product-price"))
    )
    time.sleep(2)
    print("✓ Page loaded successfully\n")
except:
    print("⚠ Timeout waiting for price\n")

# Get HTML
html = driver.page_source
soup = BeautifulSoup(html, 'html.parser')

# Find price elements
print("PRICE ELEMENTS FOUND:")
print("-" * 70)

# Check price__actual
price_actual = soup.find('span', class_='price__actual')
if price_actual:
    print(f"✓ Found span.price__actual")
    print(f"  Classes: {price_actual.get('class')}")
    print(f"  Raw text: {repr(price_actual.get_text())}")
    print(f"  Stripped text: {repr(price_actual.get_text(strip=True))}")
    
    # Try extraction
    price_text = price_actual.get_text(strip=True)
    price_text = price_text.replace('USD', '').replace('$', '').strip()
    match = re.search(r'([\d,]+\.?\d*)', price_text.replace(',', ''))
    if match:
        print(f"  ✓ Extracted price: {match.group(1)}")
    else:
        print(f"  ✗ No match found")
else:
    print("✗ No span.price__actual found")

print()

# Check product-price
product_price = soup.find('div', class_='product-price')
if product_price:
    print(f"✓ Found div.product-price")
    print(f"  Classes: {product_price.get('class')}")
    print(f"  Raw text: {repr(product_price.get_text())}")
    print(f"  Stripped text: {repr(product_price.get_text(strip=True))}")
else:
    print("✗ No div.product-price found")

print()

# Look for all price-related classes
print("ALL ELEMENTS WITH 'price' IN CLASS:")
print("-" * 70)
all_prices = soup.find_all(class_=lambda x: x and 'price' in str(x).lower())
for i, elem in enumerate(all_prices[:10], 1):
    print(f"{i}. Tag: {elem.name}, Classes: {elem.get('class')}")
    text = elem.get_text(strip=True)[:60]
    print(f"   Text: {repr(text)}")

driver.quit()
print(f"\n{'='*70}\n")
