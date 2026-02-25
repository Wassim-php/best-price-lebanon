import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraping.adapters.websites.mobileleb import MobileLebAdapter
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus

def test_mobileleb_pricing():
    """Test the Mobileleb pricing extraction with cart-based shipping calculation."""
    
    print("=" * 80)
    print("MOBILELEB PRICING TEST")
    print("=" * 80)
    
    adapter = MobileLebAdapter()
    
    # --- 1. Search for products ---
    print("\n1. Searching for products on Mobileleb...")
    try:
        offers = adapter.search("laptop", limit=1)
        
        if not offers:
            print("✗ No products found")
            return
        
        product = offers[0]
        print(f"✓ Found product: {product.title}")
        print(f"  URL: {product.url}")
        print(f"  Base price from search: ${product.item_price}")
    except Exception as e:
        print(f"✗ Search error: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # --- 2. Get detailed pricing ---
    print("\n2. Testing get_detailed_pricing (outside beirut)...")
    try:
        pricing = adapter.get_detailed_pricing(product.url, location="outside beirut")
        
        print(f"\n✓ Pricing extraction successful!")
        print(f"  Item Price: ${pricing.get('item_price', 0)}")
        print(f"  Shipping Fee: ${pricing.get('shipping_fee') if pricing.get('shipping_fee') else 'N/A'}")
        print(f"  Tax Amount: ${pricing.get('tax_amount') if pricing.get('tax_amount') else 'N/A'}")
        print(f"  Total Price: ${pricing.get('total_price', 0)}")
        print(f"  Delivery Time: {pricing.get('delivery_time', 'N/A')}")
        print(f"  Delivery Location: {pricing.get('breakdown', {}).get('delivery_location', 'N/A')}")
        
        if pricing.get('breakdown', {}).get('error'):
            print(f"  ⚠ Error: {pricing['breakdown']['error']}")
        
        # Test with inside beirut
        print("\n3. Testing get_detailed_pricing (inside beirut)...")
        pricing_inside = adapter.get_detailed_pricing(product.url, location="inside beirut")
        
        print(f"\n✓ Inside Beirut pricing:")
        print(f"  Item Price: ${pricing_inside.get('item_price', 0)}")
        print(f"  Shipping Fee: ${pricing_inside.get('shipping_fee') if pricing_inside.get('shipping_fee') else 'N/A'}")
        print(f"  Tax Amount: ${pricing_inside.get('tax_amount') if pricing_inside.get('tax_amount') else 'N/A'}")
        print(f"  Total Price: ${pricing_inside.get('total_price', 0)}")
        print(f"  Delivery Time: {pricing_inside.get('delivery_time', 'N/A')}")
        print(f"  Delivery Location: {pricing_inside.get('breakdown', {}).get('delivery_location', 'N/A')}")
        
        if pricing_inside.get('breakdown', {}).get('error'):
            print(f"  ⚠ Error: {pricing_inside['breakdown']['error']}")
        
        # --- 4. Validation ---
        print("\n4. Validation Results:")
        errors = []
        
        if pricing.get('item_price', 0) <= 0:
            errors.append("Item price not extracted properly")
        
        if pricing.get('currency') != 'USD':
            errors.append(f"Currency incorrect: {pricing.get('currency')}")
        
        if pricing.get('delivery_time') != "1-2 days":
            errors.append(f"Delivery time incorrect: {pricing.get('delivery_time')}")
        
        if not pricing.get('breakdown'):
            errors.append("Breakdown not populated")
        
        if errors:
            print("✗ Validation errors found:")
            for error in errors:
                print(f"  - {error}")
        else:
            print("✓ All validations passed!")
        
        # Compare inside vs outside
        if pricing.get('shipping_fee') and pricing_inside.get('shipping_fee'):
            if pricing.get('shipping_fee') != pricing_inside.get('shipping_fee'):
                print(f"✓ Shipping fees differ by location: Outside=${pricing.get('shipping_fee')}, Inside=${pricing_inside.get('shipping_fee')}")
            else:
                print(f"⚠ Shipping fees are the same: ${pricing.get('shipping_fee')}")
        
    except Exception as e:
        print(f"✗ Pricing extraction error: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    test_mobileleb_pricing()
