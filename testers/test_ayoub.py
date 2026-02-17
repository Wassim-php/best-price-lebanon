"""
Test the Ayoub Computers adapter
Run from testers directory: python test_ayoub.py
"""
import sys
import os
# Add parent directory to path so we can import from scraping package
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraping.adapters.ayoub import AyoubComputersAdapter

# Initialize adapter
adapter = AyoubComputersAdapter()

# Test search functionality
test_queries = [
    "laptop",
    "iPhone",
    "headphones"
]

print("=" * 70)
print("TESTING AYOUB COMPUTERS ADAPTER")
print("=" * 70)

for query in test_queries:
    print(f"\n{'='*70}")
    print(f"Searching for: '{query}'")
    print(f"{'='*70}")
    
    try:
        # Search with limit of 5 results
        offers = adapter.search(query, limit=5)
        
        print(f"\nFound {len(offers)} offers:\n")
        
        for i, offer in enumerate(offers, 1):
            print(f"{i}. {offer.title}")
            print(f"   Price: {offer.item_price} {offer.currency}")
            print(f"   URL: {offer.url}")
            print(f"   In Stock: {'Yes' if offer.in_stock else 'No'}")
            if offer.image_url:
                print(f"   Image: {offer.image_url[:60]}...")
            print()
        
        if not offers:
            print("   No offers found for this query.\n")
            
    except Exception as e:
        print(f"\n❌ ERROR: {type(e).__name__}: {str(e)}\n")

print("=" * 70)
print("TEST COMPLETED")
print("=" * 70)
