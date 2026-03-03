"""Analyze the saved HTML to find price elements"""
from bs4 import BeautifulSoup

with open('testers/zoodmall_detail_page_debug.html', 'r', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')

print("\n" + "="*70)
print("ANALYZING ZOODMALL DETAIL PAGE HTML")
print("="*70)

# Search for numbers that might be prices
print("\n1. Elements containing '375':")
for elem in soup.find_all(string=lambda s: s and '375' in str(s)):
    if elem.parent:
        print(f"   <{elem.parent.name} class='{elem.parent.get('class', [])}'>")
        print(f"      {elem.strip()[:80]}")

print("\n2. Elements containing '409':")
for elem in soup.find_all(string=lambda s: s and '409' in str(s)):
    if elem.parent:
        print(f"   <{elem.parent.name} class='{elem.parent.get('class', [])}'>")
        print(f"      {elem.strip()[:80]}")

print("\n3. Elements containing '425':")
for elem in soup.find_all(string=lambda s: s and '425' in str(s)):
    if elem.parent:
        print(f"   <{elem.parent.name} class='{elem.parent.get('class', [])}'>")
        print(f"      {elem.strip()[:80]}")

# Find elements with 'price' in class
print("\n4. Elements with 'price' in class name:")
price_elems = soup.find_all(class_=lambda x: x and 'price' in str(x).lower())
print(f"   Found {len(price_elems)} elements")
for i, elem in enumerate(price_elems[:10], 1):
    classes = ' '.join(elem.get('class', []))
    text = elem.get_text(strip=True)[:60]
    print(f"   {i}. <{elem.name} class='{classes}'> {text}")

print("\n" + "="*70 + "\n")
