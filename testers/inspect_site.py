"""
Quick script to inspect 961souq structure for cart/checkout scraping.
Run this to see what elements are actually available.
"""
import requests
from bs4 import BeautifulSoup

# Let's inspect a product page structure
product_url = "https://961souq.com/products/apple-iphone-15"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

print("Fetching product page...")
r = requests.get(product_url, headers=headers, timeout=25)
soup = BeautifulSoup(r.text, 'html.parser')

print("\n=== Product Page Structure ===\n")

# Look for add to cart button
cart_buttons = soup.find_all(['button', 'input'], type='submit')
print("Add to Cart buttons found:")
for btn in cart_buttons[:3]:
    print(f"  - Tag: {btn.name}, Name: {btn.get('name')}, Class: {btn.get('class')}, Text: {btn.get_text(strip=True)[:50]}")

# Look for price elements
print("\nPrice elements found:")
price_elements = soup.find_all(class_=lambda x: x and 'price' in x.lower())
for elem in price_elements[:5]:
    print(f"  - Class: {elem.get('class')}, Text: {elem.get_text(strip=True)[:50]}")

# Look for form structure
forms = soup.find_all('form')
print(f"\nForms found: {len(forms)}")
for form in forms[:2]:
    print(f"  - Action: {form.get('action')}, ID: {form.get('id')}, Class: {form.get('class')}")

print("\n=== Site Uses (check for JavaScript requirements) ===")
scripts = soup.find_all('script', src=True)
for script in scripts[:5]:
    src = script.get('src', '')
    if 'shopify' in src.lower() or 'cart' in src.lower() or 'checkout' in src.lower():
        print(f"  - {src}")

print("\n=== Important: Is this a Shopify site? ===")
if 'shopify' in r.text.lower():
    print("✓ YES - This is a Shopify store")
    print("  Shopify uses AJAX for cart operations - we need a different approach!")
else:
    print("✗ NO - Custom implementation")
