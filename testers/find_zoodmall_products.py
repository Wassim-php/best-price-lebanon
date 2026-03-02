"""Find individual product items in ZoodMall"""

from bs4 import BeautifulSoup
import re

with open('testers/zoodmall_cloudscraper_page.html', 'r', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')

print("=" * 70)
print("FINDING INDIVIDUAL PRODUCT ITEMS")
print("=" * 70)

# Look for links with /product/ in href
product_links = soup.find_all('a', href=lambda h: h and '/product/' in h)
print(f"\nFound {len(product_links)} links with '/product/' in href")

if product_links:
    print("\nFirst 10 product links:")
    unique_products = []
    seen_urls = set()
    
    for link in product_links:
        href = link.get('href', '')
        if href not in seen_urls:
            seen_urls.add(href)
            unique_products.append(link)
            
            text = link.get_text(strip=True)
            classes = link.get('class', [])
            
            print(f"\n  {len(unique_products)}. {text[:60]}")
            print(f"     URL: {href[:80]}")
            print(f"     Classes: {classes}")
            
            if len(unique_products) >= 10:
                break
    
    print(f"\n\nTotal unique product URLs: {len(seen_urls)}")
    
    # Analyze first product's parent structure
    print("\n" + "=" * 70)
    print("ANALYZING FIRST PRODUCT PARENT STRUCTURE")
    print("=" * 70)
    
    first_link = unique_products[0]
    print(f"\nFirst product link: {first_link.get_text(strip=True)[:60]}")
    
    # Go up the parents to find the product container
    current = first_link
    for level in range(1, 8):
        current = current.parent
        if not current:
            break
        
        tag = current.name
        classes = current.get('class', [])
        
        print(f"\nLevel {level}: <{tag}>")
        if classes:
            print(f"  Classes: {', '.join(classes)}")
        
        # Check if this level contains price info
        price_elem = current.find(class_=lambda c: c and 'price' in str(c).lower(), recursive=False)
        if price_elem:
            print(f"  ⭐ Contains price element (direct child)")
        
        # Check how many product links in this container
        links_in_container = current.find_all('a', href=lambda h: h and '/product/' in h)
        if links_in_container:
            unique_in_container = set(l.get('href') for l in links_in_container)
            
            if len(unique_in_container) == 1:
                print(f"  ⭐ LIKELY PRODUCT CONTAINER (1 unique product link)")
                
                # This is likely the product container, let's analyze it
                print(f"\n  Product container details:")
                print(f"    Tag: {tag}")
                print(f"    Classes: {classes}")
                
                # Find all price elements
                all_prices = current.find_all(class_=lambda c: c and 'price' in str(c).lower())
                if all_prices:
                    print(f"    Price elements: {len(all_prices)}")
                    for price_elem in all_prices[:3]:
                        print(f"      - {price_elem.get('class')}: {price_elem.get_text(strip=True)[:40]}")
                
                # Find image
                img = current.find('img')
                if img:
                    print(f"    Image: {img.get('src', '')[:60]}")
                
                break
            elif len(unique_in_container) > 10:
                print(f"  Contains {len(unique_in_container)} unique products (too many, we've gone too high)")
                break

# Look for common product item selectors
print("\n\n" + "=" * 70)
print("TRYING COMMON PRODUCT SELECTORS")
print("=" * 70)

selectors = [
    ('a', 'product-mini'),
    ('div', 'product-item'),
    ('div', 'product'),
    ('li', 'product'),
    ('div', 'item'),
]

for tag, class_name in selectors:
    elements = soup.find_all(tag, class_=class_name)
    if elements:
        print(f"\n✓ Found {len(elements)} <{tag} class='{class_name}'>")
        if len(elements) > 1:
            print(f"  This might be the product container!")
            
            # Check first element
            first = elements[0]
            link = first if first.name == 'a' else first.find('a', href=True)
            if link:
                print(f"  First product: {link.get_text(strip=True)[:60]}")
                print(f"  URL: {link.get('href', '')[:80]}")

print("\n" + "=" * 70)
