"""Debug ZoodMall with detailed logging"""
import sys
import logging

# Set up detailed logging
logging.basicConfig(level=logging.DEBUG)

from scraping.adapters.websites.zoodmall import ZoodMallAdapter

print("=" * 70)
print("DEBUGGING ZOODMALL ADAPTER")
print("=" * 70)

print("\n1. Initializing adapter...")
adapter = ZoodMallAdapter()
print("   ✓ Adapter initialized")

print("\n2. Searching for 'iphone' (this may take 30-60 seconds)...")
try:
    results = adapter.search("iphone", limit=5)
    print(f"\n3. Results: {len(results)} products found")
    
    if results:
        for i, product in enumerate(results[:5], 1):
            print(f"   {i}. {product.title[:60]}")
            print(f"      ${product.item_price}")
    else:
        print("   ⚠️  No products returned")
        print("   This could mean:")
        print("   - Cloudflare is blocking the request")
        print("   - The page structure has changed")
        print("   - Selenium failed to load the page")
        
except Exception as e:
    print(f"\n❌ Error during search: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
