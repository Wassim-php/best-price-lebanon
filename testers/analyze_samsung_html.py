"""Analyze Samsung A56 HTML for price structure"""
from bs4 import BeautifulSoup

with open('testers/samsung_a56_page.html', 'r', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')

print("\n" + "="*70)
print("SEARCHING FOR PRICES IN HTML")
print("="*70 + "\n")

# Find all elements containing "375" or "425"
print("1. Elements containing '375':")
print("-"*70)
for elem in soup.find_all(string=lambda text: text and '375' in str(text)):
    parent = elem.parent
    if parent:
        classes = parent.get('class', [])
        tag = parent.name
        siblings = [s.name for s in parent.find_all_next_siblings() if hasattr(s, 'name')]
        print(f"   <{tag} class='{' '.join(classes)}'>{elem.strip()[:60]}</{tag}>")
print()

print("2. Elements containing '425':")
print("-"*70)
for elem in soup.find_all(string=lambda text: text and '425' in str(text)):
    parent = elem.parent
    if parent:
        classes = parent.get('class', [])
        tag = parent.name
        print(f"   <{tag} class='{' '.join(classes)}'>{elem.strip()[:60]}</{tag}>")
print()

# Find all elements with 'price' in class name
print("3. All elements with 'price' in class:")
print("-"*70)
price_elems = soup.find_all(class_=lambda x: x and 'price' in str(x).lower())
for i, elem in enumerate(price_elems[:15], 1):
    classes = elem.get('class', [])
    text = elem.get_text(strip=True)[:60]
    print(f"{i}. <{elem.name} class='{' '.join(classes)}'>{text}</{elem.name}>")
print()

# Try to find product-price container
print("4. Looking for product-price container:")
print("-"*70)
container = soup.find('div', class_='product-price')
if container:
    print(f"✓ Found <div class='product-price'>")
    print(f"   Inner HTML:")
    for child in container.children:
        if hasattr(child, 'name') and child.name:
            classes = child.get('class', [])
            text = child.get_text(strip=True)[:60]
            print(f"     <{child.name} class='{' '.join(classes)}'>{text}</{child.name}>")
else:
    print("✗ No product-price container found")
print()

# Check for price__actual and price__sale
print("5. Specific price classes:")
print("-"*70)
actual = soup.find(class_='price__actual')
sale = soup.find(class_='price__sale')
un_sale = soup.find(class_='price__un_sale')

if actual:
    print(f"✓ price__actual: {actual.get_text(strip=True)}")
if sale:
    print(f"✓ price__sale: {sale.get_text(strip=True)}")
if un_sale:
    print(f"✓ price__un_sale: {un_sale.get_text(strip=True)}")

if not (actual or sale or un_sale):
    print("✗ None of the standard price classes found")

print("\n" + "="*70 + "\n")
