"""Save ZoodMall HTML to file for inspection"""
from scraping.adapters.websites.zoodmall import ZoodMallAdapter
from urllib.parse import quote

adapter = ZoodMallAdapter()

search_url = f"https://www.zoodmall.com.lb/en/search/?q={quote('iphone')}"
print(f"Loading: {search_url}")

adapter.driver.get(search_url)
import time
time.sleep(10)  # Wait for JS to load

html = adapter.driver.page_source

# Save to file
with open('/app/zoodmall_page.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("HTML saved to /app/zoodmall_page.html")
print(f"HTML length: {len(html)} characters")

# Check what we can find
from bs4 import BeautifulSoup
soup = BeautifulSoup(html, 'html.parser')

print("\n--- Checking for product elements ---")
print(f"<a class='product-mini'>: {len(soup.find_all('a', class_='product-mini'))}")
print(f"<div class='product-card'>: {len(soup.find_all('div', class_='product-card'))}")
print(f"<div class='product-item'>: {len(soup.find_all('div', class_='product-item'))}")
print(f"<div class='product-item-list'>: {len(soup.find_all('div', class_='product-item-list'))}")

# List all unique classes with "product" in them
all_classes = set()
for tag in soup.find_all(class_=True):
    for cls in tag.get('class', []):
        if 'product' in cls.lower():
            all_classes.add(cls)

print(f"\nAll classes with 'product': {sorted(all_classes)}")

adapter.driver.quit()
