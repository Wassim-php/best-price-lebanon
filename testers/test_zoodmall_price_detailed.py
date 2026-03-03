"""Test ZoodMall price extraction with detailed logging"""
import sys
import os
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'best_price_lebanon.settings')

import django
django.setup()

from scraping.adapters.websites.zoodmall import ZoodMallAdapter
from bs4 import BeautifulSoup

adapter = ZoodMallAdapter()
product_url = 'https://www.zoodmall.com.lb/en/product/35484455/samsung-galaxy-a56-ctc-256g8ram-with-one-year-warranty-gift/'

print("\n" + "="*70)
print("TESTING ZOODMALL PRICE EXTRACTION")
print("="*70)
print(f"Product: {product_url}\n")

# Get the pricing
result = adapter.get_detailed_pricing(product_url, 'outside beirut')

print("RESULT:")
print(f"  Base Price: ${result['base_price']}")
print(f"  Shipping: ${result['shipping_fee']}")
print(f"  Total: ${result['total_price']}")
print(f"  Delivery: {result['delivery_time']}")

# Also manually check the HTML to see what prices are there
print("\n" + "-"*70)
print("MANUAL HTML INSPECTION:")
print("-"*70)

adapter.driver.get(product_url)
import time
time.sleep(5)
html = adapter.driver.page_source
soup = BeautifulSoup(html, 'html.parser')

# Find all price elements
price_un_sale = soup.find('span', class_='price__un_sale')
price_actual = soup.find('span', class_='price__actual')
price_sale = soup.find('span', class_='price__sale')

if price_un_sale:
    print(f"✓ price__un_sale: {price_un_sale.get_text(strip=True)}")
if price_actual:
    classes = price_actual.get('class', [])
    print(f"✓ price__actual (classes: {classes}): {price_actual.get_text(strip=True)}")
if price_sale:
    print(f"✓ price__sale (crossed out): {price_sale.get_text(strip=True)}")

print("\n" + "="*70 + "\n")
