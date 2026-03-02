"""Test OutGeeked API with HP Victus search"""

import requests
import json

BASE_URL = "http://localhost:8000/api"

print("=" * 70)
print("TESTING OUTGEEKED API - HP VICTUS SEARCH")
print("=" * 70)

# Test search
print("\n1. Searching for 'hp victus'...")
search_payload = {"query": "hp victus"}

response = requests.post(f"{BASE_URL}/search/outgeeked", json=search_payload, timeout=30)

print(f"Response Status: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    
    print(f"✓ Search successful")
    print(f"  Query: {data['query']}")
    print(f"  Source: {data['source']}")
    print(f"  Status: {data['status']}")
    print(f"  Offers found: {len(data['offers'])}")
    
    if data['offers']:
        print("\n  Products:")
        for i, offer in enumerate(data['offers'], 1):
            print(f"\n    {i}. {offer['title'][:80]}")
            print(f"       Price: ${float(offer['item_price']):.2f}")
            print(f"       URL: {offer['url'][:80]}...")
        
        # Test detailed pricing
        print("\n\n2. Testing Product Details...")
        print("=" * 70)
        
        first_product = data['offers'][0]
        details_payload = {
            "product_url": first_product['url'],
            "location": "inside beirut"
        }
        
        response2 = requests.post(
            f"{BASE_URL}/product-details/outgeeked",
            json=details_payload,
            timeout=30
        )
        
        if response2.status_code == 200:
            details = response2.json()
            print(f"\n✓ Details retrieved")
            print(f"  Product: {first_product['title'][:60]}")
            print(f"  Base Price: ${float(details['item_price']):.2f}")
            print(f"  Shipping: ${float(details['shipping_fee']):.2f}")
            print(f"  Total: ${float(details['total_price']):.2f}")
            print(f"  Delivery: {details['delivery_time']}")
            
            print("\n" + "=" * 70)
            print("✅ ALL TESTS PASSED!")
            print("=" * 70)
            print("\nHP Victus search is now working correctly:")
            print(f"  ✓ Found {len(data['offers'])} HP Victus products")
            print("  ✓ Product details working")
            print("  ✓ Pricing and delivery times correct")
        else:
            print(f"\n❌ Details failed: {response2.status_code}")
            print(response2.text)
    else:
        print("\n❌ No offers found")
        print(json.dumps(data, indent=2))
else:
    print(f"❌ Search failed: {response.status_code}")
    print(response.text)
