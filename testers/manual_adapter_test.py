#!/usr/bin/env python
"""
Simple test to verify the Mobileleb adapter works end-to-end.
Run this to test the full workflow.
"""
import os
import sys
import django

sys.path.insert(0, "/app")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "best_price_lebanon.settings")
django.setup()

from scraping.registry import ADAPTERS

print("=" * 80)
print("MOBILELEB ADAPTER - FULL WORKFLOW TEST")
print("=" * 80)

adapter = ADAPTERS["mobileleb"]

# Test 1: Search
print("\n[TEST 1] SEARCH")
print("-" * 80)
query = "iphone 17"
print(f"Searching for: '{query}'")

results = adapter.search(query, limit=5)
print(f"\nFound {len(results)} products:")

if results:
    for i, r in enumerate(results[:3], 1):
        print(f"\n{i}. {r.title}")
        print(f"   Price: ${r.item_price}")
        print(f"   URL: {r.url}")
        print(f"   Image: {'✓' if r.image_url else '✗ (missing)'}")
    
    # Test 2: Get detailed pricing for first product
    print("\n[TEST 2] GET DETAILED PRICING")
    print("-" * 80)
    
    product = results[0]
    print(f"Getting pricing for: {product.title}")
    print(f"URL: {product.url}")
    print("\nFetching detailed pricing (this may take 30-60 seconds)...")
    
    pricing = adapter.get_detailed_pricing(product.url, location="outside beirut")
    
    print(f"\nDetailed pricing results:")
    print(f"  Item Price: ${pricing.get('item_price')}")
    print(f"  Shipping Fee: ${pricing.get('shipping_fee') if pricing.get('shipping_fee') else 'Not calculated'}")
    print(f"  Tax: ${pricing.get('tax_amount') if pricing.get('tax_amount') else 'N/A'}")
    print(f"  Total: ${pricing.get('total_price')}")
    print(f"  Currency: {pricing.get('currency')}")
    print(f"  Delivery Time: {pricing.get('delivery_time')}")
    
    if pricing.get('breakdown'):
        print(f"\n  Breakdown:")
        for key, val in pricing['breakdown'].items():
            if key != 'note':
                print(f"    {key}: {val}")
        if pricing['breakdown'].get('note'):
            print(f"\n  Note: {pricing['breakdown']['note']}")

else:
    print("✗ No products found!")

print("\n" + "=" * 80)
print("TEST COMPLETE")
print("=" * 80)
