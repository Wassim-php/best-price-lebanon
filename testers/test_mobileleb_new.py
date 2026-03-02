#!/usr/bin/env python3
"""Test Mobileleb adapter with simplified workflow."""

import sys
sys.path.insert(0, '/app')

from scraping.adapters.websites.mobileleb import MobileLebAdapter

def test_mobileleb():
    adapter = MobileLebAdapter()
    
    # Test 1: Search
    print("=" * 80)
    print("TEST 1: SEARCH")
    print("=" * 80)
    results = adapter.search("laptop", limit=3)
    
    if not results:
        print("✗ No search results returned")
        return
    
    print(f"✓ Found {len(results)} products")
    for i, offer in enumerate(results[:2]):
        print(f"\n  [{i+1}] {offer.title[:60]}")
        print(f"      URL: {offer.url}")
        print(f"      Price: ${offer.item_price}")
    
    # Test 2: Get detailed pricing for first product
    print("\n" + "=" * 80)
    print("TEST 2: GET DETAILED PRICING")
    print("=" * 80)
    
    first_product_url = results[0].url
    print(f"Testing with: {first_product_url}")
    
    pricing = adapter.get_detailed_pricing(first_product_url, location="outside beirut")
    
    print(f"\n✓ Pricing retrieved:")
    print(f"  Item Price: ${pricing.get('item_price', 'N/A')}")
    print(f"  Shipping Fee: ${pricing.get('shipping_fee', 'N/A')}")
    print(f"  Tax Amount: ${pricing.get('tax_amount', 'N/A')}")
    print(f"  Total Price: ${pricing.get('total_price', 'N/A')}")
    print(f"  Currency: {pricing.get('currency', 'N/A')}")
    print(f"  Delivery Time: {pricing.get('delivery_time', 'N/A')}")
    
    if pricing.get('breakdown'):
        print(f"\n  Breakdown:")
        for key, value in pricing['breakdown'].items():
            if value is not None:
                print(f"    {key}: {value}")
    
    print("\n" + "=" * 80)
    print("TESTS COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    test_mobileleb()
