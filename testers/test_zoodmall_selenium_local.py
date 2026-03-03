"""Quick test of ZoodMall Selenium adapter directly"""

import sys
sys.path.insert(0, '.')

from scraping.adapters.websites.zoodmall import ZoodMallAdapter

print("=" * 70)
print("TESTING ZOODMALL SELENIUM ADAPTER LOCALLY")
print("=" * 70)

try:
    print("\n1. Initializing adapter...")
    adapter = ZoodMallAdapter()
    print("   ✓ Adapter initialized")
    
    print("\n2. Searching for 'samsung a56'...")
    results = adapter.search("samsung a56", limit=5)
    
    print(f"\n3. Results: {len(results)} products found")
    
    if results:
        print("\n   Products:")
        for i, offer in enumerate(results[:5], 1):
            print(f"   {i}. {offer.title[:60]}")
            print(f"      Price: ${offer.item_price:.2f}")
            print(f"      Total: ${offer.total_price:.2f}")
            print()
    else:
        print("   ⚠️  No products found")
    
    print("\n✅ Test completed successfully")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
