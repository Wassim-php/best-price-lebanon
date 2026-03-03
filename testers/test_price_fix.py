"""Test updated price extraction logic"""

import cloudscraper
from bs4 import BeautifulSoup
import re

def extract_price(price_text):
    """Extract numeric price from text"""
    try:
        cleaned = re.sub(r'[^\d.,]', '', price_text)
        cleaned = cleaned.strip().replace(',', '')
        if not cleaned:
            return None
        return float(cleaned)
    except:
        return None

print("=" * 70)
print("TESTING UPDATED PRICE EXTRACTION")
print("=" * 70)

scraper = cloudscraper.create_scraper()

product_url = "https://www.zoodmall.com.lb/en/product/35483936/apple-iphone-17-silicone-case-with-magsafe/"

print(f"\nProduct URL: {product_url}\n")

response = scraper.get(product_url, timeout=30)
soup = BeautifulSoup(response.text, 'lxml')

# Try the updated selector
print("Testing price selectors:")
print("=" * 70)

# 1. Try price__actual (sale price)
price_elem = soup.find(class_='price__actual')
if price_elem:
    price_text = price_elem.get_text(strip=True)
    price = extract_price(price_text)
    print(f"\n1. price__actual: {price_text}")
    print(f"   Extracted: ${price:.2f}" if price else "   Failed to extract")

# 2. Try product-mini__totalLocalPrice (fallback)
price_elem2 = soup.find(class_='product-mini__totalLocalPrice')
if price_elem2:
    price_text2 = price_elem2.get_text(strip=True)
    price2 = extract_price(price_text2)
    print(f"\n2. product-mini__totalLocalPrice: {price_text2}")
    print(f"   Extracted: ${price2:.2f}" if price2 else "   Failed to extract")
else:
    print(f"\n2. product-mini__totalLocalPrice: Not found")

# Calculate final pricing
print("\n" + "=" * 70)
print("FINAL PRICING")
print("=" * 70)

if price:
    shipping_fee = 5.0
    tax_amount = 0.0
    total = price + shipping_fee + tax_amount
    
    print(f"\nBase Price: ${price:.2f}")
    print(f"Shipping: ${shipping_fee:.2f}")
    print(f"Taxes: ${tax_amount:.2f}")
    print(f"Total: ${total:.2f}")
    print(f"Delivery: 7-14 days")
    
    print("\n✅ Price extraction working correctly!")
else:
    print("\n❌ Failed to extract price")

print("\n" + "=" * 70)
