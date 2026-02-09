"""
Test the updated get_detailed_pricing method
Run from testers directory: python test_detailed_pricing.py
"""
import sys
import os
# Add parent directory to path so we can import from scraping package
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraping.adapters.souq961 import Souq961Adapter

# Test with iPhone 15 product
adapter = Souq961Adapter()
product_url = "https://961souq.com/products/apple-iphone-15"

print("Testing get_detailed_pricing for iPhone 15...")
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
print(f"\nBreakdown:")
for key, value in result['breakdown'].items():
    print(f"  {key}: {value}")
print("=" * 60)
