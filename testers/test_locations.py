import sys
sys.path.insert(0, "..")

from scraping.adapters.souq961 import Souq961Adapter

# Test with both locations
adapter = Souq961Adapter()

# Use different products to avoid cart conflicts
sennheiser_url = "https://961souq.com/products/sennheiser-accentum-open-true-wireless-earbuds?Title=Default+Title"
iphone_url = "https://961souq.com/products/apple-iphone-15"

print("=" * 70)
print("Testing with DEFAULT location (should be 'outside beirut')")
print("Product: Sennheiser Accentum")
print("=" * 70)
result_default = adapter.get_detailed_pricing(sennheiser_url)
print(f"Item: ${result_default['item_price']}")
print(f"Shipping: ${result_default['shipping_fee']}")
print(f"Tax: ${result_default['tax_amount']}")
print(f"Total: ${result_default['total_price']}")
print(f"Delivery Time: {result_default['delivery_time']}")
print(f"Location: {result_default['breakdown']['delivery_location']}")
print()

print("=" * 70)
print("Testing with 'inside beirut' location")
print("Product: iPhone 15")
print("=" * 70)
result_inside = adapter.get_detailed_pricing(iphone_url, location="inside beirut")
print(f"Item: ${result_inside['item_price']}")
print(f"Shipping: ${result_inside['shipping_fee']}")
print(f"Tax: ${result_inside['tax_amount']}")
print(f"Total: ${result_inside['total_price']}")
print(f"Delivery Time: {result_inside['delivery_time']}")
print(f"Location: {result_inside['breakdown']['delivery_location']}")
print()

print("=" * 70)
print("SUMMARY")
print("=" * 70)
print(f"Default location: {result_default['breakdown']['delivery_location']}")
print(f"Default delivery time: {result_default['delivery_time']}")
print(f"Inside Beirut delivery time: {result_inside['delivery_time']}")
print("=" * 70)
