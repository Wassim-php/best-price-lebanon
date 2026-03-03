import requests
from bs4 import BeautifulSoup

# Try different potential domain variations for HiCart
potential_domains = [
    "https://hicart.com.lb",
    "https://www.hicart.com.lb",
    "https://hicart.lb",
    "https://www.hicart.lb",
    "https://hi-cart.com.lb",
    "https://www.hi-cart.com.lb",
    "https://hicart.com",
    "https://www.hicart.com",
]

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
}

print("=" * 70)
print("TESTING HICART DOMAIN VARIATIONS")
print("=" * 70)

working_domain = None

for domain in potential_domains:
    try:
        print(f"\nTrying: {domain}")
        r = requests.get(domain, headers=headers, timeout=10, allow_redirects=True)
        print(f"✓ Status: {r.status_code}")
        print(f"✓ Final URL: {r.url}")
        
        soup = BeautifulSoup(r.text, 'lxml')
        title = soup.find('title')
        if title:
            print(f"✓ Page title: {title.get_text()[:100]}")
        
        # Check if this is actually HiCart
        page_text = r.text.lower()
        if 'hicart' in page_text or 'hi cart' in page_text or 'hi-cart' in page_text:
            print(f"✓✓✓ This appears to be HiCart! ✓✓✓")
            working_domain = r.url
            break
        else:
            print("⚠ Doesn't seem to be HiCart")
            
    except requests.exceptions.SSLError as e:
        print(f"✗ SSL Error")
    except requests.exceptions.ConnectionError as e:
        print(f"✗ Connection Error (domain doesn't exist)")
    except requests.exceptions.Timeout:
        print(f"✗ Timeout")
    except Exception as e:
        print(f"✗ Error: {type(e).__name__}")

print("\n" + "=" * 70)
if working_domain:
    print(f"✓ Working domain found: {working_domain}")
else:
    print("✗ Could not find working HiCart domain")
    print("\nPlease provide the correct HiCart website URL")
print("=" * 70)
