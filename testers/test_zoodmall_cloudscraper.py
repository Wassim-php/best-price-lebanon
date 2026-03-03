"""Test ZoodMall with cloudscraper to bypass Cloudflare"""

import cloudscraper
from bs4 import BeautifulSoup
import json

query = "samsung a56"
search_url = f"https://www.zoodmall.com.lb/en/search/?q={query.replace(' ', '%20')}"

print("=" * 70)
print("TESTING ZOODMALL WITH CLOUDSCRAPER")
print("=" * 70)
print(f"\nSearch URL: {search_url}\n")

# Create a cloudscraper instance
scraper = cloudscraper.create_scraper(
    browser={
        'browser': 'chrome',
        'platform': 'windows',
        'mobile': False
    }
)

try:
    print("Loading page...")
    response = scraper.get(search_url, timeout=30)
    
    print(f"Response Status: {response.status_code}")
    print(f"Response Length: {len(response.text)} characters")
    
    # Save HTML
    with open('testers/zoodmall_cloudscraper_page.html', 'w', encoding='utf-8') as f:
        f.write(response.text)
    print(f"✓ HTML saved to: testers/zoodmall_cloudscraper_page.html")
    
    # Check if we bypassed Cloudflare
    if 'Just a moment' in response.text or 'challenge' in response.text.lower()[:1000]:
        print("\n❌ Still blocked by Cloudflare")
    else:
        print("\n✅ Successfully bypassed Cloudflare!")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for product containers
        print("\n" + "=" * 70)
        print("LOOKING FOR PRODUCTS")
        print("=" * 70)
        
        # Try different selectors
        patterns = [
            ('div', 'product'),
            ('div', 'item'),
            ('article', None),
            ('li', 'product'),
            ('div', 'card'),
        ]
        
        found_products = False
        for tag, class_pattern in patterns:
            if class_pattern:
                items = soup.find_all(tag, class_=lambda c: c and class_pattern in str(c).lower())
            else:
                items = soup.find_all(tag, limit=50)
            
            if items and len(items) > 3:
                print(f"\n✓ Found {len(items)} <{tag}> elements with '{class_pattern}' pattern")
                
                first_item = items[0]
                print(f"  First item classes: {first_item.get('class')}")
                
                # Look for product title
                title = first_item.find(['h1', 'h2', 'h3', 'h4', 'a'])
                if title:
                    print(f"  Title: {title.get_text(strip=True)[:60]}")
                
                # Look for price
                price_elem = first_item.find(class_=lambda c: c and 'price' in str(c).lower())
                if price_elem:
                    print(f"  Price: {price_elem.get_text(strip=True)[:30]}")
                
                # Look for link
                link = first_item.find('a', href=True)
                if link:
                    print(f"  Link: {link.get('href', '')[:80]}")
                
                found_products = True
                break
        
        if not found_products:
            print("\n⚠️  No obvious product containers found")
            
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
        
        # Check for results count
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
                break

except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("DONE")
print("=" * 70)
