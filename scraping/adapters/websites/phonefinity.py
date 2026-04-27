import json
import logging
import re
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus, urljoin

import requests
from bs4 import BeautifulSoup

from ..base import BaseAdapter, OfferData


logger = logging.getLogger(__name__)

_PRICE_RE = re.compile(r"(\d+(?:,\d{3})*(?:\.\d+)?)")


class PhonefinityAdapter(BaseAdapter):
    """Adapter for phonefinity.net WooCommerce search results."""

    source_name = "phonefinity"
    base_url = "https://phonefinity.net"

    SHIPPING_FEE = 5.0
    TAX_AMOUNT = 0.0

    STORE_RATING = 4.8
    DELIVERY_DAYS = 3
    DELIVERY_INSIDE_BEIRUT = "1 business day"
    DELIVERY_OUTSIDE_BEIRUT = "2-4 business days"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        })

    def search(self, query: str, limit: int = 10, page: int = 1) -> List[OfferData]:
        search_url = f"{self.base_url}/?s={quote_plus(query)}&post_type=product"
        if page and page > 1:
            search_url += f"&product-page={page}"

        try:
            logger.info("Searching Phonefinity: %s", search_url)
            response = self.session.get(search_url, timeout=20)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "lxml")
            offers: List[OfferData] = []

            for card in soup.select("div.products > div.product-small"):
                offer = self._parse_search_card(card)
                if offer:
                    offers.append(offer)

                if len(offers) >= limit:
                    break

            return offers

        except Exception as e:
            logger.error("Error searching Phonefinity: %s", e)
            return []

    def get_detailed_pricing(self, product_url: str, location: str = "outside beirut") -> Dict[str, Any]:
        """
        Return final delivered price for Phonefinity.

        Phonefinity has a flat $5 shipping fee for Beirut and outside Beirut,
        and no taxes/VAT.
        """
        try:
            response = self.session.get(product_url, timeout=20)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "lxml")

            item_price = self._extract_product_page_price(soup)
            if item_price is None:
                return {
                    "item_price": 0.0,
                    "shipping_fee": self.SHIPPING_FEE,
                    "tax_amount": self.TAX_AMOUNT,
                    "total_price": self.SHIPPING_FEE,
                    "currency": "USD",
                    "delivery_time": self._delivery_time_for_location(location),
                    "breakdown": {"error": "Could not find product price"},
                }

            shipping_fee = self.SHIPPING_FEE
            tax_amount = self.TAX_AMOUNT
            total_price = round(item_price + shipping_fee + tax_amount, 2)
            delivery_time = self._delivery_time_for_location(location)

            title_el = soup.select_one("h1.product-title, h1.entry-title, h1")
            title = title_el.get_text(" ", strip=True) if title_el else "Unknown Product"

            in_stock = True
            stock_el = soup.select_one(".stock")
            if stock_el and "out of stock" in stock_el.get_text(" ", strip=True).lower():
                in_stock = False

            return {
                "item_price": item_price,
                "shipping_fee": shipping_fee,
                "tax_amount": tax_amount,
                "total_price": total_price,
                "currency": "USD",
                "delivery_time": delivery_time,
                "breakdown": {
                    "title": title,
                    "in_stock": in_stock,
                    "subtotal": item_price,
                    "shipping": shipping_fee,
                    "tax": tax_amount,
                    "total": total_price,
                    "delivery_location": location,
                    "note": "Phonefinity has flat $5 shipping for all Lebanon locations and no taxes/VAT.",
                },
            }

        except Exception as e:
            logger.error("Error getting Phonefinity pricing: %s", e)
            return {
                "item_price": 0.0,
                "shipping_fee": self.SHIPPING_FEE,
                "tax_amount": self.TAX_AMOUNT,
                "total_price": self.SHIPPING_FEE,
                "currency": "USD",
                "delivery_time": self._delivery_time_for_location(location),
                "breakdown": {"error": str(e)},
            }

    def _parse_search_card(self, card) -> Optional[OfferData]:
        title_el = card.select_one("p.name a, .woocommerce-loop-product__title a")
        if not title_el:
            return None

        title = title_el.get_text(" ", strip=True)
        href = title_el.get("href")
        if not title or not href:
            return None

        price_el = card.select_one(".price")
        item_price = self._extract_first_price(price_el.get_text(" ", strip=True) if price_el else "")
        if item_price is None:
            return None

        image_url = self._extract_image_url(card)
        classes = card.get("class", [])
        card_text = card.get_text(" ", strip=True).lower()
        in_stock = (
            "out-of-stock" not in classes
            and "outofstock" not in classes
            and "out of stock" not in card_text
        )

        return OfferData(
            source=self.source_name,
            title=title,
            url=urljoin(self.base_url, href),
            item_price=item_price,
            currency="USD",
            in_stock=in_stock,
            image_url=image_url,
        )

    def _extract_product_page_price(self, soup: BeautifulSoup) -> Optional[float]:
        meta_price = soup.find("meta", property="product:price:amount")
        if meta_price:
            price = self._extract_first_price(meta_price.get("content", ""))
            if price is not None:
                return price

        json_ld_price = self._extract_json_ld_price(soup)
        if json_ld_price is not None:
            return json_ld_price

        selectors = [
            ".product-info .price",
            ".summary .price",
            "p.price",
            ".price",
        ]
        for selector in selectors:
            price_el = soup.select_one(selector)
            if price_el:
                price = self._extract_first_price(price_el.get_text(" ", strip=True))
                if price is not None:
                    return price

        return None

    def _extract_json_ld_price(self, soup: BeautifulSoup) -> Optional[float]:
        for script in soup.find_all("script", type="application/ld+json"):
            if not script.string:
                continue
            try:
                data = json.loads(script.string)
            except json.JSONDecodeError:
                continue

            price = self._price_from_json_ld(data)
            if price is not None:
                return price

        return None

    def _price_from_json_ld(self, data: Any) -> Optional[float]:
        if isinstance(data, list):
            for item in data:
                price = self._price_from_json_ld(item)
                if price is not None:
                    return price
            return None

        if not isinstance(data, dict):
            return None

        graph = data.get("@graph")
        if graph:
            price = self._price_from_json_ld(graph)
            if price is not None:
                return price

        offers = data.get("offers")
        if isinstance(offers, list):
            for offer in offers:
                price = self._price_from_json_ld(offer)
                if price is not None:
                    return price
        elif isinstance(offers, dict):
            price = self._price_from_json_ld(offers)
            if price is not None:
                return price

        for key in ("price", "lowPrice"):
            if data.get(key) is not None:
                return self._extract_first_price(str(data[key]))

        return None

    def _extract_first_price(self, text: str) -> Optional[float]:
        if not text:
            return None

        for match in _PRICE_RE.findall(text):
            price = float(match.replace(",", ""))
            if 0 < price < 50000:
                return price

        return None

    def _extract_image_url(self, card) -> Optional[str]:
        img_el = card.select_one("img")
        if not img_el:
            return None

        for attr in ("data-src", "data-lazy-src", "src"):
            image_url = self._normalize_image_url(img_el.get(attr))
            if image_url:
                return image_url

        srcset = img_el.get("srcset")
        if srcset:
            return self._normalize_image_url(srcset.split(",")[0].strip().split(" ")[0])

        return None

    def _normalize_image_url(self, image_url: Optional[str]) -> Optional[str]:
        if not image_url:
            return None

        image_url = image_url.strip()
        if not image_url or image_url.startswith("data:"):
            return None

        if image_url.startswith("//"):
            return "https:" + image_url

        return urljoin(self.base_url, image_url)

    def _delivery_time_for_location(self, location: str) -> str:
        location_lower = (location or "").lower().strip()
        if "inside" in location_lower or location_lower == "beirut":
            return self.DELIVERY_INSIDE_BEIRUT
        return self.DELIVERY_OUTSIDE_BEIRUT
