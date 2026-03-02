"""Test HiCart adapter through the API endpoint"""

import requests
import json

BASE_URL = "http://localhost:8000/api"

def test_hicart_api():
    print("=" * 70)
    print("TESTING HICART THROUGH API")
    print("=" * 70)
    
    # Test search endpoint
    print("\n1. Testing /api/search/hicart endpoint...")
    
    payload = {
        "query": "iphone"
    }
    
    print(f"Request: POST {BASE_URL}/search/hicart")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    response = requests.post(f"{BASE_URL}/search/hicart", json=payload)
    
    print(f"\nResponse Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Success!")
        print(f"\nFull response keys: {list(data.keys())}")
        print(f"Offers: {len(data.get('offers', []))}")
        
        if data.get('offers'):
            print("\nFirst 3 products:")
            for i, product in enumerate(data['offers'][:3], 1):
                print(f"\n{i}. {product['title']}")
                print(f"   Price: ${float(product['item_price']):.2f}")
                print(f"   Source: HiCart")
                print(f"   URL: {product['url'][:80]}...")
        
        # Test get_product_details endpoint
        if data.get('results'):
            print("\n" + "=" * 70)
            print("2. Testing /api/product-details/hicart endpoint...")
            print("=" * 70)
            
            first_product = data['results'][0]
            
            detail_payload = {
                "product_url": first_product['url'],
                "location": "Beirut"
            }
            
            print(f"\nRequest: POST {BASE_URL}/product-details/hicart")
            print(f"Product: {first_product['title'][:50]}...")
            
            response2 = requests.post(f"{BASE_URL}/product-details/hicart", json=detail_payload)
            
            print(f"\nResponse Status: {response2.status_code}")
            
            if response2.status_code == 200:
                details = response2.json()
                print(f"✓ Success!")
                print(f"\nProduct Details:")
                print(f"  Base Price: ${details['price']:.2f}")
                print(f"  Shipping: ${details['shipping_fee']:.2f}")
                print(f"  Taxes: ${details['taxes']:.2f}")
                print(f"  Total: ${details['total_price']:.2f}")
                print(f"  Delivery: {details['delivery_time']}")
                print(f"  In Stock: {details['in_stock']}")
                
                # Verify fixed rules
                print("\n✓ Verifying Rules:")
                assert details['shipping_fee'] == 4.0, "Shipping should be $4"
                assert details['taxes'] == 0.0, "Taxes should be $0"
                assert details['delivery_time'] == "5 days", "Delivery should be 5 days"
                print("  ✓ All fixed rules correct ($4 shipping, $0 taxes, 5 days)")
                
                print("\n✅ API TESTS PASSED!")
            else:
                print(f"✗ Failed: {response2.text}")
    else:
        print(f"✗ Failed: {response.text}")
    
    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    test_hicart_api()
