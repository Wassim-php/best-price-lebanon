"""Quick test of ZoodMall in Docker"""
import sys
from scraping.adapters.websites.zoodmall import ZoodMallAdapter

print("Initializing ZoodMall adapter...")
adapter = ZoodMallAdapter()

print("Searching for 'iphone'...")
try:
    results = adapter.search("iphone", limit=3)
    print(f"Found {len(results)} products")
    for i, product in enumerate(results[:3], 1):
        print(f"{i}. {product.title[:50]} - ${product.item_price}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
