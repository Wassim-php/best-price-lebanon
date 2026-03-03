import requests
from bs4 import BeautifulSoup

# Fetch the product page
url = 'https://abedtahan.com/products/wave-patio-heater-glass-and-river-stone'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

print(f"Fetching: {url}\n")
r = requests.get(url, headers=headers, timeout=15)
soup = BeautifulSoup(r.text, 'lxml')

print("=" * 60)
print("PRICE ELEMENTS")
print("=" * 60)

# Find all elements with 'price' in the class name
price_elements = soup.select('[class*="price"]')
for i, elem in enumerate(price_elements[:15]):
    classes = ' '.join(elem.get('class', []))
    text = elem.get_text(strip=True)[:150]
    print(f"\n{i+1}. <{elem.name} class='{classes}'>")
    print(f"   Text: {text}")

print("\n" + "=" * 60)
print("SPECIFIC PRICE SELECTORS")
print("=" * 60)

selectors = [
    '.price',
    '.price-item',
    '.price-item--sale',
    '.price-item--regular',
    'span.price-item--sale',
    'span.price-item--regular',
    '.price__sale',
    '.price__regular',
]

for selector in selectors:
    elem = soup.select_one(selector)
    if elem:
        print(f"\n{selector}: {elem.get_text(strip=True)[:100]}")
    else:
        print(f"\n{selector}: NOT FOUND")

print("\n" + "=" * 60)
print("CHECKING PRODUCT JSON")
print("=" * 60)

# Look for product JSON data
scripts = soup.find_all('script', type='application/json')
for i, script in enumerate(scripts[:3]):
    if 'price' in script.string.lower():
        print(f"\nScript {i+1}:")
        print(script.string[:500])
