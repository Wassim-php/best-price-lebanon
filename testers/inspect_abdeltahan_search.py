import requests
from bs4 import BeautifulSoup
import re

# Search for the product
search_url = 'https://abedtahan.com/search?q=Wave+Gas+%26+Electric+Heater&options[prefix]=last'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

print(f"Searching: {search_url}\n")
r = requests.get(search_url, headers=headers, timeout=15)
soup = BeautifulSoup(r.text, 'lxml')

print("=" * 60)
print("SEARCH RESULTS")
print("=" * 60)

# Find product cards
cards = soup.select("li.grid__item")
print(f"\nFound {len(cards)} product cards\n")

_PRICE_RE = re.compile(r"(\d+(?:,\d{3})*(?:\.\d+)?)")

for i, card in enumerate(cards[:5]):
    print(f"\n--- Product {i+1} ---")
    
    # Title
    title_el = card.select_one("h3.card__heading a")
    if title_el:
        print(f"Title: {title_el.get_text(strip=True)}")
        print(f"URL: {title_el.get('href')}")
    
    # Price elements
    print("\nPrice elements in this card:")
    price_elements = card.select('[class*="price"]')
    for j, elem in enumerate(price_elements[:5]):
        classes = ' '.join(elem.get('class', []))
        text = elem.get_text(strip=True)
        print(f"  {j+1}. <{elem.name} class='{classes}'>: {text[:80]}")
    
    # Try extracting price with current method
    price_el = card.select_one(".price-item--sale")
    if not price_el:
        price_el = card.select_one(".price-item--regular")
    
    if price_el:
        raw_price = price_el.get_text(strip=True)
        print(f"\nExtracted price element text: '{raw_price}'")
        
        # Find all numbers
        matches = _PRICE_RE.findall(raw_price)
        print(f"All numbers found: {matches}")
        
        if matches:
            for match in matches:
                price = float(match.replace(',', ''))
                print(f"  - Potential price: ${price}")

print("\n" + "=" * 60)
