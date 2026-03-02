"""Find the actual search results section in OutGeeked HTML"""

from bs4 import BeautifulSoup

with open('testers/outgeeked_hp_victus_search.html', 'r', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')

print("=" * 70)
print("FINDING SEARCH RESULTS SECTION")
print("=" * 70)

# The HP Victus links have query parameters with _pos, _sid, _ss
# Let's find their parent containers

victus_links = soup.find_all('a', href=lambda x: x and 'hp-victus' in x.lower())

print(f"\nFound {len(victus_links)} links with 'hp-victus' in URL")

if victus_links:
    print("\n" + "=" * 70)
    print("ANALYZING FIRST HP VICTUS PRODUCT STRUCTURE")
    print("=" * 70)
    
    first_link = victus_links[0]
    print(f"\nLink text: {first_link.get_text(strip=True)[:80]}")
    print(f"Link URL: {first_link.get('href')}")
    print(f"Link classes: {first_link.get('class')}")
    
    # Find parent containers
    print("\n" + "=" * 70)
    print("PARENT STRUCTURE")
    print("=" * 70)
    
    current = first_link
    for level in range(1, 8):
        current = current.parent
        if current:
            tag = current.name
            classes = current.get('class', [])
            id_attr = current.get('id', '')
            
            print(f"\nLevel {level}: <{tag}>")
            if classes:
                print(f"  Classes: {', '.join(classes)}")
            if id_attr:
                print(f"  ID: {id_attr}")
            
            # Check if this is a product container
            if 'product' in str(classes).lower() or 'item' in str(classes).lower():
                print(f"  ⭐ This looks like a product container!")
                
                # Check what other content is in this container
                children = [child for child in current.children if child.name]
                print(f"  Children tags: {[child.name for child in children[:10]]}")
        else:
            break
    
    # Find the common parent of all HP Victus products
    print("\n" + "=" * 70)
    print("FINDING COMMON PARENT OF ALL SEARCH RESULTS")
    print("=" * 70)
    
    # Get parents of all HP Victus links at level 5 (likely the product container)
    product_containers = []
    for link in victus_links[:4]:  # First 4 (the actual products, not "View details")
        if 'hp victus' in link.get_text(strip=True).lower():
            current = link
            for _ in range(5):  # Go up 5 levels
                current = current.parent
                if not current:
                    break
            if current:
                product_containers.append(current)
    
    if product_containers:
        print(f"\nFound {len(product_containers)} product containers")
        first_container = product_containers[0]
        
        print(f"\nProduct container:")
        print(f"  Tag: {first_container.name}")
        print(f"  Classes: {first_container.get('class')}")
        print(f"  ID: {first_container.get('id')}")
        
        # Check if all containers share a common parent
        common_parent = product_containers[0].parent
        print(f"\nCommon parent of all products:")
        print(f"  Tag: {common_parent.name}")
        print(f"  Classes: {common_parent.get('class')}")
        print(f"  ID: {common_parent.get('id')}")
        
        # Count how many similar product containers are in the common parent
        if 'class' in product_containers[0].attrs:
            similar_containers = common_parent.find_all(
                product_containers[0].name,
                class_=product_containers[0].get('class')
            )
            print(f"  Total similar containers in parent: {len(similar_containers)}")

# Alternative: Search for the search results grid/list
print("\n" + "=" * 70)
print("LOOKING FOR SEARCH RESULTS GRID")
print("=" * 70)

# Find divs that contain the HP Victus products
search_sections = soup.find_all('div', class_=lambda x: x and ('search' in str(x).lower() or 'predictive' in str(x).lower() or 'results' in str(x).lower()))

for section in search_sections[:5]:
    hp_in_section = section.find_all('a', href=lambda x: x and 'hp-victus' in x.lower())
    if hp_in_section:
        print(f"\n✓ Found section with HP Victus products!")
        print(f"  Tag: {section.name}")
        print(f"  Classes: {section.get('class')}")
        print(f"  ID: {section.get('id')}")
        print(f"  HP Victus products in this section: {len(hp_in_section)}")

print("\n" + "=" * 70)
