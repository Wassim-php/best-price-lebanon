"""Test ZoodMall search through Docker with longer timeout"""

import requests
import time

BASE_URL = "http://localhost:8000/api"

print("=" * 70)
print("TESTING ZOODMALL SELENIUM - SAMSUNG A56")
print("=" * 70)

print("\nSearching for 'samsung a56' (Selenium may take 15-30 seconds)...")
search_payload = {"query": "samsung a56"}

try:
    # Increased timeout for Selenium (much slower than requests)
    response = requests.post(
        f"{BASE_URL}/search/zoodmall",
        json=search_payload,
        timeout=180  # 3 minutes for Selenium
    )
    
    print(f"\nResponse Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        
        print(f"✓ Success!")
        print(f"  Query: {data.get('query', 'N/A')}")
        print(f"  Source: {data.get('source', 'N/A')}")
        print(f"  Offers: {len(data.get('offers', []))}")
        
        if data.get('offers'):
            print("\n  Products found:")
            for i, offer in enumerate(data['offers'][:10], 1):
                print(f"    {i}. {offer['title'][:70]}")
                print(f"       ${float(offer['item_price']):.2f} + ${float(offer['shipping_fee']):.2f} = ${float(offer['total_price']):.2f}")
        else:
            print("\n  ⚠️  No products found")
    else:
        print(f"\n❌ Error: {response.status_code}")
        try:
            error_data = response.json()
            print(f"  Message: {error_data.get('error',  'Unknown error')}")
        except:
            print(f"  Response: {response.text[:500]}")
            
except requests.exceptions.Timeout:
    print("\n⏱️  Request timed out after 3 minutes")
    print("   This might indicate ChromeDriver issues in Docker")
except Exception as e:
    print(f"\n❌ Exception: {e}")

print("\n" + "=" * 70)
