"""
Quick test script for the comparisons endpoint
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_compare_endpoint():
    """Test the compare all sources endpoint"""
    print("🔍 Testing Comparisons Endpoint")
    print("=" * 60)
    
    # Test data
    payload = {
        "query": "samsung",
        "location": "outside beirut",
        "save": True
    }
    
    print(f"\n📤 Request:")
    print(f"URL: {BASE_URL}/api/comparisons/compare")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    print("\n⏳ Sending request... (this may take 20-40 seconds)")
    start_time = time.time()
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/comparisons/compare",
            json=payload,
            timeout=120  # Increased to 2 minutes
        )
        
        elapsed = time.time() - start_time
        
        print(f"\n✅ Response received in {elapsed:.2f} seconds")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"\n📊 Results Summary:")
            print(f"Query: {data['query']}")
            print(f"Location: {data['location']}")
            if 'search_id' in data:
                print(f"Search ID: {data['search_id']}")
            
            print(f"\n🏪 Sites:")
            print(f"  Checked: {data['metadata']['sites_checked']}")
            print(f"  Succeeded: {data['metadata']['sites_succeeded']}")
            print(f"  Failed: {data['metadata']['sites_failed']}")
            
            if data['metadata']['failed_sources']:
                print(f"\n❌ Failed Sources:")
                for source in data['metadata']['failed_sources']:
                    print(f"  - {source['source']}: {source['error']}")
            
            print(f"\n💰 Pricing:")
            print(f"  Min Price: ${data['metadata']['min_price']:.2f}")
            
            print(f"\n🏆 Top 3 Results (by score):")
            for i, result in enumerate(data['results'][:3], 1):
                print(f"\n  #{i} - Score: {result['score']}/10")
                print(f"      Source: {result['source']}")
                print(f"      Title: {result['product']['title'][:60]}...")
                print(f"      Total Price: ${result['pricing']['total_price']}")
                print(f"      Store Rating: {result['store_rating']}/5.0")
                print(f"      Delivery: {result['delivery_days']} days")
                print(f"      Score Breakdown:")
                print(f"        - Price: {result['score_breakdown']['price_score']}/10")
                print(f"        - Delivery: {result['score_breakdown']['delivery_score']}/10")
                print(f"        - Trust: {result['score_breakdown']['trust_score']}/10")
            
            print(f"\n📝 Full Response saved to: test_compare_response.json")
            with open('test_compare_response.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return True
        else:
            print(f"\n❌ Error Response:")
            print(json.dumps(response.json(), indent=2))
            return False
            
    except requests.exceptions.Timeout:
        print(f"\n⏰ Request timed out after 60 seconds")
        return False
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_compare_endpoint()
    
    if success:
        print("\n" + "=" * 60)
        print("✨ Test completed successfully!")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("⚠️  Test failed!")
        print("=" * 60)
