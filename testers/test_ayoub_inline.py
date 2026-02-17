"""
Test Ayoub adapter with inline debugging
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import re
from typing import List, Optional
from urllib.parse import quote_plus, urljoin
import requests
from bs4 import BeautifulSoup

# Copy the adapter logic but with debug prints
query = "headphones"
limit = 5
base_url = "https://ayoubcomputers.com"
source_name = "ayoubcomputers"

# Step 1: Get token
search_url = f"{base_url}/search-result/?search_query={quote_plus(query)}"
headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "en-US,en;q=0.9",
}
r = requests.get(search_url, headers=headers, timeout=25)
r.raise_for_status()

token_re = re.compile(r"var\s+storefrontAPIToken\s*=\s*'([^']+)'")
m = token_re.search(r.text)
token = m.group(1).strip()

# Step 2: GraphQL query
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
    "variables": {"term": query, "first": max(1, int(limit))},
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

edges = (
    data.get("data", {})
        .get("site", {})
        .get("search", {})
        .get("searchProducts", {})
        .get("products", {})
        .get("edges", [])
)

print(f"Processing {len(edges)} edges with limit={limit}")
print("=" * 70)

offers = []
for i, edge in enumerate(edges, 1):
    node = (edge or {}).get("node") or {}
    title = (node.get("name") or "").strip()
    path = node.get("path")
    price_obj = (((node.get("prices") or {}).get("price")) or {})
    value = price_obj.get("value")
    currency = price_obj.get("currencyCode") or "USD"
    
    print(f"\nProduct {i}: {title[:50]}")
    print(f"  path={bool(path)}, value={value}, title={bool(title)}")
    print(f"  Check: not title={not title}, not path={not path}, value is None={value is None}")
    
    if not title or not path or value is None:
        print(f"  ❌ SKIPPED (missing data)")
        continue
    
    print(f"  ✓ Has all required data")
    
    product_url = urljoin(base_url, path)
    
    image_url: Optional[str] = None
    default_image = node.get("defaultImage") or {}
    if default_image.get("url"):
        image_url = default_image["url"]
    
    in_stock = True
    avail = node.get("availabilityV2") or {}
    status = (avail.get("status") or "").upper()
    if status in {"OUT_OF_STOCK", "UNAVAILABLE"}:
        in_stock = False
    
    print(f"  status={status}, in_stock={in_stock}")
    print(f"  ✓ ADDED to offers (total: {len(offers) + 1})")
    
    offers.append({
        "title": title,
        "price": float(value),
        "currency": currency,
        "in_stock": in_stock,
    })
    
    if len(offers) >= limit:
        print(f"  🛑 Reached limit of {limit}, breaking")
        break

print(f"\n{'='*70}")
print(f"Final result: {len(offers)} offers")
for i, offer in enumerate(offers, 1):
    print(f"{i}. {offer['title']} - ${offer['price']}")
