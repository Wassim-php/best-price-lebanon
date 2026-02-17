"""
Test the get_detailed_pricing method for AbedTahan
Run from testers directory: python test_abdeltahan_pricing.py
"""
import sys
import os
# Add parent directory to path so we can import from scraping package
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraping.adapters.websites.abdeltahan import AbedTahanAdapter

# Test with a real product from Abed Tahan
# Try searching first to get a real product URL
adapter = AbedTahanAdapter()

# First, search for a product to get a real URL
print("Searching for laptops on Abed Tahan...")
results = adapter.search("laptop", limit=1)

if results:
    product_url = results[0].url
    print(f"Found product: {results[0].title}")
    print(f"URL: {product_url}")
    print(f"Base price from search: ${results[0].item_price}\n")
else:
    # Fallback to a manually found product URL
    product_url = "https://abedtahan.com/products/hp-pavilion-15-eg0013dx"
    print(f"Using fallback URL: {product_url}\n")

print("Testing get_detailed_pricing...")
print("(This may take 20-30 seconds as it opens a browser)\n")

result = adapter.get_detailed_pricing(product_url)

print("=" * 60)
print("RESULTS:")
print("=" * 60)
print(f"Item Price: ${result['item_price']}")
print(f"Shipping Fee: ${result['shipping_fee']}" if result['shipping_fee'] is not None else "Shipping Fee: Not calculated")
print(f"Tax Amount: ${result['tax_amount']}" if result['tax_amount'] is not None else "Tax Amount: Not calculated")
print(f"Total Price: ${result['total_price']}")
print(f"Currency: {result['currency']}")
print(f"\nBreakdown:")
for key, value in result['breakdown'].items():
    print(f"  {key}: {value}")
print("=" * 60)

# Check for errors
if "error" in result['breakdown']:
    print("\n⚠️  ERROR DETECTED - Method may not be working properly!")
    print(f"Error details: {result['breakdown']['error']}")
else:
    print("\n✓ No errors detected in execution")
    if result['total_price'] > result['item_price']:
        print("✓ Total price includes fees/taxes/shipping")
    else:
        print("⚠️  Total price equals item price - no additional fees were calculated")
