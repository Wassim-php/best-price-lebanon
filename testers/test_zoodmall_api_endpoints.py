"""Test all ZoodMall API endpoints"""

import requests
import json

BASE_URL = "http://localhost:8000/api"

print("=" * 70)
print("TESTING ZOODMALL API ENDPOINTS")
print("=" * 70)

# Test 1: Search endpoint
print("\n1. Testing /api/search/zoodmall")
print("-" * 70)
try:
    response = requests.post(
        f"{BASE_URL}/search/zoodmall",
        json={"query": "samsung a56"},
        timeout=180
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Query: {data.get('query')}")
        print(f"✓ Source: {data.get('source')}")
        print(f"✓ Offers: {len(data.get('offers', []))}")
    else:
        print(f"✗ Error: {response.text[:200]}")
except Exception as e:
    print(f"✗ Exception: {e}")

# Test 2: Search with details endpoint
print("\n2. Testing /api/search-with-details/zoodmall")
print("-" * 70)
try:
    response = requests.post(
        f"{BASE_URL}/search-with-details/zoodmall",
        json={"query": "samsung a56", "location": "outside beirut"},
        timeout=180
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Query: {data.get('query')}")
        print(f"✓ Source: {data.get('source')}")
        if 'product' in data:
            print(f"✓ Product: {data['product'].get('title', 'N/A')[:60]}")
        if 'pricing' in data:
            pricing = data['pricing']
            print(f"✓ Base Price: ${pricing.get('base_price', 0)}")
            print(f"✓ Shipping: ${pricing.get('shipping_fee', 0)}")
            print(f"✓ Total: ${pricing.get('total_price', 0)}")
    else:
        print(f"✗ Error: {response.text[:200]}")
except Exception as e:
    print(f"✗ Exception: {e}")

# Test 3: Product details endpoint (if we have a URL)
print("\n3. Testing /api/product-details/zoodmall")
print("-" * 70)
print("(Requires product URL - skipping for now)")

# Test 4: Check available sources
print("\n4. Testing source availability")
print("-" * 70)
try:
    response = requests.post(
        f"{BASE_URL}/search/zoodmall",
        json={"query": "test"},
        timeout=30
    )
    if response.status_code == 404:
        print("✗ ZoodMall source not registered")
    else:
        print("✓ ZoodMall source is available")
except Exception as e:
    print(f"? Could not verify: {e}")

print("\n" + "=" * 70)
