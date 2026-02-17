"""
Test detailed pricing for Sennheiser product
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraping.adapters.souq961 import Souq961Adapter

# Test with Sennheiser product
adapter = Souq961Adapter()
product_url = "https://961souq.com/products/sennheiser-accentum-open-true-wireless-earbuds?Title=Default+Title"

print("Testing get_detailed_pricing for Sennhe iser Accentum...")
print(f"URL: {product_url}")
print("\nFetching pricing details (this may take 20-30 seconds)...\n")

result = adapter.get_detailed_pricing(product_url)

print("=" * 60)
print("RESULTS:")
print("=" * 60)
print(f"Item Price: ${result['item_price']}")
print(f"Shipping Fee: ${result['shipping_fee']}" if result['shipping_fee'] is not None else "Shipping Fee: TBD at checkout")
print(f"Tax Amount: ${result['tax_amount']}" if result['tax_amount'] is not None else "Tax Amount: $0.00")
print(f"Total Price: ${result['total_price']}")
print(f"Currency: {result['currency']}")
print(f"Delivery Time: {result['delivery_time']}" if result.get('delivery_time') else "Delivery Time: Not specified")
print(f"\nBreakdown:")
for key, value in result['breakdown'].items():
    print(f"  {key}: {value}")
print("=" * 60)
