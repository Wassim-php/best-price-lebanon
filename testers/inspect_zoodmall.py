"""Inspect ZoodMall website structure"""

import requests
from bs4 import BeautifulSoup
import json

query = "samsung a56"
search_url = f"https://www.zoodmall.com.lb/en/search/?q={query.replace(' ', '%20')}"

print("=" * 70)
print("INSPECTING ZOODMALL SEARCH PAGE")
print("=" * 70)
print(f"\nSearch URL: {search_url}\n")

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
}

try:
    response = requests.get(search_url, headers=headers, timeout=15)
    print(f"Response Status: {response.status_code}")
    print(f"Response Length: {len(response.text)} characters")
    
    # Save HTML for inspection
    with open('testers/zoodmall_search_page.html', 'w', encoding='utf-8') as f:
        f.write(response.text)
    print(f"✓ HTML saved to: testers/zoodmall_search_page.html")
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Look for product containers
    print("\n" + "=" * 70)
    print("LOOKING FOR PRODUCT CONTAINERS")
    print("=" * 70)
    
    # Common patterns
    patterns = [
        ('div', 'product'),
        ('div', 'item'),
        ('article', None),
        ('li', 'product'),
        ('div', 'card'),
    ]
    
    for tag, class_pattern in patterns:
        if class_pattern:
            items = soup.find_all(tag, class_=lambda c: c and class_pattern in str(c).lower())
        else:
            items = soup.find_all(tag)
        
        if items and len(items) > 3:  # Likely found product containers
            print(f"\n✓ Found {len(items)} <{tag}> with '{class_pattern}' in class")
            
            first_item = items[0]
            print(f"  First item classes: {first_item.get('class')}")
            
            # Look for links
            links = first_item.find_all('a', href=True)
            if links:
                print(f"  Links in first item: {len(links)}")
                print(f"  First link: {links[0].get('href', '')[:80]}")
            
            # Look for prices
            price_patterns = ['price', 'cost', 'amount']
            for pattern in price_patterns:
                price_elem = first_item.find(class_=lambda c: c and pattern in str(c).lower())
                if price_elem:
                    print(f"  Found price element: {price_elem.get('class')}")
                    print(f"  Price text: {price_elem.get_text(strip=True)[:50]}")
                    break
    
    # Look for product links
    print("\n" + "=" * 70)
    print("LOOKING FOR PRODUCT LINKS")
    print("=" * 70)
    
    all_links = soup.find_all('a', href=True)
    product_links = [link for link in all_links if '/product' in link.get('href', '').lower() or '/p/' in link.get('href', '').lower()]
    
    print(f"\nFound {len(product_links)} links with '/product' or '/p/' in href")
    
    if product_links:
        print("\nFirst 5 product links:")
        for i, link in enumerate(product_links[:5], 1):
            text = link.get_text(strip=True)
            href = link.get('href', '')
            if text and len(text) > 3:
                print(f"  {i}. {text[:60]}")
                print(f"     URL: {href[:80]}")
    
    # Check for JSON data
    print("\n" + "=" * 70)
    print("CHECKING FOR JSON DATA")
    print("=" * 70)
    
    scripts = soup.find_all('script', type='application/ld+json')
    print(f"\nFound {len(scripts)} JSON-LD scripts")
    
    for i, script in enumerate(scripts[:3], 1):
        try:
            data = json.loads(script.string)
            print(f"\nScript {i} type: {data.get('@type', 'Unknown')}")
            if isinstance(data, dict):
                print(f"  Keys: {list(data.keys())[:10]}")
        except:
            pass
    
    # Look for data attributes
    print("\n" + "=" * 70)
    print("CHECKING FOR DATA ATTRIBUTES")
    print("=" * 70)
    
    elements_with_data = soup.find_all(attrs=lambda a: any(k.startswith('data-') for k in (a or {}).keys()))
    print(f"\nFound {len(elements_with_data)} elements with data- attributes")
    
    if elements_with_data:
        data_attrs = set()
        for elem in elements_with_data[:50]:
            for attr in elem.attrs:
                if attr.startswith('data-'):
                    data_attrs.add(attr)
        
        print(f"\nCommon data attributes: {sorted(data_attrs)[:20]}")
    
    # Check page text for results count
    print("\n" + "=" * 70)
    print("CHECKING FOR RESULTS COUNT")
    print("=" * 70)
    
    page_text = soup.get_text()
    import re
    
    result_patterns = [
        r'(\d+)\s+results?',
        r'(\d+)\s+products?',
        r'(\d+)\s+items?',
        r'showing\s+(\d+)',
    ]
    
    for pattern in result_patterns:
        match = re.search(pattern, page_text, re.IGNORECASE)
        if match:
            print(f"  Found: '{match.group(0)}' - Count: {match.group(1)}")
    
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Search URL: {search_url}")
    print(f"Status: {response.status_code}")
    print(f"HTML saved for detailed inspection")
    print("=" * 70)

except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
