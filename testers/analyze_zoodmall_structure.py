"""Analyze ZoodMall product structure in detail"""

from bs4 import BeautifulSoup

with open('testers/zoodmall_cloudscraper_page.html', 'r', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')

print("=" * 70)
print("ANALYZING ZOODMALL PRODUCT STRUCTURE")
print("=" * 70)

# Find product containers
products = soup.find_all('div', class_='productList-container')
print(f"\nFound {len(products)} products")

if products:
    print("\n" + "=" * 70)
    print("ANALYZING FIRST PRODUCT")
    print("=" * 70)
    
    first = products[0]
    
    # Find product title
    print("\nLooking for title...")
    title_patterns = [
        ('h1', None),
        ('h2', None),
        ('h3', None),
        ('h4', None),
        ('a', 'title'),
        ('div', 'name'),
        ('span', 'name'),
    ]
    
    for tag, class_pattern in title_patterns:
        if class_pattern:
            elem = first.find(tag, class_=lambda c: c and class_pattern in str(c).lower())
        else:
            elem = first.find(tag)
        
        if elem and elem.get_text(strip=True):
            text = elem.get_text(strip=True)
            if len(text) > 10:  # Likely a product title
                print(f"  ✓ Found title in <{tag}>: {text[:80]}")
                print(f"    Classes: {elem.get('class')}")
                break
    
    # Find product link
    print("\nLooking for link...")
    link = first.find('a', href=lambda h: h and '/product/' in h)
    if link:
        href = link.get('href')
        print(f"  ✓ Found link: {href}")
        print(f"    Full URL: https://www.zoodmall.com.lb{href if href.startswith('/') else ''}")
        print(f"    Link classes: {link.get('class')}")
        print(f"    Link text: {link.get_text(strip=True)[:60]}")
    
    # Find price
    print("\nLooking for price...")
    price_patterns = [
        lambda: first.find(class_=lambda c: c and 'price' in str(c).lower()),
        lambda: first.find('span', class_=lambda c: c and 'price' in str(c).lower()),
        lambda: first.find('div', class_=lambda c: c and 'price' in str(c).lower()),
        lambda: first.find(attrs={'data-price': True}),
    ]
    
    for pattern in price_patterns:
        elem = pattern()
        if elem:
            print(f"  ✓ Found price element")
            print(f"    Classes: {elem.get('class')}")
            print(f"    Text: {elem.get_text(strip=True)}")
            print(f"    Data attributes: {[k for k in elem.attrs if k.startswith('data-')]}")
            break
    
    # Find image
    print("\nLooking for image...")
    img = first.find('img')
    if img:
        print(f"  ✓ Found image")
        print(f"    src: {img.get('src', '')[:80]}")
        print(f"    data-src: {img.get('data-src', '')[:80]}")
        print(f"    alt: {img.get('alt', '')[:60]}")
    
    # Show raw HTML (partial)
    print("\n" + "=" * 70)
    print("FIRST PRODUCT RAW HTML (first 1000 chars)")
    print("=" * 70)
    print(first.prettify()[:1000])
    
    print("\n" + "=" * 70)
    print("ANALYZING MORE PRODUCTS")
    print("=" * 70)
    
    for i, product in enumerate(products[:5], 1):
        # Get title
        title_elem = None
        for tag in ['h1', 'h2', 'h3', 'h4']:
            elem = product.find(tag)
            if elem:
                title_elem = elem
                break
        
        if not title_elem:
            # Try finding in link text
            link = product.find('a', href=lambda h: h and '/product/' in h)
            if link:
                title_elem = link
        
        title = title_elem.get_text(strip=True) if title_elem else "N/A"
        
        # Get price
        price_elem = product.find(class_=lambda c: c and 'price' in str(c).lower())
        price = price_elem.get_text(strip=True) if price_elem else "N/A"
        
        # Get link
        link = product.find('a', href=lambda h: h and '/product/' in h)
        url = link.get('href') if link else "N/A"
        
        print(f"\nProduct {i}:")
        print(f"  Title: {title[:60]}")
        print(f"  Price: {price[:30]}")
        print(f"  URL: {url[:80]}")

print("\n" + "=" * 70)
print("DONE")
print("=" * 70)
