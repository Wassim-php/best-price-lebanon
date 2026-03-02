"""Comprehensive test for OutGeeked adapter"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraping.adapters.websites.outgeeked import OutGeekedAdapter

def test_outgeeked():
    print("=" * 70)
    print("TESTING OUTGEEKED ADAPTER")
    print("=" * 70)
    
    adapter = OutGeekedAdapter()
    
    # Test 1: Search
    print("\n1. Testing search for 'iphone 17'...")
    results = adapter.search("iphone 17", limit=10)
    
    print(f"\nFound {len(results)} products")
    
    if results:
        print("\nFirst 5 results:")
        for i, product in enumerate(results[:5], 1):
            print(f"\n{i}. {product.title}")
            print(f"   Price: ${product.item_price:.2f}")
            print(f"   URL: {product.url[:80]}...")
            print(f"   In Stock: {product.in_stock}")
        
        # Test 2: Product Details - Inside Beirut
        print("\n" + "=" * 70)
        print("2. Testing get_detailed_pricing (Inside Beirut)...")
        print("=" * 70)
        
        first_product = results[0]
        print(f"\nFetching details for: {first_product.title}")
        
        details_inside = adapter.get_detailed_pricing(first_product.url, location="inside beirut")
        
        if details_inside and details_inside.get('item_price'):
            print("\n✓ Details (Inside Beirut):")
            print(f"  Name: {details_inside['breakdown'].get('title', 'N/A')}")
            print(f"  Base Price: ${details_inside['item_price']:.2f}")
            print(f"  Shipping Fee: ${details_inside['shipping_fee']:.2f}")
            print(f"  Taxes: ${details_inside['tax_amount']:.2f}")
            print(f"  Total Price: ${details_inside['total_price']:.2f}")
            print(f"  Delivery Time: {details_inside['delivery_time']}")
            print(f"  In Stock: {details_inside['breakdown'].get('in_stock', 'N/A')}")
            
            # Test 3: Product Details - Outside Beirut
            print("\n" + "=" * 70)
            print("3. Testing get_detailed_pricing (Outside Beirut)...")
            print("=" * 70)
            
            details_outside = adapter.get_detailed_pricing(first_product.url, location="outside beirut")
            
            print("\n✓ Details (Outside Beirut):")
            print(f"  Base Price: ${details_outside['item_price']:.2f}")
            print(f"  Shipping Fee: ${details_outside['shipping_fee']:.2f}")
            print(f"  Taxes: ${details_outside['tax_amount']:.2f}")
            print(f"  Total Price: ${details_outside['total_price']:.2f}")
            print(f"  Delivery Time: {details_outside['delivery_time']}")
            
            # Test 4: Verify Fixed Rules
            print("\n" + "=" * 70)
            print("4. Verifying OutGeeked Rules...")
            print("=" * 70)
            
            # Check shipping fee
            assert details_inside['shipping_fee'] == 3.0, "Shipping should always be $3"
            assert details_outside['shipping_fee'] == 3.0, "Shipping should always be $3"
            print("  ✓ Shipping fee: $3.00 (flat rate)")
            
            # Check taxes
            assert details_inside['tax_amount'] == 0.0, "Taxes should always be $0"
            assert details_outside['tax_amount'] == 0.0, "Taxes should always be $0"
            print("  ✓ Taxes: $0.00")
            
            # Check delivery times
            assert details_inside['delivery_time'] == "2-5 days", "Inside Beirut should be 2-5 days"
            assert details_outside['delivery_time'] == "5-7 days", "Outside Beirut should be 5-7 days"
            print("  ✓ Delivery inside Beirut: 2-5 days")
            print("  ✓ Delivery outside Beirut: 5-7 days")
            
            # Check total calculation
            expected_total_inside = details_inside['item_price'] + 3.0
            expected_total_outside = details_outside['item_price'] + 3.0
            assert abs(details_inside['total_price'] - expected_total_inside) < 0.01, "Total calculation wrong"
            assert abs(details_outside['total_price'] - expected_total_outside) < 0.01, "Total calculation wrong"
            print(f"  ✓ Total = Base + $3 shipping (${details_inside['item_price']:.2f} + $3.00 = ${details_inside['total_price']:.2f})")
            
            # Test 5: Different locations
            print("\n" + "=" * 70)
            print("5. Testing Different Location Variations...")
            print("=" * 70)
            
            test_locations = [
                ("Beirut", "2-5 days"),
                ("Inside Beirut", "2-5 days"),
                ("Tripoli", "5-7 days"),
                ("Sidon", "5-7 days"),
                ("outside beirut", "5-7 days"),
            ]
            
            for location, expected_delivery in test_locations:
                details = adapter.get_detailed_pricing(first_product.url, location=location)
                assert details['delivery_time'] == expected_delivery, f"Wrong delivery time for {location}"
                assert details['shipping_fee'] == 3.0, f"Shipping should be $3 for {location}"
                print(f"  ✓ {location}: $3 shipping, {expected_delivery}")
            
            print("\n" + "=" * 70)
            print("✅ ALL TESTS PASSED!")
            print("=" * 70)
            print("\nOutGeeked adapter is fully functional:")
            print("  ✓ Search returns products correctly")
            print("  ✓ Product details extracted successfully")
            print("  ✓ Fixed shipping: $3 (flat rate)")
            print("  ✓ Location-based delivery times working")
            print("  ✓ No taxes applied")
            print("=" * 70)
        else:
            print("\n✗ Failed to get product details")
    else:
        print("\n✗ No products found")


if __name__ == "__main__":
    try:
        test_outgeeked()
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
