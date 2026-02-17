"""
Test the Ayoub Computers get_detailed_pricing method
Run from testers directory: python test_ayoub_pricing.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraping.adapters.ayoub import AyoubComputersAdapter

# Initialize adapter
adapter = AyoubComputersAdapter()

# Test with a real product URL - using the headphones we found in the search test
product_url = "https://ayoubcomputers.com/hoco-wireless-and-wired-headphones-w33/"

print("=" * 70)
print("TESTING AYOUB COMPUTERS - DETAILED PRICING")
print("=" * 70)
print(f"\nProduct URL: {product_url}")
print("\nFetching pricing details...\n")

result = adapter.get_detailed_pricing(product_url)

print("=" * 70)
print("RESULTS:")
print("=" * 70)
print(f"Item Price: ${result['item_price']:.2f}")
print(f"Shipping Fee: ${result['shipping_fee']:.2f}" if result['shipping_fee'] is not None else "Shipping Fee: FREE")
print(f"Tax Amount: ${result['tax_amount']:.2f}" if result['tax_amount'] is not None else "Tax Amount: N/A")
print(f"Total Price: ${result['total_price']:.2f}")
print(f"Currency: {result['currency']}")
print(f"Delivery Time: {result['delivery_time']}" if result.get('delivery_time') else "Delivery Time: Not specified")

if result.get('breakdown'):
    print(f"\nBreakdown:")
    for key, value in result['breakdown'].items():
        print(f"  {key}: {value}")

print("=" * 70)

# Verify calculations
if result['item_price'] > 0:
    expected_tax = round(result['item_price'] * 0.11, 2)
    expected_total = round(result['item_price'] + expected_tax, 2)
    
    print("\nVerification:")
    print(f"  Tax calculation (11%): ${expected_tax:.2f} {'✓' if expected_tax == result['tax_amount'] else '✗'}")
    print(f"  Total calculation: ${expected_total:.2f} {'✓' if expected_total == result['total_price'] else '✗'}")
    print(f"  Free shipping: {'✓' if result['shipping_fee'] == 0.0 else '✗'}")
    print("=" * 70)
