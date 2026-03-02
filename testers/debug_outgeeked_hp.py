"""Debug OutGeeked search for 'hp victus'"""

import requests
from bs4 import BeautifulSoup
import json

query = "hp victus"
search_url = f"https://outgeeked.net/search?options%5Bprefix%5D=last&q={query.replace(' ', '+')}"

print("=" * 70)
print(f"DEBUGGING OUTGEEKED SEARCH: '{query}'")
print("=" * 70)
print(f"\nSearch URL: {search_url}\n")

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

response = requests.get(search_url, headers=headers, timeout=15)
print(f"Response Status: {response.status_code}")
print(f"Response Length: {len(response.text)} characters\n")

soup = BeautifulSoup(response.text, 'html.parser')

# Check for results count
results_text = soup.get_text()
if 'results found' in results_text.lower():
    import re
    match = re.search(r'(\d+)\s+results?\s+found', results_text, re.IGNORECASE)
    if match:
        print(f"Results Found: {match.group(1)}")

# Method 1: Original selector - product-card divs
print("\n" + "=" * 70)
print("METHOD 1: div.product-card")
print("=" * 70)
product_cards = soup.find_all('div', class_='product-card')
print(f"Found {len(product_cards)} product-card divs")

if product_cards:
    for i, card in enumerate(product_cards[:3], 1):
        print(f"\n  Card {i}:")
        link = card.find('a', href=lambda x: x and '/products/' in x)
        if link:
            print(f"    Link: {link.get('href', 'N/A')}")
            print(f"    Title: {link.get_text(strip=True)[:60]}")

# Method 2: Check for alternative product containers
print("\n" + "=" * 70)
print("METHOD 2: Alternative Selectors")
print("=" * 70)

# Check for product links directly
product_links = soup.find_all('a', href=lambda x: x and '/products/' in x)
print(f"Found {len(product_links)} links containing '/products/'")

if product_links:
    print("\n  First 5 product links:")
    for i, link in enumerate(product_links[:5], 1):
        title = link.get_text(strip=True)
        if title and len(title) > 3:  # Filter out empty or very short text
            print(f"    {i}. {title[:60]}")
            print(f"       URL: {link.get('href')}")

# Method 3: Check for product items
print("\n" + "=" * 70)
print("METHOD 3: Check for 'product' class variations")
print("=" * 70)

product_items = soup.find_all(class_=lambda x: x and 'product' in x.lower())
print(f"Found {len(product_items)} elements with 'product' in class")

if product_items:
    classes_found = set()
    for item in product_items:
        classes = item.get('class', [])
        classes_found.update(classes)
    print(f"\n  Unique classes containing 'product': {sorted(classes_found)}")

# Method 4: Check page structure
print("\n" + "=" * 70)
print("METHOD 4: Page Structure Analysis")
print("=" * 70)

# Check for no results message
no_results_indicators = [
    'no results', 'no products', 'nothing found', 'try again',
    '0 results', 'no matches', "didn't find"
]

page_text_lower = soup.get_text().lower()
for indicator in no_results_indicators:
    if indicator in page_text_lower:
        print(f"  ⚠️  Found indicator: '{indicator}'")

# Check if there's a product grid or collection
grid = soup.find('div', class_=lambda x: x and ('grid' in str(x).lower() or 'collection' in str(x).lower()))
if grid:
    print(f"\n  Found grid/collection container")
    print(f"  Classes: {grid.get('class')}")
    print(f"  Children count: {len(list(grid.children))}")

# Save HTML for inspection
output_file = "testers/outgeeked_hp_victus_search.html"
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(response.text)
print(f"\n✓ HTML saved to: {output_file}")

print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print(f"Query: '{query}'")
print(f"Product Cards Found: {len(product_cards)}")
print(f"Product Links Found: {len(product_links)}")
print(f"Status: {'✓ Products found' if product_cards or product_links else '✗ No products found'}")
print("=" * 70)
