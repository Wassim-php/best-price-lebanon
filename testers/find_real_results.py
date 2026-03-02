"""Find actual search results with query parameters"""

from bs4 import BeautifulSoup

with open('testers/outgeeked_hp_victus_search.html', 'r', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')

print("=" * 70)
print("FINDING ACTUAL SEARCH RESULTS (with _pos parameter)")
print("=" * 70)

# Find links with _pos parameter (these are the actual search results)
search_result_links = soup.find_all('a', href=lambda x: x and '_pos=' in x and '/products/' in x)

print(f"\nFound {len(search_result_links)} search result links (with _pos parameter)")

if search_result_links:
    # Get unique products (filter out duplicates like "View details")
    unique_products = {}
    for link in search_result_links:
        url = link.get('href', '')
        # Extract product slug from URL
        if '/products/' in url:
            product_slug = url.split('/products/')[1].split('?')[0]
            if product_slug not in unique_products:
                unique_products[product_slug] = link
    
    print(f"Unique products: {len(unique_products)}")
    
    print("\n" + "=" * 70)
    print("ANALYZING SEARCH RESULT STRUCTURE")
    print("=" * 70)
    
    # Analyze the first search result
    first_result = list(unique_products.values())[0]
    print(f"\nFirst result link:")
    print(f"  Text: {first_result.get_text(strip=True)[:80]}")
    print(f"  URL: {first_result.get('href')}")
    print(f"  Classes: {first_result.get('class')}")
    
    # Find parent structure
    print("\n" + "=" * 70)
    print("PARENT STRUCTURE OF SEARCH RESULT")
    print("=" * 70)
    
    current = first_result
    product_container = None
    
    for level in range(1, 10):
        current = current.parent
        if not current:
            break
            
        tag = current.name
        classes = current.get('class', [])
        id_attr = current.get('id', '')
        
        print(f"\nLevel {level}: <{tag}>")
        if classes:
            print(f"  Classes: {', '.join(classes)}")
        if id_attr:
            print(f"  ID: {id_attr}")
        
        # Look for a container that has all search results
        if not product_container:
            # Check if this container has links with _pos
            links_in_container = current.find_all('a', href=lambda x: x and '_pos=' in x and '/products/' in x)
            unique_links = set()
            for l in links_in_container:
                url = l.get('href', '')
                if '/products/' in url:
                    slug = url.split('/products/')[1].split('?')[0]
                    unique_links.add(slug)
            
            if len(unique_links) >= 3:  # If it contains most/all results
                product_container = current
                print(f"  ⭐ SEARCH RESULTS CONTAINER! ({len(unique_links)} unique products)")
    
    if product_container:
        print("\n" + "=" * 70)
        print("SEARCH RESULTS CONTAINER DETAILS")
        print("=" * 70)
        print(f"Tag: {product_container.name}")
        print(f"Classes: {product_container.get('class')}")
        print(f"ID: {product_container.get('id')}")
        
        # Find what selector we should use
        print("\n" + "=" * 70)
        print("RECOMMENDED SELECTOR")
        print("=" * 70)
        
        child_selector = None
        
        # Check for common patterns
        if product_container.get('class'):
            class_name = ' '.join(product_container.get('class'))
            print(f"\nOption 1: Find by class")
            print(f"  container = soup.find('div', class_='{class_name}')")
            print(f"  products = container.find_all('a', href=lambda x: x and '/products/' in x and '_pos=' in x)")
        
        if product_container.get('id'):
            print(f"\nOption 2: Find by ID")
            print(f"  container = soup.find(id='{product_container.get('id')}')")
        
        # Find the direct children that contain product info
        direct_children = [child for child in product_container.children if child.name]
        print(f"\nDirect children count: {len(direct_children)}")
        if direct_children:
            first_child = direct_children[0]
            print(f"First child: <{first_child.name}> classes={first_child.get('class')}")
            
            # Check if each child corresponds to one product
            child_with_link = [child for child in direct_children if child.find('a', href=lambda x: x and '/products/' in x and '_pos=' in x)]
            print(f"Children with product links: {len(child_with_link)}")

# Alternative: Look for predictive search results
print("\n\n" + "=" * 70)
print("CHECKING FOR PREDICTIVE SEARCH SECTION")
print("=" * 70)

predictive = soup.find('div', class_=lambda x: x and 'predictive-search' in str(x).lower())
if predictive:
    print("✓ Found predictive-search div")
    print(f"  Classes: {predictive.get('class')}")
    print(f"  ID: {predictive.get('id')}")
    
    # Check if it contains search results
    predictive_products = predictive.find_all('a', href=lambda x: x and '_pos=' in x and '/products/' in x)
    unique_predictive = set()
    for link in predictive_products:
        url = link.get('href', '')
        if '/products/' in url:
            slug = url.split('/products/')[1].split('?')[0]
            unique_predictive.add(slug)
    
    print(f"  Products found: {len(unique_predictive)}")
    
    if unique_predictive:
        print("\n  Products:")
        for i, slug in enumerate(unique_predictive, 1):
            print(f"    {i}. {slug}")
else:
    print("✗ No predictive-search div found")

print("\n" + "=" * 70)
