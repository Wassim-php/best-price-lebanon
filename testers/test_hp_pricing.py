"""
Test script to check detailed pricing for HP Victus laptop
Run from testers directory: python test_hp_pricing.py
"""
import sys
import os
# Add parent directory to path so we can import from scraping package
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraping.adapters.websites.souq961 import Souq961Adapter

def test_hp_product():
    adapter = Souq961Adapter()
    product_url = "https://961souq.com/products/hp-victus-15-fa2093"
    
    print("Testing get_detailed_pricing for HP Victus laptop...")
    print(f"URL: {product_url}\n")
    print("Fetching pricing details (this may take 20-30 seconds)...\n")
    
    result = adapter.get_detailed_pricing(product_url)
    
    print("=" * 60)
    print("RESULTS:")
    print("=" * 60)
    print(f"Item Price: ${result['item_price']}")
    print(f"Shipping Fee: ${result['shipping_fee']}")
    print(f"Tax Amount: ${result['tax_amount']}")
    print(f"Total Price: ${result['total_price']}")
    print(f"Currency: {result['currency']}")
    print(f"\nBreakdown:")
    for key, value in result['breakdown'].items():
        print(f"  {key}: {value}")
    print("=" * 60)

if __name__ == "__main__":
    test_hp_product()
