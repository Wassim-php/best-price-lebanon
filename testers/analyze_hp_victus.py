"""Analyze the saved HTML to find the real HP Victus products"""

from bs4 import BeautifulSoup

print("=" * 70)
print("ANALYZING HP VICTUS SEARCH RESULTS")
print("=" * 70)

with open('testers/outgeeked_hp_victus_search.html', 'r', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')

# Find the search results section specifically
print("\n1. Looking for 'hp' or 'victus' in product titles...")
print("=" * 70)

# Find all links with product URLs
all_product_links = soup.find_all('a', href=lambda x: x and '/products/' in x)

hp_products = []
for link in all_product_links:
    text = link.get_text(strip=True).lower()
    href = link.get('href', '')
    
    # Look for HP or Victus in the text or URL
    if ('hp' in text or 'victus' in text or 'hp' in href.lower() or 'victus' in href.lower()) and len(text) > 5:
        hp_products.append({
            'title': link.get_text(strip=True),
            'url': href
        })

if hp_products:
    print(f"\nFound {len(hp_products)} HP/Victus products:")
    for i, prod in enumerate(hp_products, 1):
        print(f"\n  {i}. {prod['title']}")
        print(f"     URL: {prod['url']}")
else:
    print("\n⚠️  No HP or Victus products found in links")

# Check for a specific search results container
print("\n\n2. Looking for search results container...")
print("=" * 70)

# Common Shopify search result containers
search_containers = [
    soup.find('div', class_=lambda x: x and 'search' in str(x).lower() and 'result' in str(x).lower()),
    soup.find('div', id=lambda x: x and 'search' in str(x).lower()),
    soup.find('div', class_=lambda x: x and 'collection' in str(x).lower()),
]

for container in search_containers:
    if container:
        print(f"\nFound container: {container.get('class') or container.get('id')}")
        
        # Find products within this container
        products_in_container = container.find_all('div', class_='product-card')
        print(f"Products in container: {len(products_in_container)}")
        
        if products_in_container:
            print("\nFirst 3 products in search container:")
            for i, card in enumerate(products_in_container[:3], 1):
                # Try multiple ways to find the title
                title_elem = (
                    card.find('a', class_=lambda x: x and 'title' in str(x).lower()) or
                    card.find('h3') or
                    card.find('h2') or
                    card.find('a', href=lambda x: x and '/products/' in x)
                )
                
                if title_elem:
                    print(f"\n  {i}. {title_elem.get_text(strip=True)[:80]}")
                    
                    # Find the link
                    link = card.find('a', href=lambda x: x and '/products/' in x)
                    if link:
                        print(f"     URL: {link.get('href')}")

# Check the page text for "4 results found"
print("\n\n3. Checking results count context...")
print("=" * 70)
page_text = soup.get_text()
import re

# Find the context around "4 results found"
match = re.search(r'.{0,100}4\s+results?\s+found.{0,100}', page_text, re.IGNORECASE | re.DOTALL)
if match:
    print(f"\nContext: {match.group(0).strip()}")

# Look for actual search query confirmation
query_match = re.search(r'search.*?for.*?["\'](.+?)["\']', page_text, re.IGNORECASE)
if query_match:
    print(f"\nSearch query on page: '{query_match.group(1)}'")

print("\n\n4. Checking for 'hp victus' in raw HTML...")
print("=" * 70)

# Check if "hp victus" or "victus" appears anywhere in the HTML
if 'hp victus' in html.lower():
    print("✓ 'hp victus' found in HTML")
    # Find the context
    start_idx = html.lower().find('hp victus')
    context = html[max(0, start_idx-100):start_idx+200]
    print(f"\nContext:\n{context}")
elif 'victus' in html.lower():
    print("✓ 'victus' found in HTML (but not 'hp victus')")
    # Count occurrences
    count = html.lower().count('victus')
    print(f"  Occurrences: {count}")
    
    # Find first occurrence context
    start_idx = html.lower().find('victus')
    context = html[max(0, start_idx-50):start_idx+150]
    print(f"\nFirst context:\n{context[:200]}")
else:
    print("✗ 'victus' NOT found in HTML")
    print("\n⚠️  This suggests the search returned 0 actual results,")
    print("    and the page is showing recommended/popular products instead")

print("\n" + "=" * 70)
