"""Inspect Samsung A56 product page price structure"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import time
from bs4 import BeautifulSoup

# Initialize Chrome (local)
chrome_options = Options()
chrome_options.add_argument('--headless=new')

driver = webdriver.Chrome(options=chrome_options)

url = 'https://www.zoodmall.com.lb/en/product/35484455/samsung-galaxy-a56-ctc-256g8ram-with-one-year-warranty-gift/'
print(f"\nLoading: {url}\n")

driver.get(url)
time.sleep(5)  # Wait for page to load

html = driver.page_source
soup = BeautifulSoup(html, 'html.parser')

print("="*70)
print("ALL PRICE ELEMENTS:")
print("="*70)

# Find all elements with 'price' in class
price_elements = soup.find_all(class_=lambda x: x and 'price' in str(x).lower())

for i, elem in enumerate(price_elements, 1):
    classes = elem.get('class', [])
    text = elem.get_text(strip=True)
    print(f"\n{i}. Tag: <{elem.name}> Classes: {classes}")
    print(f"   Text: {repr(text[:80])}")
    
    # Check for strikethrough/crossed out styling
    style = elem.get('style', '')
    if 'line-through' in style or 'strikethrough' in style:
        print(f"   ⚠ HAS LINE-THROUGH STYLE")
    
    # Check parent for strikethrough
    if elem.parent:
        parent_style = elem.parent.get('style', '')
        if 'line-through' in parent_style:
            print(f"   ⚠ PARENT HAS LINE-THROUGH")

driver.quit()

# Also check the HTML structure
print("\n" + "="*70)
print("PRICE CONTAINER STRUCTURE:")
print("="*70)

soup2 = BeautifulSoup(html, 'html.parser')
product_price = soup2.find('div', class_='product-price')
if product_price:
    print("\n<div class='product-price'>")
    for child in product_price.children:
        if hasattr(child, 'name') and child.name:
            classes = child.get('class', [])
            text = child.get_text(strip=True)[:50]
            print(f"  <{child.name} class='{' '.join(classes)}'>{text}</{child.name}>")
    print("</div>")

print("\n" + "="*70 + "\n")
