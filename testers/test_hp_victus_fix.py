"""Test OutGeeked adapter with HP Victus search"""

import sys
sys.path.insert(0, 'c:\\Users\\naous\\senior-project\\best-price-lebanon')

from scraping.adapters.websites.outgeeked import OutGeekedAdapter

print("=" * 70)
print("TESTING OUTGEEKED ADAPTER - HP VICTUS SEARCH")
print("=" * 70)

adapter = OutGeekedAdapter()

# Test search
print("\n1. Searching for 'hp victus'...")
print("=" * 70)

products = adapter.search("hp victus", limit=10)

print(f"\n✓ Found {len(products)} products")

if products:
    print("\nProducts found:")
    for i, product in enumerate(products, 1):
        print(f"\n  {i}. {product.title}")
        print(f"     Price: ${product.item_price:.2f}")
        print(f"     URL: {product.url}")
        print(f"     In Stock: {product.in_stock}")
    
    # Test detailed pricing for first product
    print("\n\n2. Testing Detailed Pricing...")
    print("=" * 70)
    
    first_product = products[0]
    print(f"\nProduct: {first_product.title}")
    
    # Inside Beirut
    print("\n  Inside Beirut:")
    details_inside = adapter.get_detailed_pricing(first_product.url, "inside beirut")
    print(f"    Base Price: ${details_inside['item_price']:.2f}")
    print(f"    Shipping: ${details_inside['shipping_fee']:.2f}")
    print(f"    Taxes: ${details_inside.get('tax_amount', 0):.2f}")
    print(f"    Total: ${details_inside['total_price']:.2f}")
    print(f"    Delivery: {details_inside['delivery_time']}")
    
    # Outside Beirut
    print("\n  Outside Beirut:")
    details_outside = adapter.get_detailed_pricing(first_product.url, "outside beirut")
    print(f"    Base Price: ${details_outside['item_price']:.2f}")
    print(f"    Shipping: ${details_outside['shipping_fee']:.2f}")
    print(f"    Taxes: ${details_outside.get('tax_amount', 0):.2f}")
    print(f"    Total: ${details_outside['total_price']:.2f}")
    print(f"    Delivery: {details_outside['delivery_time']}")
    
    print("\n" + "=" * 70)
    print("✅ TEST PASSED - HP Victus products found!")
    print("=" * 70)
else:
    print("\n" + "=" * 70)
    print("❌ TEST FAILED - No products found")
    print("=" * 70)
    sys.exit(1)
