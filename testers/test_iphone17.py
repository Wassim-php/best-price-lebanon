#!/usr/bin/env python
"""
Test what raw search returns for "iphone 17" vs what AI filter returns.
"""
import os
import sys
import django

sys.path.insert(0, "/app")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "best_price_lebanon.settings")
django.setup()

from scraping.registry import ADAPTERS
from scraping.ai_filter import filter_offers_with_ai

adapter = ADAPTERS["mobileleb"]
query = "iphone 17"

print("=" * 80)
print(f"TESTING: '{query}'")
print("=" * 80)

# Raw search
raw = adapter.search(query=query, limit=20)
print(f"\nRAW SEARCH RESULTS ({len(raw)} products):")
print("-" * 80)
for i, offer in enumerate(raw, 1):
    print(f"{i}. {offer.title}")

# Apply AI filter
print(f"\nAPPLYING AI FILTER...")
print("-" * 80)
try:
    filtered = filter_offers_with_ai(query, raw)
    print(f"\nFILTERED RESULTS ({len(filtered)} products):")
    for i, offer in enumerate(filtered, 1):
        print(f"{i}. {offer.title}")
    
    if len(filtered) == 0 and len(raw) > 0:
        print("\n❌ PROBLEM: AI filtered out ALL results!")
        print(f"\nThe raw search had these product types:")
        types = {}
        for offer in raw:
            if "Pro Max" in offer.title:
                key = "iPhone Pro Max"
            elif "Pro" in offer.title:
                key = "iPhone Pro"
            elif "Plus" in offer.title:
                key = "iPhone Plus"
            elif "iPhone" in offer.title:
                key = "iPhone Standard"
            else:
                key = "Other"
            types[key] = types.get(key, 0) + 1
        
        for product_type, count in sorted(types.items()):
            print(f"  - {product_type}: {count}")
            
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
