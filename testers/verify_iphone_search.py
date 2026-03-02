"""Quick test to verify iphone 17 search still works"""

import requests

BASE_URL = "http://localhost:8000/api"

print("Testing 'iphone 17' search to verify fix didn't break existing functionality...")

response = requests.post(f"{BASE_URL}/search/outgeeked", json={"query": "iphone 17"}, timeout=30)

if response.status_code == 200:
    data = response.json()
    print(f"✓ Status: {response.status_code}")
    print(f"✓ Found {len(data['offers'])} products")
    
    if data['offers']:
        print(f"✓ First product: {data['offers'][0]['title'][:60]}")
        print(f"✓ Price: ${float(data['offers'][0]['item_price']):.2f}")
        print("\n✅ Original search still works!")
    else:
        print("❌ No products found (regression!)")
else:
    print(f"❌ Failed: {response.status_code}")
    print(response.text)
