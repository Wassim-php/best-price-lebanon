"""
Quick unit test of the search_and_get_details logic
Run from testers directory: python test_endpoint_logic.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'best_price_lebanon.settings')
import django
django.setup()

from scraping.registry import ADAPTERS
from scraping.services import run_search

def test_endpoint_logic(source_key, query, location="outside beirut"):
    """Simulate the endpoint logic"""
    
    print("=" * 70)
    print(f"Testing: {source_key.upper()} - '{query}'")
    print("=" * 70)
    
    if source_key not in ADAPTERS:
        print(f"❌ ERROR: Unknown source '{source_key}'")
        return
    
    try:
        # Step 1: Search with AI filter and cheapest only
        print("\n1. Running AI-filtered search (cheapest only)...")
        job = run_search(
            query=query, 
            source_key=source_key, 
            limit=10, 
            use_ai_filter=True,
            cheapest_only=True
        )
        
        # Step 2: Get the offers from the job
        offers = job.offers.all()
        
        if not offers:
            print(f"❌ No products found matching '{query}'")
            return
        
        print(f"✓ Found {offers.count()} product(s)")
        
        # Should have exactly 1 offer due to cheapest_only=True
        offer = offers[0]
        
        print(f"\n2. Cheapest product:")
        print(f"   Title: {offer.title}")
        print(f"   URL: {offer.url}")
        print(f"   Price: ${offer.item_price} {offer.currency}")
        print(f"   In Stock: {offer.in_stock}")
        
        # Step 3: Get detailed pricing
        adapter = ADAPTERS[source_key]
        
        if not hasattr(adapter, 'get_detailed_pricing'):
            print(f"\n⚠️  Source {source_key} does not support detailed pricing")
            return
        
        print(f"\n3. Fetching detailed pricing...")
        pricing_details = adapter.get_detailed_pricing(offer.url, location=location)
        
        # Step 4: Display final results
        print(f"\n" + "=" * 70)
        print("FINAL RESULT")
        print("=" * 70)
        
        print(f"\n📦 PRODUCT:")
        print(f"   Title: {offer.title}")
        print(f"   URL: {offer.url}")
        print(f"   In Stock: {'✓' if offer.in_stock else '✗'}")
        
        print(f"\n💰 PRICING:")
        print(f"   Item Price: ${pricing_details['item_price']:.2f}")
        
        if pricing_details.get('shipping_fee') is not None:
            if pricing_details['shipping_fee'] == 0:
                print(f"   Shipping: FREE")
            else:
                print(f"   Shipping: ${pricing_details['shipping_fee']:.2f}")
        
        if pricing_details.get('tax_amount') is not None:
            print(f"   Tax: ${pricing_details['tax_amount']:.2f}")
        
        print(f"   💵 TOTAL: ${pricing_details['total_price']:.2f}")
        print(f"   Currency: {pricing_details.get('currency', 'USD')}")
        
        if pricing_details.get('delivery_time'):
            print(f"   🚚 Delivery: {pricing_details['delivery_time']}")
        
        if pricing_details.get('breakdown'):
            print(f"\n   Breakdown:")
            for key, value in pricing_details['breakdown'].items():
                print(f"     • {key}: {value}")
        
        print(f"\n✓ Success!")
        print("=" * 70)
        
    except Exception as e:
        import traceback
        print(f"\n❌ ERROR: {type(e).__name__}: {str(e)}")
        print("\nTraceback:")
        traceback.print_exc()
        print("=" * 70)


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("TESTING SEARCH-WITH-DETAILS ENDPOINT LOGIC")
    print("=" * 70)
    
    # Test with Ayoub Computers
    test_endpoint_logic("ayoubcomputers", "wireless headphones")
    
    print("\n\n")
    
    # Test with 961souq if desired
    # test_endpoint_logic("961souq", "iPhone 15")
    
    print("\n" + "=" * 70)
    print("TEST COMPLETED")
    print("=" * 70)
