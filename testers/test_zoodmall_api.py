"""Test ZoodMall adapter through Django API"""

import requests
import time

BASE_URL = "http://localhost:8000/api"

print("=" * 70)
print("COMPREHENSIVE ZOODMALL API TEST")
print("=" * 70)

# Wait for Django to start
print("\nWaiting for Django to start...")
time.sleep(3)

# Test 1: Verify adapter is registered
print("\n1. Verifying ZoodMall adapter is registered...")
print("=" * 70)

try:
    response = requests.get(f"{BASE_URL}/sources/", timeout=10)
    if response.status_code == 200:
        sources = response.json()
        if 'zoodmall' in str(sources).lower():
            print("✓ ZoodMall adapter is registered")
        else:
            print("⚠️  ZoodMall not found in sources (this endpoint may not exist)")
except:
    print("⚠️  Could not check sources endpoint (may not be implemented)")

# Test 2: Search
print("\n2. Testing Search Endpoint...")
print("=" * 70)

search_payload = {"query": "iphone"}

try:
    response = requests.post(f"{BASE_URL}/search/zoodmall", json=search_payload, timeout=60)
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        
        print(f"✓ Search successful")
        print(f"  Query: {data.get('query', 'N/A')}")
        print(f"  Source: {data.get('source', 'N/A')}")
        print(f"  Status: {data.get('status', 'N/A')}")
        print(f"  Offers found: {len(data.get('offers', []))}")
        
        if data.get('offers'):
            print("\n  Sample Products:")
            for i, offer in enumerate(data['offers'][:5], 1):
                print(f"    {i}. {offer['title'][:60]}")
                print(f"       Price: ${float(offer['item_price']):.2f}")
            
            # Test 3: Product Details
            print("\n" + "=" * 70)
            print("3. Testing Product Details...")
            print("=" * 70)
            
            test_product = data['offers'][0]
            details_payload = {
                "product_url": test_product['url'],
                "location": "beirut"
            }
            
            print(f"\n  Product: {test_product['title'][:60]}")
            
            response2 = requests.post(
                f"{BASE_URL}/product-details/zoodmall",
                json=details_payload,
                timeout=60
            )
            
            print(f"  Status: {response2.status_code}")
            
            if response2.status_code == 200:
                details = response2.json()
                
                print(f"\n✓ Details retrieved")
                print(f"  Base Price: ${float(details['item_price']):.2f}")
                print(f"  Shipping: ${float(details['shipping_fee']):.2f}")
                print(f"  Taxes: ${float(details.get('tax_amount', 0)):.2f}")
                print(f"  Total: ${float(details ['total_price']):.2f}")
                print(f"  Delivery: {details['delivery_time']}")
                
                # Verify calculation
                expected_total = float(details['item_price']) + float(details['shipping_fee']) + float(details.get('tax_amount', 0))
                actual_total = float(details['total_price'])
                
                if abs(actual_total - expected_total) < 0.01:
                    print("\n  ✓ Price calculation verified")
                else:
                    print(f"\n  ⚠️  Price mismatch: expected ${expected_total:.2f}, got ${actual_total:.2f}")
                
                # Test 4: Verify ZoodMall Rules
                print("\n" + "=" * 70)
                print("4. Verifying ZoodMall Rules...")
                print("=" * 70)
                
                assert float(details['shipping_fee']) == 5.0, "Shipping should be $5.00"
                print("  ✓ Shipping: $5.00 (international)")
                
                assert float(details.get('tax_amount', 0)) == 0.0, "Taxes should be $0.00"
                print("  ✓ Taxes: $0.00")
                
                assert details['delivery_time'] == "7-14 days", "Delivery should be 7-14 days"
                print("  ✓ Delivery: 7-14 days (international)")
                
                print("\n" + "=" * 70)
                print("✅ ALL API TESTS PASSED!")
                print("=" * 70)
                print("\nZoodMall adapter is fully functional via API:")
                print("  ✓ Search working")
                print("  ✓ Product details working")
                print("  ✓ Pricing rules correct")
                print("=" * 70)
            else:
                print(f"\n❌ Product details failed: {response2.status_code}")
                print(response2.text)
        else:
            print("\n⚠️  No offers found")
    else:
        print(f"❌ Search failed: {response.status_code}")
        print(response.text)
        
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
