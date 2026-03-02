"""Test OutGeeked adapter through Django API"""

import requests
import json

BASE_URL = "http://localhost:8000/api"

def test_outgeeked_api():
    print("=" * 70)
    print("COMPREHENSIVE OUTGEEKED API TEST")
    print("=" * 70)
    
    # 1. Test Search
    print("\n1. Testing Search Endpoint...")
    search_payload = {"query": "iphone 17"}
    response = requests.post(f"{BASE_URL}/search/outgeeked", json=search_payload, timeout=30)
    
    assert response.status_code == 200, f"Search failed: {response.status_code}"
    data = response.json()
    
    print(f"✓ Search successful")
    print(f"  Query: {data['query']}")
    print(f"  Source: {data['source']}")
    print(f"  Status: {data['status']}")
    print(f"  Offers found: {len(data['offers'])}")
    
    assert len(data['offers']) > 0, "No offers returned"
    assert data['source'] == 'outgeeked', "Wrong source"
    assert data['status'] == 'DONE', "Search not completed"
    
    # Show sample products
    print("\n  Sample Products:")
    for i, offer in enumerate(data['offers'][:5], 1):
        print(f"    {i}. {offer['title'][:60]}")
        print(f"       Price: ${float(offer['item_price']):.2f}")
        print(f"       In Stock: {offer['in_stock']}")
    
    # 2. Test Product Details - Inside Beirut
    print("\n" + "=" * 70)
    print("2. Testing Product Details (Inside Beirut)...")
    print("=" * 70)
    
    test_product = data['offers'][0]
    details_payload = {
        "product_url": test_product['url'],
        "location": "inside beirut"
    }
    
    print(f"\n  Product: {test_product['title'][:60]}")
    
    response2 = requests.post(
        f"{BASE_URL}/product-details/outgeeked", 
        json=details_payload,
        timeout=30
    )
    
    assert response2.status_code == 200, f"Details failed: {response2.status_code}"
    details_inside = response2.json()
    
    print(f"\n✓ Details retrieved (Inside Beirut)")
    print(f"  Base Price: ${float(details_inside['item_price']):.2f}")
    print(f"  Shipping: ${float(details_inside['shipping_fee']):.2f}")
    print(f"  Taxes: ${float(details_inside.get('tax_amount', 0)):.2f}")
    print(f"  Total: ${float(details_inside['total_price']):.2f}")
    print(f"  Delivery: {details_inside['delivery_time']}")
    
    # 3. Test Product Details - Outside Beirut
    print("\n" + "=" * 70)
    print("3. Testing Product Details (Outside Beirut)...")
    print("=" * 70)
    
    details_payload['location'] = "outside beirut"
    
    response3 = requests.post(
        f"{BASE_URL}/product-details/outgeeked",
        json=details_payload,
        timeout=30
    )
    
    assert response3.status_code == 200, f"Details failed: {response3.status_code}"
    details_outside = response3.json()
    
    print(f"\n✓ Details retrieved (Outside Beirut)")
    print(f"  Base Price: ${float(details_outside['item_price']):.2f}")
    print(f"  Shipping: ${float(details_outside['shipping_fee']):.2f}")
    print(f"  Taxes: ${float(details_outside.get('tax_amount', 0)):.2f}")
    print(f"  Total: ${float(details_outside['total_price']):.2f}")
    print(f"  Delivery: {details_outside['delivery_time']}")
    
    # 4. Verify Fixed Rules
    print("\n" + "=" * 70)
    print("4. Verifying OutGeeked Rules...")
    print("=" * 70)
    
    # Shipping should be $3 for both
    assert float(details_inside['shipping_fee']) == 3.0, "Shipping should be $3"
    assert float(details_outside['shipping_fee']) == 3.0, "Shipping should be $3"
    print("  ✓ Flat rate shipping: $3.00")
    
    # No taxes
    assert float(details_inside.get('tax_amount', 0)) == 0.0, "Taxes should be $0"
    assert float(details_outside.get('tax_amount', 0)) == 0.0, "Taxes should be $0"
    print("  ✓ Taxes: $0.00")
    
    # Delivery times based on location
    assert details_inside['delivery_time'] == "2-5 days", "Inside Beirut should be 2-5 days"
    assert details_outside['delivery_time'] == "5-7 days", "Outside Beirut should be 5-7 days"
    print("  ✓ Delivery inside Beirut: 2-5 days")
    print("  ✓ Delivery outside Beirut: 5-7 days")
    
    # Total calculation
    expected_total = float(details_inside['item_price']) + 3.0
    actual_total = float(details_inside['total_price'])
    assert abs(actual_total - expected_total) < 0.01, "Total calculation wrong"
    print(f"  ✓ Total = Base + $3 (${float(details_inside['item_price']):.2f} + $3.00 = ${actual_total:.2f})")
    
    # 5. Test Multiple Locations
    print("\n" + "=" * 70)
    print("5. Testing Multiple Locations...")
    print("=" * 70)
    
    test_locations = {
        "Beirut": "2-5 days",
        "Tripoli": "5-7 days",
        "Sidon": "5-7 days",
        "Zahle": "5-7 days",
    }
    
    for location, expected_delivery in test_locations.items():
        details_payload['location'] = location
        response4 = requests.post(
            f"{BASE_URL}/product-details/outgeeked",
            json=details_payload,
            timeout=30
        )
        
        assert response4.status_code == 200
        loc_details = response4.json()
        
        assert float(loc_details['shipping_fee']) == 3.0, f"Shipping in {location} should be $3"
        assert loc_details['delivery_time'] == expected_delivery, f"Wrong delivery for {location}"
        
        print(f"  ✓ {location}: $3 shipping, {expected_delivery}")
    
    print("\n" + "=" * 70)
    print("✅ ALL API TESTS PASSED!")
    print("=" * 70)
    print("\nOutGeeked adapter is fully functional via API:")
    print("  ✓ Search endpoint working")
    print("  ✓ Product details endpoint working")
    print("  ✓ Flat rate shipping: $3")
    print("  ✓ Location-based delivery times")
    print("  ✓ No taxes applied")
    print("=" * 70)


if __name__ == "__main__":
    try:
        test_outgeeked_api()
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
