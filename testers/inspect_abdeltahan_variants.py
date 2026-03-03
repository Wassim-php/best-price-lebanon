import requests
from bs4 import BeautifulSoup
import re
import json

# Fetch the product page
url = 'https://abedtahan.com/products/wave-patio-heater-glass-and-river-stone'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

print(f"Fetching: {url}\n")
r = requests.get(url, headers=headers, timeout=15)
soup = BeautifulSoup(r.text, 'lxml')

print("=" * 60)
print("LOOKING FOR PRODUCT JSON / VARIANTS")
print("=" * 60)

# Look for product JSON
scripts = soup.find_all('script')
for script in scripts:
    if script.string and 'product' in script.string.lower() and ('price' in script.string.lower() or 'variant' in script.string.lower()):
        try:
            # Try to find JSON data
            text = script.string.strip()
            if text.startswith('{') or text.startswith('[') or 'var product' in text or 'window' in text:
                print(f"\n--- Found potential product data ---")
                print(text[:800])
                print("\n...")
        except:
            pass

print("\n" + "=" * 60)
print("PRICE IN PRODUCT-INFO SECTION")
print("=" * 60)

# Look at the product info section specifically
product_info = soup.select_one('.product__info-wrapper')
if product_info:
    price_container = product_info.select_one('.price')
    if price_container:
        print(f"\nPrice container HTML:")
        print(str(price_container)[:500])
        
        # Try to find the actual price span
        price_spans = price_container.select('span.price-item')
        print(f"\nFound {len(price_spans)} price-item spans:")
        for span in price_spans:
            classes = ' '.join(span.get('class', []))
            text = span.get_text(strip=True)
            print(f"  <span class='{classes}'>: {text}")

print("\n" + "=" * 60)
print("ALL PRICES ON PAGE")
print("=" * 60)

_PRICE_RE = re.compile(r"\$(\d+(?:,\d{3})*(?:\.\d+)?)")
all_prices = _PRICE_RE.findall(r.text)
unique_prices = sorted(set(float(p.replace(',', '')) for p in all_prices[:50]))
print(f"\nUnique prices found on page: {unique_prices[:15]}")
