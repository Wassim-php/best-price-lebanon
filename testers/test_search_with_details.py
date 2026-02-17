"""
Test the new search-with-details endpoint
This endpoint combines AI-filtered search with detailed pricing
Run from testers directory: python test_search_with_details.py
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000/api"

def test_search_with_details(source_key, query, location="outside beirut"):
    """Test the search-with-details endpoint"""
    url = f"{BASE_URL}/search-with-details/{source_key}"
    
    payload = {
        "query": query,
        "location": location
    }
    
    print("=" * 80)
    print(f"Testing: {source_key.upper()} - Query: '{query}'")
    print("=" * 80)
    print(f"POST {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print("\nSending request...\n")
    
    try:
        response = requests.post(url, json=payload, timeout=60)
        
        print(f"Status Code: {response.status_code}")
        print(f"\nResponse:")
        print("=" * 80)
        
        if response.status_code == 200:
            data = response.json()
            print(json.dumps(data, indent=2))
            
            # Pretty print the results
            print("\n" + "=" * 80)
            print("FORMATTED RESULTS")
            print("=" * 80)
            
            if "product" in data:
                print(f"\n📦 PRODUCT:")
                print(f"  Title: {data['product']['title']}")
                print(f"  URL: {data['product']['url']}")
                print(f"  In Stock: {'✓' if data['product'].get('in_stock', True) else '✗'}")
                if data['product'].get('image_url'):
                    print(f"  Image: {data['product']['image_url'][:60]}...")
            
            if "pricing" in data:
                pricing = data['pricing']
                print(f"\n💰 PRICING:")
                print(f"  Item Price: ${pricing['item_price']:.2f}")
                
                if pricing.get('shipping_fee') is not None:
                    if pricing['shipping_fee'] == 0:
                        print(f"  Shipping: FREE")
                    else:
                        print(f"  Shipping: ${pricing['shipping_fee']:.2f}")
                
                if pricing.get('tax_amount') is not None:
                    print(f"  Tax: ${pricing['tax_amount']:.2f}")
                
                print(f"  💵 TOTAL: ${pricing['total_price']:.2f} {pricing.get('currency', 'USD')}")
                
                if pricing.get('delivery_time'):
                    print(f"  🚚 Delivery: {pricing['delivery_time']}")
                
                if pricing.get('breakdown'):
                    print(f"\n  Breakdown:")
                    for key, value in pricing['breakdown'].items():
                        print(f"    • {key}: {value}")
            
            print(f"\n🏪 Source: {data.get('source', 'N/A')}")
            print(f"🔍 Query: {data.get('query', 'N/A')}")
            
        else:
            print(json.dumps(response.json(), indent=2))
        
        print("=" * 80)
        print()
        
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Could not connect to server.")
        print("Please make sure Django server is running: python manage.py runserver")
        print("=" * 80)
        print()
    except Exception as e:
        print(f"❌ ERROR: {type(e).__name__}: {str(e)}")
        print("=" * 80)
        print()

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("TESTING SEARCH-WITH-DETAILS ENDPOINT")
    print("=" * 80)
    print()
    
    # Test 1: Ayoub Computers - headphones
    test_search_with_details("ayoubcomputers", "headphones")
    
    # Test 2: Ayoub Computers - iPhone
    test_search_with_details("ayoubcomputers", "iPhone 15")
    
    # Test 3: 961souq - laptop
    test_search_with_details("961souq", "HP laptop")
    
    # Test 4: With different location
    test_search_with_details("ayoubcomputers", "wireless mouse", location="inside beirut")
    
    print("\n" + "=" * 80)
    print("ALL TESTS COMPLETED")
    print("=" * 80)
