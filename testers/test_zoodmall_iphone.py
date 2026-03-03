"""Test ZoodMall with iphone search"""

import cloudscraper
from bs4 import BeautifulSoup

query = "iphone"
search_url = f"https://www.zoodmall.com.lb/en/search/?q={query}"

print(f"Testing ZoodMall search: {query}\n")

scraper = cloudscraper.create_scraper()
response = scraper.get(search_url, timeout=30)

print(f"Status: {response.status_code}")

soup = BeautifulSoup(response.text, 'html.parser')
products = soup.find_all('div', class_='product-item-list')

print(f"Found {len(products)} products\n")

for i, item in enumerate(products[:10], 1):  #  Show first 10
    link = item.find('a', class_='product-mini')
    if link:
        title = link.get_text(strip=True)
        href = link.get('href', '')
        
        price_elem = item.find(class_='product-mini__totalLocalPrice')
        price = price_elem.get_text(strip=True).replace('\n', ' ') if price_elem else "N/A"
        
        print(f"{i}. {title[:70]}")
        print(f"   Price: {price}")
        print(f"   URL: https://www.zoodmall.com.lb{href}\n")
