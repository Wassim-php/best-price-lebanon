"""List all registered adapters"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraping.registry import ADAPTERS

print("=" * 70)
print("REGISTERED ADAPTERS")
print("=" * 70)

for key, adapter in ADAPTERS.items():
    source_name = getattr(adapter, 'source_name', adapter.__class__.__name__)
    has_search = hasattr(adapter, 'search')
    has_details = hasattr(adapter, 'get_detailed_pricing')
    
    print(f"\n{key}")
    print(f"  Name: {source_name}")
    print(f"  Class: {adapter.__class__.__name__}")
    print(f"  Search: {'✓' if has_search else '✗'}")
    print(f"  Details: {'✓' if has_details else '✗'}")

print("\n" + "=" * 70)
print(f"Total: {len(ADAPTERS)} adapters")
print("=" * 70)
