"""Test the 375 product URL specifically"""
import sys, os
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'best_price_lebanon.settings')
import django
django.setup()

from scraping.adapters.websites.zoodmall import ZoodMallAdapter

# This is the 375.00 product from search results
url_375 = 'https://www.zoodmall.com.lb/en/product/35484455/samsung-galaxy-a56-ctc-256g8ram-with-one-year-warranty-gift/'

print("\n" + "="*70)
print("TESTING $375 PRODUCT URL")
print("="*70)
print(f"URL: {url_375}")
print()

adapter = ZoodMallAdapter()
result = adapter.get_detailed_pricing(url_375, 'outside beirut')

print(f"Expected: $375.00 (user says detail page shows 425 crossed, 375 actual)")
print(f"Actual: ${result['base_price']}")
if result['base_price'] == 375.0:
    print(f"Status: ✓ CORRECT")
else:
    print(f"Status: ✗ WRONG (should be 375, got {result['base_price']})")
print("="*70 + "\n")
