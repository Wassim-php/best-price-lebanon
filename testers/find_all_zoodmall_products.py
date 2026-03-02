"""Search for all product-item-list divs"""

from bs4 import BeautifulSoup
import re

with open('testers/zoodmall_cloudscraper_page.html', 'r', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')

print("=" * 70)
print("FINDING ALL PRODUCT CONTAINERS")
print("=" * 70)

# Find all product-item-list divs
product_items = soup.find_all('div', class_='product-item-list')
print(f"\nFound {len(product_items)} product-item-list divs")

if product_items:
    print("\n" + "=" * 70)
    print("ANALYZING ALL PRODUCTS")
    print("=" * 70)
    
    for i, item in enumerate(product_items, 1):
        # Find product link
        link = item.find('a', class_='product-mini')
        if link:
            title = link.get_text(strip=True)
            href = link.get('href', '')
            
            # Find price
            price_elem = item.find(class_='product-mini__totalLocalPrice')
            price = price_elem.get_text(strip=True) if price_elem else "N/A"
            
            # Find original price (strikethrough)
            orig_price_elem = item.find(class_='price-text-decoration')
            orig_price = orig_price_elem.get_text(strip=True) if orig_price_elem else "N/A"
            
            # Find image
            img = item.find('img', src=lambda s: s and 'zoodmall' in s and 'flag' not in s.lower())
            image_url = img.get('src', '') if img else "N/A"
            
            print(f"\nProduct {i}:")
            print(f"  Title: {title[:80]}")
            print(f"  URL: https://www.zoodmall.com.lb{href}")
            print(f"  Price: {price.replace(chr(10), ' ')}")  # Remove newlines
            if orig_price != "N/A":
                print(f"  Original Price: {orig_price.replace(chr(10), ' ')}")
            if image_url != "N/A":
                print(f"  Image: {image_url[:80]}")
else:
    print("\n⚠️  No product-item-list divs found")
    print("\nLet's check what divs with 'product' in class exist:")
    
    all_product_divs = soup.find_all('div', class_=lambda c: c and 'product' in ' '.join(c).lower())
    print(f"\nFound {len(all_product_divs)} divs with 'product' in class")
    
    # Get unique classes
    unique_classes = set()
    for div in all_product_divs:
        classes = div.get('class', [])
        for cls in classes:
            if 'product' in cls.lower():
                unique_classes.add(cls)
    
    print(f"\nUnique classes containing 'product': {sorted(unique_classes)}")

# Check if page mentions total results
print("\n" + "=" * 70)
print("CHECKING FOR RESULTS INFO")
print("=" * 70)

page_text = soup.get_text()
result_match = re.search(r'(\d+)\s+(results?|items?|products?)', page_text, re.IGNORECASE)
if result_match:
    print(f"\nFound: {result_match.group(0)}")

# Check if there's pagination or lazy loading indicator
pagination = soup.find(class_=lambda c: c and ('pagination' in str(c).lower() or 'load' in str(c).lower()))
if pagination:
    print(f"\nFound pagination/loading element: {pagination.get('class')}")

print("\n" + "=" * 70)
