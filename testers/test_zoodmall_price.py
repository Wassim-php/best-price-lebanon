"""Test ZoodMall price extraction for specific product"""
import sys
import os
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'best_price_lebanon.settings')

import django
django.setup()

from scraping.adapters.websites.zoodmall import ZoodMallAdapter

# Test the specific product URL
product_url = 'https://www.zoodmall.com.lb/en/product/35484455/samsung-galaxy-a56-ctc-256g8ram-with-one-year-warranty-gift/'

adapter = ZoodMallAdapter()
result = adapter.get_detailed_pricing(product_url, 'outside beirut')

print("\n" + "="*70)
print("ZOODMALL PRICE EXTRACTION TEST")
print("="*70)
print(f"Product URL: {product_url}")
print(f"\nBase Price: ${result['base_price']}")
print(f"Shipping Fee: ${result['shipping_fee']}")
print(f"Tax: ${result['tax']}")
print(f"Total Price: ${result['total_price']}")
print(f"Delivery Time: {result['delivery_time']}")
print(f"Title: {result['title']}")
print("="*70)
