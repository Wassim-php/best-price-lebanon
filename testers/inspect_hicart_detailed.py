import requests
from bs4 import BeautifulSoup
from urllib.parse import quote

# HiCart search inspection
search_query = "iphone"
base_url = "https://www.hicart.com"
search_url = f"{base_url}/catalogsearch/result/?q={quote(search_query)}"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
}

print("=" * 70)
print("DETAILED HICART INSPECTION")
print("=" * 70)
print(f"URL: {search_url}\n")

try:
    r = requests.get(search_url, headers=headers, timeout=15)
    
    if r.status_code == 200:
        soup = BeautifulSoup(r.text, 'lxml')
        
        # Save full HTML to file for manual inspection
        with open('testers/hicart_search_page.html', 'w', encoding='utf-8') as f:
            f.write(soup.prettify())
        print("✓ Saved full HTML to testers/hicart_search_page.html\n")
        
        # Look for all links that might be product links
        all_links = soup.find_all('a', href=True)
        product_links = []
        
        for link in all_links:
            href = link.get('href', '')
            text = link.get_text().strip()
            
            # Skip empty, javascript, and navigation links
            if (href and 
                not href.startswith('javascript:') and 
                not href.startswith('#') and
                text and
                len(text) > 3 and
                ('/' in href or 'product' in href.lower())):
                
                # Look for product-like patterns
                if any(word in href.lower() for word in ['product', 'item', '.html']):
                    product_links.append({
                        'text': text[:80],
                        'href': href,
                        'classes': link.get('class', [])
                    })
        
        print(f"Found {len(product_links)} potential product links:")
        for i, link in enumerate(product_links[:10]):  # Show first 10
            print(f"\n{i+1}. {link['text']}")
            print(f"   URL: {link['href']}")
            print(f"   Classes: {link['classes']}")
        
        # Look for price elements
        print("\n" + "=" * 70)
        print("SEARCHING FOR PRICE ELEMENTS")
        print("=" * 70)
        
        # Find all elements that might contain prices
        price_patterns = [
            ('class', 'price'),
            ('class', 'special'),
            ('class', 'regular'),
            ('class', 'sale'),
            ('data-price', True),
        ]
        
        price_elements = []
        for attr, value in price_patterns:
            if value is True:
                elements = soup.find_all(attrs={attr: True})
            else:
                elements = soup.find_all(class_=lambda x: x and value in x.lower() if x else False)
            
            for elem in elements:
                text = elem.get_text().strip()
                if text and ('$' in text or 'usd' in text.lower() or text.replace(',','').replace('.','').isdigit()):
                    price_elements.append({
                        'tag': elem.name,
                        'classes': elem.get('class', []),
                        'text': text[:50],
                        'parent': elem.parent.name if elem.parent else 'None'
                    })
        
        print(f"\nFound {len(price_elements)} price-like elements:")
        for i, elem in enumerate(price_elements[:10]):
            print(f"\n{i+1}. <{elem['tag']}> {elem['text']}")
            print(f"   Classes: {elem['classes']}")
            print(f"   Parent: {elem['parent']}")
        
        # Look for product titles/names
        print("\n" + "=" * 70)
        print("SEARCHING FOR PRODUCT NAMES")
        print("=" * 70)
        
        # Look in common heading tags and specific classes
        name_candidates = []
        
        for tag in ['h2', 'h3', 'h4']:
            headings = soup.find_all(tag)
            for h in headings:
                text = h.get_text().strip()
                if text and len(text) > 5:  # Reasonable product name length
                    link = h.find('a')
                    name_candidates.append({
                        'tag': tag,
                        'text': text[:80],
                        'has_link': bool(link),
                        'classes': h.get('class', [])
                    })
        
        print(f"\nFound {len(name_candidates)} potential product names:")
        for i, name in enumerate(name_candidates[:10]):
            print(f"\n{i+1}. <{name['tag']}> {name['text']}")
            print(f"   Has link: {name['has_link']}")
            print(f"   Classes: {name['classes']}")
        
        # Look for divs/sections that might be product containers
        print("\n" + "=" * 70)
        print("ANALYZING CONTAINER STRUCTURE")
        print("=" * 70)
        
        # Look for repeating structures (likely product items)
        all_divs = soup.find_all(['div', 'li', 'article'])
        class_counts = {}
        
        for div in all_divs:
            classes = div.get('class', [])
            if classes:
                class_str = ' '.join(classes)
                class_counts[class_str] = class_counts.get(class_str, 0) + 1
        
        # Find classes that repeat (likely product containers)
        repeated_classes = [(cls, count) for cls, count in class_counts.items() 
                          if count > 2 and count < 50 and 'item' in cls.lower() or 'product' in cls.lower()]
        
        repeated_classes.sort(key=lambda x: x[1], reverse=True)
        
        print("\nMost common product-like classes:")
        for cls, count in repeated_classes[:15]:
            print(f"  {count}x: {cls}")
        
        # Try to find a sample product structure if repeated classes found
        if repeated_classes:
            sample_class = repeated_classes[0][0]
            print(f"\n\nSample element with class '{sample_class}':")
            sample = soup.find(class_=lambda x: x and sample_class in ' '.join(x) if x else False)
            if sample:
                print(sample.prettify()[:1000])
                
    else:
        print(f"Failed: Status {r.status_code}")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("INSPECTION COMPLETE")
print("=" * 70)
