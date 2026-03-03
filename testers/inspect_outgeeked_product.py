"""Inspect OutGeeked product detail page"""

import requests
from bs4 import BeautifulSoup

base_url = "https://outgeeked.net"
# Using a product URL from the search results
product_url = f"{base_url}/products/apple-iphone-17-pro"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
}

print("=" * 70)
print("INSPECTING OUTGEEKED PRODUCT PAGE")
print("=" * 70)
print(f"URL: {product_url}\n")

try:
    r = requests.get(product_url, headers=headers, timeout=15)
    
    if r.status_code == 200:
        soup = BeautifulSoup(r.text, 'lxml')
        
        # Save to file
        with open('testers/outgeeked_product_page.html', 'w', encoding='utf-8') as f:
            f.write(soup.prettify())
        print("✓ Saved HTML to testers/outgeeked_product_page.html\n")
        
        # Product title
        title_selectors = [
            'h1.product-title',
            'h1.product__title',
            'h1[class*="product"]',
            'h1',
        ]
        
        print("PRODUCT TITLE:")
        for selector in title_selectors:
            title = soup.select_one(selector)
            if title:
                print(f"  Selector: {selector}")
                print(f"  Text: {title.get_text().strip()}")
                break
        
        # Price
        print("\n" + "=" * 70)
        print("PRICE INFORMATION")
        print("=" * 70)
        
        # Look for price elements
        price_selectors = [
            'span.f-price-item',
            'span.f-price-item--sale',
            'span.f-price-item--regular',
            'span.price',
            'div.price',
        ]
        
        for selector in price_selectors:
            prices = soup.select(selector)
            if prices:
                print(f"\nSelector: {selector}")
                for i, price in enumerate(prices[:3], 1):
                    print(f"  {i}. {price.get_text().strip()}")
        
        # Look for Shopify JSON data
        print("\n" + "=" * 70)
        print("SHOPIFY JSON DATA")
        print("=" * 70)
        
        scripts = soup.find_all('script', type='application/json')
        for i, script in enumerate(scripts[:3], 1):
            content = script.get_text().strip()
            if 'price' in content.lower() or 'product' in content.lower():
                print(f"\nScript {i} (first 500 chars):")
                print(content[:500])
        
        # Look for variant data
        variant_script = soup.find('script', string=lambda t: t and 'variants' in t)
        if variant_script:
            print("\n" + "=" * 70)
            print("VARIANT DATA FOUND")
            print("=" * 70)
            print(variant_script.get_text()[:1000])
        
        # Availability
        print("\n" + "=" * 70)
        print("AVAILABILITY")
        print("=" * 70)
        
        availability_selectors = [
            'div.product-form__buttons',
            'button[name="add"]',
            '.product-availability',
            'span.inventory',
        ]
        
        for selector in availability_selectors:
            elem = soup.select_one(selector)
            if elem:
                print(f"Selector: {selector}")
                print(f"  Text: {elem.get_text().strip()[:100]}")
        
    else:
        print(f"Failed: Status {r.status_code}")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("COMPLETE")
print("=" * 70)
