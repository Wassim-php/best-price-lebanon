import requests
from bs4 import BeautifulSoup
from urllib.parse import quote

# HiCart search - Magento-based site
search_query = "iphone 17"
base_url = "https://www.hicart.com"
search_url = f"{base_url}/catalogsearch/result/?q={quote(search_query)}"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
}

print("=" * 70)
print("INSPECTING HICART SEARCH RESULTS")
print("=" * 70)
print(f"URL: {search_url}\n")

try:
    r = requests.get(search_url, headers=headers, timeout=15)
    print(f"Status Code: {r.status_code}")
    print(f"Response Length: {len(r.text)} characters\n")
    
    if r.status_code == 200:
        soup = BeautifulSoup(r.text, 'lxml')
        
        # Page title
        title = soup.find('title')
        if title:
            print(f"Page Title: {title.get_text()}")
        
        print("\n" + "=" * 70)
        print("SEARCHING FOR PRODUCT CONTAINERS")
        print("=" * 70)
        
        # Common Magento product selectors
        selectors = [
            'li.product-item',
            'div.product-item',
            'li.item.product',
            'div.product',
            'ol.products.list li',
            'div.products.wrapper li',
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            if elements:
                print(f"\n✓ Found {len(elements)} products with selector: {selector}")
                
                # Analyze first product
                first = elements[0]
                print("\nFirst Product HTML Structure:")
                print(first.prettify()[:1500])
                
                # Look for product name
                name_selectors = [
                    'a.product-item-link',
                    'h2.product-name a',
                    'a.product.name',
                    'span.product-name',
                    'h3.product-item-name a',
                ]
                
                for ns in name_selectors:
                    name = first.select_one(ns)
                    if name:
                        print(f"\n✓ Product Name Selector: {ns}")
                        print(f"  Text: {name.get_text().strip()}")
                        print(f"  Link: {name.get('href', 'N/A')}")
                
                # Look for price
                price_selectors = [
                    'span.price',
                    'span.regular-price span.price',
                    'span.special-price span.price',
                    'div.price-box span.price',
                    'span.price-wrapper',
                ]
                
                for ps in price_selectors:
                    price = first.select_one(ps)
                    if price:
                        print(f"\n✓ Price Selector: {ps}")
                        print(f"  Text: {price.get_text().strip()}")
                
                break
        else:
            print("\n✗ No products found with common selectors")
            print("\nShowing page structure (first 2000 chars):")
            print(soup.prettify()[:2000])
        
        print("\n" + "=" * 70)
        print("TESTING PRODUCT DETAIL PAGE")
        print("=" * 70)
        
        # Try a sample product page
        test_products = soup.select('a.product-item-link, a[href*="/product"]')
        if test_products:
            product_url = test_products[0].get('href')
            if not product_url.startswith('http'):
                product_url = base_url + product_url
            
            print(f"\nTesting product page: {product_url}")
            
            r2 = requests.get(product_url, headers=headers, timeout=15)
            if r2.status_code == 200:
                soup2 = BeautifulSoup(r2.text, 'lxml')
                
                print("\nProduct Page Selectors:")
                
                # Price
                price_selectors = [
                    'span.price',
                    'meta[property="product:price:amount"]',
                    'div.price-box span.price',
                ]
                
                for ps in price_selectors:
                    if ps.startswith('meta'):
                        price = soup2.select_one(ps)
                        if price:
                            print(f"✓ Price (meta): {ps} = {price.get('content')}")
                    else:
                        price = soup2.select_one(ps)
                        if price:
                            print(f"✓ Price: {ps} = {price.get_text().strip()}")
                
                # Title
                title_selectors = [
                    'h1.page-title',
                    'span.base',
                    'h1.product-name',
                ]
                
                for ts in title_selectors:
                    title = soup2.select_one(ts)
                    if title:
                        print(f"✓ Title: {ts} = {title.get_text().strip()[:50]}")
        
    else:
        print(f"Failed to fetch page. Status: {r.status_code}")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("INSPECTION COMPLETE")
print("=" * 70)
