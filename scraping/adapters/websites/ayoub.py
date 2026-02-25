import re
from typing import List, Optional, Dict, Any
from urllib.parse import urljoin, quote_plus

import requests
from bs4 import BeautifulSoup

from ..base import BaseAdapter, OfferData
from ..utils import (
    extract_price,
    PRICE_REGEX as _PRICE_RE,
    get_default_headers,
    get_graphql_headers,
    build_product_url,
    extract_price_from_json_ld,
    create_pricing_result,
    calculate_tax,
)


_TOKEN_RE = re.compile(r"var\s+storefrontAPIToken\s*=\s*'([^']+)'")


class AyoubComputersAdapter(BaseAdapter):
    source_name = "ayoubcomputers"
    base_url = "https://ayoubcomputers.com"
    graphql_path = "/graphql"

    def _get_storefront_token(self, html: str) -> str:
        m = _TOKEN_RE.search(html)
        if not m:
            raise RuntimeError("Could not find storefrontAPIToken in Ayoub search HTML.")
        return m.group(1).strip()

    def _fetch_token_from_search_page(self, query: str) -> str:
        search_url = f"{self.base_url}/search-result/?search_query={quote_plus(query)}"
        headers = get_default_headers()
        r = requests.get(search_url, headers=headers, timeout=25)
        r.raise_for_status()
        return self._get_storefront_token(r.text)

    def search(self, query: str, limit: int = 10, page: int = 1) -> List[OfferData]:
        """
        Ayoub Computers search (BigCommerce Storefront GraphQL).
        NOTE: page param is ignored for now (GraphQL uses cursor-based pagination).
        """
        token = self._fetch_token_from_search_page(query=query)

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

        # Request more products than limit since many may have null prices
        # This ensures we can filter and still return enough valid offers
        fetch_count = max(20, int(limit) * 3)
        
        payload = {
            "query": gql,
            "variables": {"term": query, "first": fetch_count},
        }

        headers = get_graphql_headers(token)

        r = requests.post(
            urljoin(self.base_url, self.graphql_path),
            json=payload,
            headers=headers,
            timeout=25,
        )
        r.raise_for_status()

        data = r.json()
        if "errors" in data and data["errors"]:
            raise RuntimeError(f"GraphQL errors: {data['errors']}")

        edges = (
            data.get("data", {})
                .get("site", {})
                .get("search", {})
                .get("searchProducts", {})
                .get("products", {})
                .get("edges", [])
        )

        offers: List[OfferData] = []
        for edge in edges:
            node = (edge or {}).get("node") or {}
            title = (node.get("name") or "").strip()
            path = node.get("path")  # usually like "/some-product/"
            price_obj = (((node.get("prices") or {}).get("price")) or {})
            value = price_obj.get("value")
            currency = price_obj.get("currencyCode") or "USD"

            if not title or not path or value is None:
                continue

            product_url = build_product_url(path, self.base_url)

            image_url: Optional[str] = None
            default_image = node.get("defaultImage") or {}
            if default_image.get("url"):
                image_url = default_image["url"]

            # availabilityV2.status can be "IN_STOCK" / "OUT_OF_STOCK" etc.
            in_stock = True
            avail = node.get("availabilityV2") or {}
            status = (avail.get("status") or "").upper()
            if status in {"OUT_OF_STOCK", "UNAVAILABLE"}:
                in_stock = False

            offers.append(
                OfferData(
                    source=self.source_name,
                    title=title,
                    url=product_url,
                    item_price=float(value),
                    currency=currency,
                    image_url=image_url,
                    in_stock=in_stock,
                )
            )

            if len(offers) >= limit:
                break

        return offers

    def get_detailed_pricing(self, product_url: str, location: str = "outside beirut") -> Dict[str, Any]:
        """
        Get detailed pricing for Ayoub Computers products.
        
        Ayoub Computers has fixed pricing:
        - Delivery is always FREE
        - Taxes are always 11%
        - Delivery time is always 2-6 business days
        
        Args:
            product_url: Full URL to the product page
            location: Delivery location (not used for Ayoub, as pricing is fixed)
            
        Returns:
            Dictionary containing:
                - item_price: Base product price
                - shipping_fee: Shipping cost (always 0)
                - tax_amount: Tax amount (11% of item price)
                - total_price: Final total price (item_price * 1.11)
                - currency: Currency code (USD)
                - delivery_time: Estimated delivery time
                - breakdown: Additional pricing details
        """
        headers = get_default_headers()
        
        try:
            # Fetch the product page
            r = requests.get(product_url, headers=headers, timeout=25)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "lxml")
            
            # Extract product price from various possible selectors
            item_price = 0.0
            
            # Try different price selectors used by BigCommerce
            price_selectors = [
                '.price--withoutTax',
                '.price-section .price',
                '[data-product-price-without-tax]',
                '.productView-price .price',
                'span.price',
            ]
            
            for selector in price_selectors:
                price_el = soup.select_one(selector)
                if price_el:
                    item_price = extract_price(price_el.get_text(strip=True))
                    if item_price > 0:
                        break
            
            # If we couldn't find the price, try JSON-LD data
            if item_price == 0.0:
                json_ld_price = extract_price_from_json_ld(soup)
                if json_ld_price:
                    item_price = json_ld_price
            
            if item_price == 0.0:
                return create_pricing_result(
                    error="Could not extract product price from page"
                )
            
            # Fixed pricing rules for Ayoub Computers
            shipping_fee = 0.0  # Always free
            tax_rate = 0.11  # Always 11%
            tax_amount = calculate_tax(item_price, tax_rate)
            total_price = round(item_price + tax_amount, 2)
            delivery_time = "2-6 business days"
            
            return create_pricing_result(
                item_price=item_price,
                shipping_fee=shipping_fee,
                tax_amount=tax_amount,
                total_price=total_price,
                currency="USD",
                delivery_time=delivery_time,
                breakdown={
                    "Item Price": f"${item_price:.2f}",
                    "Shipping": "FREE",
                    "Tax (11%)": f"${tax_amount:.2f}",
                    "Total": f"${total_price:.2f}",
                    "Delivery Time": delivery_time,
                    "Note": "Ayoub Computers offers free delivery with 11% tax on all orders"
                }
            )
            
        except requests.RequestException as e:
            return create_pricing_result(
                error=f"Failed to fetch product page: {str(e)}"
            )
        except Exception as e:
            return create_pricing_result(
                error=f"Unexpected error: {str(e)}"
            )
