"""Inspect a ZoodMall product page"""

import cloudscraper
from bs4 import BeautifulSoup

product_url = "https://www.zoodmall.com.lb/en/product/35483936/apple-iphone-17-silicone-case-with-magsafe/"

print("=" * 70)
print("INSPECTING ZOODMALL PRODUCT PAGE")
print("=" * 70)
print(f"\nURL: {product_url}\n")

scraper = cloudscraper.create_scraper()
response = scraper.get(product_url, timeout=30)

print(f"Status: {response.status_code}")

soup = BeautifulSoup(response.text, 'lxml')

# Save HTML
with open('testers/zoodmall_product_page.html', 'w', encoding='utf-8') as f:
    f.write(response.text)
print("✓ HTML saved to: testers/zoodmall_product_page.html\n")

# Look for all price elements
print("=" * 70)
print("LOOKING FOR PRICE ELEMENTS")
print("=" * 70)

price_elements = soup.find_all(class_=lambda c: c and 'price' in str(c).lower())
print(f"\nFound {len(price_elements)} elements with 'price' in class\n")

for i, elem in enumerate(price_elements[:10], 1):
    print(f"{i}. Class: {elem.get('class')}")
    print(f"   Text: {elem.get_text(strip=True)[:80]}")
    print()

# Look for specific price classes from search page
print("=" * 70)
print("CHECKING SPECIFIC PRICE SELECTORS")
print("=" * 70)

selectors = [
    ('product-mini__totalLocalPrice', 'Search page price class'),
    ('product-price', 'Product price class'),
    ('actual-price', 'Actual price class'),
    ('price', 'Generic price class'),
]

for class_name, description in selectors:
    elem = soup.find(class_=class_name)
    if elem:
        print(f"\n✓ Found {description}:")
        print(f"  Class: {elem.get('class')}")
        print(f"  Text: {elem.get_text(strip=True)}")

# Look for data attributes with price
print("\n" + "=" * 70)
print("CHECKING FOR DATA ATTRIBUTES")
print("=" * 70)

elements_with_data_price = soup.find_all(attrs=lambda a: a and any(k.startswith('data-price') for k in a.keys()))
if elements_with_data_price:
    print(f"\nFound {len(elements_with_data_price)} elements with data-price attributes")
    for elem in elements_with_data_price[:5]:
        print(f"  Tag: {elem.name}")
        print(f"  Class: {elem.get('class')}")
        for attr, value in elem.attrs.items():
            if 'price' in attr.lower():
                print(f"  {attr}: {value}")
        print()

print("=" * 70)
