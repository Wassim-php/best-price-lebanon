"""Test ZoodMall with samsung a56 search via API"""

import requests
import time

BASE_URL = "http://localhost:8000/api"

print("=" * 70)
print("TESTING ZOODMALL - SAMSUNG A56 SEARCH")
print("=" * 70)

print("\nWaiting for Django to start...")
time.sleep(5)

print("\nSearching for 'samsung a56'...")
search_payload = {"query": "samsung a56"}

try:
    response = requests.post(
        f"{BASE_URL}/search/zoodmall",
        json=search_payload,
        timeout=90  # Increased timeout for retries
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
            for i, offer in enumerate(data['offers'][:5], 1):
                print(f"    {i}. {offer['title'][:70]}")
                print(f"       ${float(offer['item_price']):.2f}")
        else:
            print("\n  ⚠️  No products found (Cloudflare may be blocking)")
    else:
        print(f"\n❌ Error: {response.status_code}")
        try:
            error_data = response.json()
            print(f"  Message: {error_data.get('error', 'Unknown error')}")
        except:
            print(f"  Response: {response.text[:200]}")
            
except requests.exceptions.Timeout:
    print("\n⏱️  Request timed out (server may be processing)")
except Exception as e:
    print(f"\n❌ Exception: {e}")

print("\n" + "=" * 70)
print("Note: ZoodMall has strong Cloudflare protection that may block")
print("requests from Docker containers. This works locally but requires")
print("a proxy service (like ScraperAPI or Bright Data) for production.")
print("=" * 70)
