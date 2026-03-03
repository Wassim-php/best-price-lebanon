"""Debug why parsing fails"""
from scraping.adapters.websites.zoodmall import ZoodMallAdapter
from urllib.parse import quote
from bs4 import BeautifulSoup
import time

adapter = ZoodMallAdapter()

search_url = f"https://www.zoodmall.com.lb/en/search/?q={quote('iphone')}"
print(f"Loading: {search_url}")

adapter.driver.get(search_url)
time.sleep(10)

html = adapter.driver.page_source
soup = BeautifulSoup(html, 'html.parser')

product_cards = soup.find_all('a', class_='product-mini', limit=5)
print(f"\nFound {len(product_cards)} product cards")

for i, card in enumerate(product_cards[:3], 1):
    print(f"\n--- Product {i} ---")
    
    # Check URL
    url = card.get('href', '')
    print(f"URL: {url[:60] if url else 'NONE'}")
    
    # Check title
    title = card.get('title', '').strip()
    print(f"Title attr: {title[:50] if title else 'NONE'}")
    
    # Check for title in children
    title_elem = card.find('div', class_='product-mini__title')
    if title_elem:
        print(f"Title elem: {title_elem.get_text(strip=True)[:50]}")
    
    # Check for price
    price_elem = card.find('span', class_='price__actual')
    if price_elem:
        print(f"Price elem: {price_elem.get_text(strip=True)}")
    else:
        # Try other price selectors
        for cls in ['product-mini__totalLocalPrice', 'price', 'product-price']:
            elem = card.find(class_=cls)
            if elem:
                print(f"Price ({cls}): {elem.get_text(strip=True)}")
                break
    
    # Try parsing with adapter's method
    try:
        offer = adapter._parse_product_card(card)
        if offer:
            print(f"✓ Parsed: {offer.title[:40]} - ${offer.item_price}")
        else:
            print(f"✗ Parsing returned None")
    except Exception as e:
        print(f"✗ Parsing error: {e}")

adapter.driver.quit()
