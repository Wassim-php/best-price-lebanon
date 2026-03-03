"""Check what HTML Selenium actually sees"""
import sys
import os
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'best_price_lebanon.settings')

import django
django.setup()

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import time

chrome_options = Options()
chrome_options.add_argument('--headless=new')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--disable-gpu')

service = Service('/usr/local/bin/chromedriver')
driver = webdriver.Chrome(service=service, options=chrome_options)

url = 'https://www.zoodmall.com.lb/en/product/35484455/samsung-galaxy-a56-ctc-256g8ram-with-one-year-warranty-gift/'
print(f"\nLoading: {url}\n")

driver.get(url)
time.sleep(10)  # Wait longer

html = driver.page_source

# Check what's in the HTML
print(f"HTML Length: {len(html)} bytes")
print()

# Search for key strings
searches = ['375', '409', '425', 'USD', 'price__', 'product-price', 'price__actual', 'price__sale', 'price__un_sale']
for term in searches:
    count = html.lower().count(term.lower())
    if count > 0:
        print(f"✓ Found '{term}': {count} times")
    else:
        print(f"✗ NOT found: '{term}'")

print()

# Find any element with "price" in class
import re
price_classes = re.findall(r'class="[^"]*price[^"]*"', html, re.I)
unique_classes = set(price_classes[:20])
if unique_classes:
    print(f"Price-related classes found ({len(unique_classes)} unique):")
    for cls in list(unique_classes)[:10]:
        print(f"  {cls}")
else:
    print("No price-related classes found")

driver.quit()
