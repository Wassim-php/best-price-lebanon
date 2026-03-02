"""Test ZoodMall with full product details"""

import requests
import json

BASE_URL = "http://localhost:8000/api"

print("=" * 70)
print("ZOODMALL - SAMSUNG A56 SEARCH WITH FULL DETAILS")
print("=" * 70)

# Test search endpoint
print("\n1. Search Results:")
print("-" * 70)
response = requests.post(
    f"{BASE_URL}/search/zoodmall",
    json={"query": "samsung a56"},
    timeout=180
)

if response.status_code == 200:
    data = response.json()
    offers = data.get('offers', [])
    print(f"Found {len(offers)} products:\n")
    
    for i, offer in enumerate(offers, 1):
        print(f"{i}. {offer['title']}")
        print(f"   Item Price: ${float(offer['item_price']):.2f}")
        print(f"   Shipping: ${float(offer.get('shipping_fee', 0)):.2f}")
        print(f"   Total: ${float(offer.get('total_price', offer['item_price'])):.2f}")
        print(f"   URL: {offer['url'][:60]}...")
        print()

# Test search-with-details endpoint
print("2. Best Deal with Full Pricing:")
print("-" * 70)
response = requests.post(
    f"{BASE_URL}/search-with-details/zoodmall",
    json={"query": "samsung a56", "location": "outside beirut"},
    timeout=180
)

if response.status_code == 200:
    data = response.json()
    product = data.get('product', {})
    pricing = data.get('pricing', {})
    
    print(f"Product: {product.get('title', 'N/A')}")
    print(f"\nPricing Breakdown:")
    print(f"  Base Price: ${pricing.get('base_price', 0):.2f}")
    print(f"  Shipping: ${pricing.get('shipping_fee', 0):.2f}")
    print(f"  Tax: ${pricing.get('tax', 0):.2f}")
    print(f"  ─────────────────")
    print(f"  Total: ${pricing.get('total_price', 0):.2f}")
    print(f"\nDelivery: {pricing.get('delivery_time', 'N/A')}")
    print(f"Location: Akkar, North Lebanon (Door Delivery)")
    print(f"Currency: {pricing.get('currency', 'USD')}")
else:
    print(f"Error: {response.status_code} - {response.text[:100]}")

print("\n" + "=" * 70)
print("NOTE: Based on actual ZoodMall shipping to:")
print("Meniara, Akkar, North Lebanon")
print("Delivery: 2-7 days | Shipping: $4.75 USD")
print("=" * 70)
