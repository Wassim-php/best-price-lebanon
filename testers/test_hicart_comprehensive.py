"""Comprehensive test for HiCart adapter - search and details"""

import requests
import json

BASE_URL = "http://localhost:8000/api"

def test_hicart_comprehensive():
    print("=" * 70)
    print("COMPREHENSIVE HICART ADAPTER TEST")
    print("=" * 70)
    
    # 1. Test Search
    print("\n1. Testing Search Endpoint...")
    search_payload = {"query": "iphone 17"}
    response = requests.post(f"{BASE_URL}/search/hicart", json=search_payload, timeout=30)
    
    assert response.status_code == 200, f"Search failed: {response.status_code}"
    data = response.json()
    
    print(f"✓ Search successful")
    print(f"  Query: {data['query']}")
    print(f"  Source: {data['source']}")
    print(f"  Status: {data['status']}")
    print(f"  Offers found: {len(data['offers'])}")
    
    assert len(data['offers']) > 0, "No offers returned"
    assert data['source'] == 'hicart', "Wrong source"
    assert data['status'] == 'DONE', "Search not completed"
    
    # Show sample products
    print("\n  Sample Products:")
    for i, offer in enumerate(data['offers'][:5], 1):
        print(f"    {i}. {offer['title'][:60]}")
        print(f"       Price: ${float(offer['item_price']):.2f}")
        print(f"       In Stock: {offer['in_stock']}")
    
    # 2. Test Product Details
    print("\n" + "=" * 70)
    print("2. Testing Product Details Endpoint...")
    print("=" * 70)
    
    test_product = data['offers'][0]
    details_payload = {
        "product_url": test_product['url'],
        "location": "Beirut"
    }
    
    print(f"\n  Product: {test_product['title'][:60]}")
    print(f"  URL: {test_product['url'][:70]}...")
    
    response2 = requests.post(
        f"{BASE_URL}/product-details/hicart", 
        json=details_payload,
        timeout=30
    )
    
    assert response2.status_code == 200, f"Details failed: {response2.status_code}"
    details = response2.json()
    
    print(f"\n✓ Details retrieved successfully")
    print(f"  Base Price: ${float(details['item_price']):.2f}")
    print(f"  Shipping Fee: ${float(details['shipping_fee']):.2f}")
    print(f"  Taxes: ${float(details.get('tax_amount', 0)):.2f}")
    print(f"  Total Price: ${float(details['total_price']):.2f}")
    print(f"  Delivery: {details['delivery_time']}")
    print(f"  In Stock: {details['breakdown'].get('in_stock', True)}")
    
    # 3. Verify Fixed Rules
    print("\n" + "=" * 70)
    print("3. Verifying HiCart Fixed Rules...")
    print("=" * 70)
    
    assert float(details['shipping_fee']) == 4.0, "Shipping should always be $4"
    assert float(details.get('tax_amount', 0)) == 0.0, "Taxes should always be $0"
    assert details['delivery_time'] == "5 days", "Delivery should always be 5 days"
    
    # Verify total calculation
    expected_total = float(details['item_price']) + 4.0
    actual_total = float(details['total_price'])
    assert abs(actual_total - expected_total) < 0.01, f"Total calculation wrong: {actual_total} != {expected_total}"
    
    print("  ✓ Shipping fee: $4.00")
    print("  ✓ Taxes: $0.00")
    print("  ✓ Delivery time: 5 days")
    print(f"  ✓ Total = Base + Shipping (${float(details['item_price']):.2f} + $4.00 = ${actual_total:.2f})")
    
    # 4. Test with different location (should be same shipping)
    print("\n" + "=" * 70)
    print("4. Testing Different Locations...")
    print("=" * 70)
    
    for location in ["Tripoli", "Sidon", "Zahle"]:
        details_payload['location'] = location
        response3 = requests.post(
            f"{BASE_URL}/product-details/hicart",
            json=details_payload,
            timeout=30
        )
        
        assert response3.status_code == 200
        loc_details = response3.json()
        
        assert float(loc_details['shipping_fee']) == 4.0, f"Shipping in {location} should be $4"
        assert float(loc_details.get('tax_amount', 0)) == 0.0, f"Taxes in {location} should be $0"
        assert loc_details['delivery_time'] == "5 days", f"Delivery in {location} should be 5 days"
        
        print(f"  ✓ {location}: $4 shipping, $0 taxes, 5 days")
    
    print("\n" + "=" * 70)
    print("✅ ALL TESTS PASSED!")
    print("=" * 70)
    print("\nHiCart adapter is fully functional:")
    print("  ✓ Search returns products correctly")
    print("  ✓ Product details retrieved successfully")
    print("  ✓ Fixed rules applied correctly ($4, 0 taxes, 5 days)")
    print("  ✓ Location-independent pricing")
    print("=" * 70)


if __name__ == "__main__":
    try:
        test_hicart_comprehensive()
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
