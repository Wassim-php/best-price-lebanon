"""Test script for HiCart adapter"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraping.adapters.websites.hicart import HiCartAdapter

def test_hicart():
    print("=" * 70)
    print("TESTING HICART ADAPTER")
    print("=" * 70)
    
    adapter = HiCartAdapter()
    
    # Test search
    print("\n1. Testing search for 'iphone'...")
    results = adapter.search("iphone")
    
    print(f"\nFound {len(results)} products")
    
    if results:
        print("\nFirst 3 results:")
        for i, product in enumerate(results[:3], 1):
            print(f"\n{i}. {product.title}")
            print(f"   Price: ${product.item_price:.2f}")
            print(f"   URL: {product.url[:80]}...")
            print(f"   In Stock: {product.in_stock}")
        
        # Test product details
        print("\n" + "=" * 70)
        print("2. Testing get_product_details...")
        print("=" * 70)
        
        first_product = results[0]
        print(f"\nFetching details for: {first_product.title}")
        
        details = adapter.get_product_details(first_product.url, location="Beirut")
        
        if details:
            print("\n✓ Product Details:")
            print(f"  Name: {details['name']}")
            print(f"  Base Price: ${details['price']:.2f}")
            print(f"  Shipping Fee: ${details['shipping_fee']:.2f}")
            print(f"  Taxes: ${details['taxes']:.2f}")
            print(f"  Total Price: ${details['total_price']:.2f}")
            print(f"  Delivery Time: {details['delivery_time']}")
            print(f"  In Stock: {details['in_stock']}")
            print(f"  Currency: {details['currency']}")
            
            # Verify fixed rules
            print("\n✓ Verifying Fixed Rules:")
            assert details['shipping_fee'] == 4.0, "Shipping should be $4"
            assert details['taxes'] == 0.0, "Taxes should be $0"
            assert details['delivery_time'] == "5 days", "Delivery should be 5 days"
            print("  ✓ Shipping fee is $4")
            print("  ✓ Taxes are $0")
            print("  ✓ Delivery time is 5 days")
            
            # Verify total calculation
            expected_total = details['price'] + 4.0
            assert abs(details['total_price'] - expected_total) < 0.01, "Total price calculation"
            print(f"  ✓ Total price calculated correctly (${details['price']:.2f} + $4.00 = ${details['total_price']:.2f})")
            
            print("\n✅ ALL TESTS PASSED!")
        else:
            print("\n✗ Failed to get product details")
    else:
        print("\n✗ No products found")
    
    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    test_hicart()
