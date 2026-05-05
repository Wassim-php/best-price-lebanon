import json
import re
from typing import List, Optional, Dict, Any
from urllib.parse import quote_plus, urljoin

import requests
from bs4 import BeautifulSoup

from ..base import BaseAdapter, OfferData


# Regex to match prices, with or without commas: 1234.56 or 1,234.56
_PRICE_RE = re.compile(r"(\d+(?:,\d{3})*(?:\.\d+)?)")


def _extract_last_price(text: str) -> Optional[float]:
    if not text:
        return None
    matches = _PRICE_RE.findall(text)
    if not matches:
        return None
    return float(matches[-1].replace(',', ''))

class Souq961Adapter(BaseAdapter):
    source_name = "961souq"
    base_url = "https://961souq.com"
    
    # Store metadata for scoring
    STORE_RATING = 4.5  # Out of 5.0
    DELIVERY_DAYS = 4  # Typical delivery time in days

    def search(self, query: str, limit: int = 10, page: int = 1) -> List[OfferData]:
        # Example: https://961souq.com/search?q=hp+victus&page=2
        search_url = f"{self.base_url}/search?q={quote_plus(query)}"
        if page and page > 1:
            search_url += f"&page={page}"

        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept-Language": "en-US,en;q=0.9",
        }

        r = requests.get(search_url, headers=headers, timeout=25)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "lxml")

        offers: List[OfferData] = []

        cards = soup.select("a.search-result-card")
        for card in cards:
            title_el = card.select_one("h3.search-result-title")
            price_el = card.select_one("p.search-result-price")
            img_el = card.select_one("img.search-result-image")

            href = card.get("href")

            if not title_el or not price_el or not href:
                continue

            title = title_el.get_text(" ", strip=True)

            raw_price = price_el.get_text(" ", strip=True)
            item_price = _extract_last_price(raw_price)
            if item_price is None:
                continue

            url = urljoin(self.base_url, href)

            image_url: Optional[str] = None
            if img_el and img_el.get("src"):
                image_url = img_el["src"]

            offers.append(
                OfferData(
                    source=self.source_name,
                    title=title,
                    url=url,
                    item_price=item_price,
                    currency="USD",
                    image_url=image_url,
                    in_stock=True,  # Search page doesn't show stock; default True for now
                )
            )

            if len(offers) >= limit:
                break

        return offers

    def get_detailed_pricing(self, product_url: str, location: str = "outside beirut") -> Dict[str, Any]:
        """
        Get product pricing with estimated shipping using JSON/HTML scraping.

        Args:
            product_url: Full URL to the product page
            location: Delivery location - "inside beirut" or "outside beirut" (default: "outside beirut")

        Returns:
            Dictionary containing:
                - item_price: Base product price
                - shipping_fee: Shipping cost (estimated based on location)
                - tax_amount: Tax amount (fixed at 0%)
                - total_price: Final total price
                - currency: Currency code
                - delivery_time: Estimated delivery time
                - breakdown: Additional pricing details if available
        """
        location_lower = location.lower().strip()
        if 'inside' in location_lower:
            location_display = "Beirut (inside Beirut)"
            shipping_fee = 3.0
            delivery_time = "2-3 business days"
        elif 'outside' in location_lower:
            location_display = "Koura (outside Beirut)"
            shipping_fee = 5.0
            delivery_time = "3-5 business days"
        else:
            location_display = location.title()
            shipping_fee = 5.0
            delivery_time = "3-5 business days"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        }

        item_price = 0.0

        try:
            # Prefer Shopify product JSON when available.
            for json_url in (f"{product_url}.js", f"{product_url}.json"):
                try:
                    json_resp = requests.get(json_url, headers=headers, timeout=10)
                    if not json_resp.ok:
                        continue
                    data = json_resp.json()
                    variants = data.get("variants", []) if isinstance(data, dict) else []
                    if not variants:
                        continue
                    variant = next((v for v in variants if v.get("available")), variants[0])
                    price = variant.get("price")
                    if price is None:
                        continue
                    price_val = float(price)
                    # Shopify prices are usually in cents.
                    if price_val > 10000:
                        price_val = price_val / 100.0
                    item_price = round(price_val, 2)
                    break
                except Exception:
                    continue

            if item_price == 0.0:
                response = requests.get(product_url, headers=headers, timeout=15)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'lxml')

                # Try JSON-LD price first.
                for script in soup.select('script[type="application/ld+json"]'):
                    try:
                        data = json.loads(script.string or "")
                    except Exception:
                        continue
                    items = data if isinstance(data, list) else [data]
                    for item in items:
                        offers = item.get("offers") if isinstance(item, dict) else None
                        if isinstance(offers, dict):
                            price = offers.get("price")
                            if price is not None:
                                item_price = float(price)
                                break
                        if isinstance(offers, list) and offers:
                            price = offers[0].get("price")
                            if price is not None:
                                item_price = float(price)
                                break
                    if item_price > 0:
                        break

                # Fallback to visible price elements.
                if item_price == 0.0:
                    price_selectors = [
                        'span[class*="current"]',
                        'span[class*="sale"]',
                        'span[class*="actual"]',
                        'div[class*="current"]',
                        'div[class*="sale"]',
                        'span.price:not(.old):not(.crossed)',
                        'span.product-price',
                        'div.product-price',
                        'span[class*="price"]',
                        'div[class*="price"]',
                    ]
                    for selector in price_selectors:
                        price_elem = soup.select_one(selector)
                        if not price_elem:
                            continue
                        raw_price = price_elem.get_text(" ", strip=True)
                        extracted = _extract_last_price(raw_price)
                        if extracted is not None and extracted > 0:
                            item_price = extracted
                            break

            if item_price == 0.0:
                return {
                    "item_price": 0.0,
                    "shipping_fee": None,
                    "tax_amount": None,
                    "total_price": 0.0,
                    "currency": "USD",
                    "delivery_time": None,
                    "breakdown": {"error": "Could not extract price from product page", "delivery_location": location_display}
                }

            tax_amount = 0.0
            total_price = round(item_price + shipping_fee + tax_amount, 2)

            return {
                "item_price": round(item_price, 2),
                "shipping_fee": shipping_fee,
                "tax_amount": tax_amount,
                "total_price": total_price,
                "currency": "USD",
                "delivery_time": delivery_time,
                "breakdown": {
                    "subtotal": round(item_price, 2),
                    "shipping": shipping_fee,
                    "tax": tax_amount,
                    "total": total_price,
                    "delivery_time": delivery_time,
                    "delivery_location": location_display
                }
            }

        except Exception as e:
            print(f"Error in get_detailed_pricing: {e}")
            return {
                "item_price": 0.0,
                "shipping_fee": None,
                "tax_amount": None,
                "total_price": 0.0,
                "currency": "USD",
                "delivery_time": None,
                "breakdown": {"error": str(e), "delivery_location": location_display}
            }
