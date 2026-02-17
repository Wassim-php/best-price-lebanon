"""
Debug the Ayoub Computers adapter to see what's happening with search
Run from testers directory: python test_ayoub_debug.py
"""
import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from urllib.parse import quote_plus, urljoin
import re

# Test search for headphones
query = "headphones"
base_url = "https://ayoubcomputers.com"
search_url = f"{base_url}/search-result/?search_query={quote_plus(query)}"

print("=" * 70)
print(f"DEBUG: Searching for '{query}'")
print("=" * 70)

# Step 1: Get the token
print(f"\n1. Fetching token from: {search_url}")
headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "en-US,en;q=0.9",
}
r = requests.get(search_url, headers=headers, timeout=25)
r.raise_for_status()

token_re = re.compile(r"var\s+storefrontAPIToken\s*=\s*'([^']+)'")
m = token_re.search(r.text)
if m:
    token = m.group(1).strip()
    print(f"✓ Token found: {token[:20]}...")
else:
    print("✗ Token NOT found!")
    print("First 1000 chars of HTML:")
    print(r.text[:1000])
    sys.exit(1)

# Step 2: Make GraphQL request
print(f"\n2. Making GraphQL request...")

gql = """
query SearchProducts($term: String!, $first: Int!) {
  site {
    search {
      searchProducts(filters: { searchTerm: $term }) {
        products(first: $first) {
          edges {
            node {
              name
              path
              availabilityV2 {
                status
              }
              defaultImage {
                url(width: 300)
              }
              prices {
                price {
                  value
                  currencyCode
                }
              }
            }
          }
        }
      }
    }
  }
}
"""

payload = {
    "query": gql,
    "variables": {"term": query, "first": 10},
}

headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "en-US,en;q=0.9",
    "Content-Type": "application/json",
    "Authorization": f"Bearer {token}",
}

r = requests.post(
    urljoin(base_url, "/graphql"),
    json=payload,
    headers=headers,
    timeout=25,
)
r.raise_for_status()

data = r.json()

print(f"\n3. GraphQL Response:")
print(json.dumps(data, indent=2))

# Step 3: Parse response
edges = (
    data.get("data", {})
        .get("site", {})
        .get("search", {})
        .get("searchProducts", {})
        .get("products", {})
        .get("edges", [])
)

print(f"\n4. Found {len(edges)} edges in response")

for i, edge in enumerate(edges, 1):
    node = (edge or {}).get("node") or {}
    title = (node.get("name") or "").strip()
    path = node.get("path")
    price_obj = (((node.get("prices") or {}).get("price")) or {})
    value = price_obj.get("value")
    
    print(f"\nProduct {i}:")
    print(f"  Title: {title}")
    print(f"  Path: {path}")
    print(f"  Price: {value}")
    print(f"  Has title: {bool(title)}")
    print(f"  Has path: {bool(path)}")
    print(f"  Has value: {value is not None}")
    print(f"  Would include: {bool(title and path and value is not None)}")
