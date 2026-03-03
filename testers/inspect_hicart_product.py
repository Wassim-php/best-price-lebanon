import requests
from bs4 import BeautifulSoup

# Test a product detail page
# From the search, I can see product names with links
search_url = "https://www.hicart.com/catalogsearch/result/?q=iphone"
base_url = "https://www.hicart.com"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
}

print("=" * 70)
print("FETCHING PRODUCT DETAIL PAGE")
print("=" * 70)

# First get search page to find a product link
r = requests.get(search_url, headers=headers, timeout=15)
if r.status_code == 200:
    soup = BeautifulSoup(r.text, 'lxml')
    
    # Find first product link
    product_name = soup.find('h2', class_='product-name')
    if product_name:
        product_link = product_name.find('a')
        if product_link and product_link.get('href'):
            product_url = product_link['href']
            if not product_url.startswith('http'):
                product_url = base_url + product_url
            
            print(f"Product: {product_link.get_text().strip()}")
            print(f"URL: {product_url}\n")
            
            # Fetch product detail page
            r2 = requests.get(product_url, headers=headers, timeout=15)
            if r2.status_code == 200:
                soup2 = BeautifulSoup(r2.text, 'lxml')
                
                # Save to file
                with open('testers/hicart_product_page.html', 'w', encoding='utf-8') as f:
                    f.write(soup2.prettify())
                print("✓ Saved product page HTML to testers/hicart_product_page.html\n")
                
                print("=" * 70)
                print("PRODUCT PAGE ANALYSIS")
                print("=" * 70)
                
                # Title
                title = soup2.find('h1', class_='product-name')
                if not title:
                    title = soup2.find('h1')
                if title:
                    print(f"\nProduct Title:")
                    print(f"  {title.get_text().strip()}")
                
                # Price
                price_box = soup2.find('div', class_='price-box')
                if price_box:
                    print(f"\nPrice Box HTML:")
                    print(price_box.prettify()[:500])
                    
                    regular_price = price_box.find('span', class_='regular-price')
                    if regular_price:
                        price = regular_price.find('span', class_='price')
                        if price:
                            print(f"\n✓ Regular Price: {price.get_text().strip()}")
                    
                    special_price = price_box.find('span', class_='special-price')
                    if special_price:
                        price = special_price.find('span', class_='price')
                        if price:
                            print(f"✓ Special Price: {price.get_text().strip()}")
                
                # Look for meta tags with price
                meta_price = soup2.find('meta', property='product:price:amount')
                if meta_price:
                    print(f"\n✓ Meta price: {meta_price.get('content')}")
                
                # Description
                desc = soup2.find('div', class_='short-description')
                if desc:
                    print(f"\nShort Description:")
                    print(f"  {desc.get_text().strip()[:200]}")
                
                # Availability
                availability = soup2.find('p', class_='availability')
                if not availability:
                    availability = soup2.find(class_=lambda x: x and 'availability' in x.lower() if x else False)
                if availability:
                    print(f"\nAvailability: {availability.get_text().strip()}")
                
                # SKU
                sku = soup2.find(class_=lambda x: x and 'sku' in x.lower() if x else False)
                if sku:
                    print(f"SKU: {sku.get_text().strip()}")
                
            else:
                print(f"Failed to fetch product page: {r2.status_code}")
        else:
            print("No product link found")
    else:
        print("No product name found")
else:
    print(f"Failed to fetch search page: {r.status_code}")

print("\n" + "=" * 70)
print("COMPLETE")
print("=" * 70)
