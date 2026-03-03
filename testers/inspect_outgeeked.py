"""Inspect OutGeeked website structure"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import quote

# OutGeeked search
search_query = "iphone"
base_url = "https://outgeeked.net"
# URL-encoded "options[prefix]=last"
search_url = f"{base_url}/search?options%5Bprefix%5D=last&q={quote(search_query)}"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
}

print("=" * 70)
print("INSPECTING OUTGEEKED SEARCH RESULTS")
print("=" * 70)
print(f"URL: {search_url}\n")

try:
    r = requests.get(search_url, headers=headers, timeout=15)
    print(f"Status Code: {r.status_code}")
    print(f"Response Length: {len(r.text)} characters\n")
    
    if r.status_code == 200:
        soup = BeautifulSoup(r.text, 'lxml')
        
        # Save to file
        with open('testers/outgeeked_search_page.html', 'w', encoding='utf-8') as f:
            f.write(soup.prettify())
        print("✓ Saved HTML to testers/outgeeked_search_page.html\n")
        
        # Page title
        title = soup.find('title')
        if title:
            print(f"Page Title: {title.get_text()}")
        
        print("\n" + "=" * 70)
        print("SEARCHING FOR PRODUCT CONTAINERS")
        print("=" * 70)
        
        # Common Shopify selectors
        selectors = [
            'div.product-card',
            'div.grid-item',
            'div.product-item',
            'article.product',
            'div.product',
            'li.product',
            '[class*="product"]',
        ]
        
        found_products = False
        for selector in selectors:
            elements = soup.select(selector)
            if elements and len(elements) > 2:  # More than 2 likely means product list
                print(f"\n✓ Found {len(elements)} elements with selector: {selector}")
                
                # Analyze first product
                first = elements[0]
                print("\nFirst Product HTML Structure:")
                print(first.prettify()[:1500])
                
                found_products = True
                break
        
        if not found_products:
            print("\n✗ No obvious product containers found")
            print("\nSearching for product-like patterns...")
            
            # Look for divs with product-related classes
            all_divs = soup.find_all(['div', 'article', 'li'])
            product_like = []
            for div in all_divs:
                classes = ' '.join(div.get('class', []))
                if any(word in classes.lower() for word in ['product', 'item', 'card', 'grid']):
                    product_like.append((div.name, classes))
            
            # Count occurrences
            from collections import Counter
            class_counts = Counter([c for _, c in product_like])
            
            print("\nMost common product-like classes:")
            for cls, count in class_counts.most_common(10):
                print(f"  {count}x: {cls}")
        
        # Look for product names/links
        print("\n" + "=" * 70)
        print("SEARCHING FOR PRODUCT NAMES/LINKS")
        print("=" * 70)
        
        # Find links that might be products
        all_links = soup.find_all('a', href=True)
        product_links = []
        
        for link in all_links:
            href = link.get('href', '')
            text = link.get_text().strip()
            
            # Shopify products typically have /products/ in URL
            if '/products/' in href and text and len(text) > 3:
                product_links.append({
                    'text': text[:80],
                    'href': href,
                    'classes': link.get('class', [])
                })
        
        if product_links:
            print(f"\nFound {len(product_links)} product links:")
            for i, link in enumerate(product_links[:10], 1):
                print(f"{i}. {link['text']}")
                print(f"   URL: {link['href']}")
        
        # Look for prices
        print("\n" + "=" * 70)
        print("SEARCHING FOR PRICES")
        print("=" * 70)
        
        price_patterns = ['price', 'amount', 'cost']
        price_elements = []
        
        for pattern in price_patterns:
            elements = soup.find_all(class_=lambda x: x and pattern in str(x).lower())
            for elem in elements[:5]:
                text = elem.get_text().strip()
                if '$' in text or 'usd' in text.lower():
                    price_elements.append({
                        'tag': elem.name,
                        'classes': elem.get('class', []),
                        'text': text[:50]
                    })
        
        if price_elements:
            print(f"\nFound {len(price_elements)} price elements:")
            for i, elem in enumerate(price_elements[:10], 1):
                print(f"{i}. <{elem['tag']}> {elem['text']}")
                print(f"   Classes: {elem['classes']}")
        
    else:
        print(f"Failed to fetch page. Status: {r.status_code}")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("INSPECTION COMPLETE")
print("=" * 70)
