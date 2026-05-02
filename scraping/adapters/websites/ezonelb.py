import json
import logging
import re
from html import unescape
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from ..base import BaseAdapter, OfferData


logger = logging.getLogger(__name__)

_PRICE_RE = re.compile(r"(\d+(?:,\d{3})*(?:\.\d+)?)")


class EzoneLbAdapter(BaseAdapter):
    """Adapter for ezonelb.com WooCommerce search results."""

    source_name = "ezonelb"
    base_url = "https://ezonelb.com"

    STORE_RATING = 4.5
    DELIVERY_DAYS = 2

    SHIPPING_INSIDE_BEIRUT = 0.0
    SHIPPING_OUTSIDE_BEIRUT = 3.0
    TAX_AMOUNT = 0.0

    DELIVERY_INSIDE_BEIRUT = "1 business day"
    DELIVERY_OUTSIDE_BEIRUT = "2-3 business days"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "BestPriceLebanon/1.0",
            "Accept": "application/json,text/html;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        })

    def search(self, query: str, limit: int = 10, page: int = 1) -> List[OfferData]:
        if page and page > 1:
            search_url = (
                f"{self.base_url}/page/{page}/"
                f"?s={quote_plus(query)}&post_type=product&dgwt_wcas=1"
            )
        else:
            search_url = (
                f"{self.base_url}/?s={quote_plus(query)}"
                "&post_type=product&dgwt_wcas=1"
            )

        try:
            logger.info("Searching Ezone LB: %s", search_url)
            response = self.session.get(search_url, timeout=20)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "lxml")
            offers: List[OfferData] = []

            for card in soup.select("div.products div.wd-product, div.products div.product-grid-item"):
                offer = self._parse_search_card(card)
                if offer:
                    offers.append(offer)

                if len(offers) >= limit:
                    break

            return offers

        except Exception as e:
            logger.error("Error searching Ezone LB: %s", e)
            return self._search_store_api(query, limit=limit, page=page)

    def get_detailed_pricing(self, product_url: str, location: str = "outside beirut") -> Dict[str, Any]:
        """Return final delivered price for Ezone LB.

        Ezone LB has no taxes. Delivery is free inside Beirut and $3 outside
        Beirut.
        """
        try:
            product = self._get_store_api_product(product_url)
            item_price = self._price_from_store_api_product(product) if product else None
            title = unescape(product.get("name", "Unknown Product")) if product else "Unknown Product"
            in_stock = bool(product.get("is_in_stock", True)) if product else True

            if item_price is None:
                response = self.session.get(product_url, timeout=20)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, "lxml")

                item_price = self._extract_product_page_price(soup)

                title_el = soup.select_one("h1.product_title, h1.product-title, h1.entry-title, h1")
                title = title_el.get_text(" ", strip=True) if title_el else title

                stock_el = soup.select_one(".stock")
                stock_text = stock_el.get_text(" ", strip=True).lower() if stock_el else ""
                in_stock = "out of stock" not in stock_text

            delivery_zone = self._delivery_zone(location)
            shipping_fee = self._shipping_fee_for_zone(delivery_zone)
            delivery_time = self._delivery_time_for_zone(delivery_zone)

            if item_price is None:
                return {
                    "item_price": 0.0,
                    "shipping_fee": shipping_fee,
                    "tax_amount": self.TAX_AMOUNT,
                    "total_price": shipping_fee,
                    "currency": "USD",
                    "delivery_time": delivery_time,
                    "breakdown": {"error": "Could not find product price"},
                }

            tax_amount = self.TAX_AMOUNT
            total_price = round(item_price + shipping_fee + tax_amount, 2)

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
                    "note": (
                        "Ezone LB has no taxes. Delivery is free inside Beirut "
                        "and $3 outside Beirut."
                    ),
                },
            }

        except Exception as e:
            logger.error("Error getting Ezone LB pricing: %s", e)
            delivery_zone = self._delivery_zone(location)
            return {
                "item_price": 0.0,
                "shipping_fee": self._shipping_fee_for_zone(delivery_zone),
                "tax_amount": self.TAX_AMOUNT,
                "total_price": self._shipping_fee_for_zone(delivery_zone),
                "currency": "USD",
                "delivery_time": self._delivery_time_for_zone(delivery_zone),
                "breakdown": {"error": str(e)},
            }

    def _search_store_api(self, query: str, limit: int = 10, page: int = 1) -> List[OfferData]:
        per_page = max(1, min(limit or 10, 100))
        api_url = (
            f"{self.base_url}/wp-json/wc/store/v1/products"
            f"?search={quote_plus(query)}&per_page={per_page}&page={page or 1}"
        )

        try:
            logger.info("Searching Ezone LB Store API: %s", api_url)
            response = self.session.get(api_url, headers={"Accept": "application/json"}, timeout=20)
            response.raise_for_status()
            products = response.json()

            if not isinstance(products, list):
                return []

            offers = []
            for product in products:
                offer = self._parse_store_api_product(product)
                if offer:
                    offers.append(offer)

                if len(offers) >= limit:
                    break

            return offers

        except Exception as e:
            logger.warning("Error searching Ezone LB Store API: %s", e)
            return []

    def _parse_store_api_product(self, product: Dict[str, Any]) -> Optional[OfferData]:
        title = unescape(product.get("name") or "")
        url = product.get("permalink")
        item_price = self._price_from_store_api_product(product)
        if not title or not url or item_price is None:
            return None

        image_url = None
        images = product.get("images") or []
        if images and isinstance(images, list):
            first_image = images[0] or {}
            image_url = first_image.get("thumbnail") or first_image.get("src")

        return OfferData(
            source=self.source_name,
            title=title,
            url=url,
            item_price=item_price,
            currency=(product.get("prices") or {}).get("currency_code", "USD"),
            in_stock=bool(product.get("is_in_stock", True)),
            image_url=image_url,
        )

    def _get_store_api_product(self, product_url: str) -> Optional[Dict[str, Any]]:
        slug = self._slug_from_product_url(product_url)
        if not slug:
            return None

        api_url = f"{self.base_url}/wp-json/wc/store/v1/products?slug={quote_plus(slug)}"
        try:
            response = self.session.get(api_url, headers={"Accept": "application/json"}, timeout=20)
            response.raise_for_status()
            products = response.json()
        except Exception as e:
            logger.warning("Error fetching Ezone LB Store API product: %s", e)
            return None

        if isinstance(products, list) and products:
            return products[0]
        return None

    def _price_from_store_api_product(self, product: Optional[Dict[str, Any]]) -> Optional[float]:
        if not product:
            return None

        prices = product.get("prices") or {}
        price_range = prices.get("price_range") or {}
        raw_price = (
            prices.get("price")
            or prices.get("sale_price")
            or price_range.get("min_amount")
            or price_range.get("min_price")
            or prices.get("regular_price")
        )
        price = self._extract_first_price(str(raw_price or ""))
        if price is None:
            return None

        minor_unit = prices.get("currency_minor_unit", 0)
        if isinstance(minor_unit, int) and minor_unit > 0:
            price = price / (10 ** minor_unit)

        return price

    def _slug_from_product_url(self, product_url: str) -> Optional[str]:
        path = urlparse(product_url).path.strip("/")
        parts = [part for part in path.split("/") if part]
        if not parts:
            return None
        if parts[0] == "product" and len(parts) > 1:
            return parts[1]
        return parts[-1]

    def _parse_search_card(self, card) -> Optional[OfferData]:
        title_el = card.select_one("h3.wd-entities-title a, .woocommerce-loop-product__title a")
        if not title_el:
            return None

        title = title_el.get_text(" ", strip=True)
        href = title_el.get("href")
        if not title or not href:
            return None

        price_el = card.select_one(".price")
        item_price = self._extract_display_price(price_el) if price_el else None
        if item_price is None:
            return None

        classes = card.get("class", [])
        card_text = card.get_text(" ", strip=True).lower()
        in_stock = (
            "outofstock" not in classes
            and "out-of-stock" not in classes
            and "out of stock" not in card_text
        )

        return OfferData(
            source=self.source_name,
            title=title,
            url=urljoin(self.base_url, href),
            item_price=item_price,
            currency="USD",
            in_stock=in_stock,
            image_url=self._extract_image_url(card),
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

        for selector in (".summary .price", ".product-info .price", "p.price", ".price"):
            price_el = soup.select_one(selector)
            if price_el:
                price = self._extract_display_price(price_el)
                if price is not None:
                    return price

        return None

    def _extract_json_ld_price(self, soup: BeautifulSoup) -> Optional[float]:
        for script in soup.find_all("script", type="application/ld+json"):
            script_text = script.string or script.get_text()
            if not script_text:
                continue
            try:
                data = json.loads(script_text)
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

    def _extract_display_price(self, price_el) -> Optional[float]:
        sale_el = price_el.select_one("ins .woocommerce-Price-amount, ins")
        if sale_el:
            sale_price = self._extract_first_price(sale_el.get_text(" ", strip=True))
            if sale_price is not None:
                return sale_price

        for hidden_text in price_el.select(".screen-reader-text"):
            hidden_text.extract()

        return self._extract_first_price(price_el.get_text(" ", strip=True))

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

        srcset = img_el.get("data-srcset") or img_el.get("srcset")
        if srcset:
            return self._normalize_image_url(srcset.split(",")[0].strip().split(" ")[0])

        return None

    def _normalize_image_url(self, image_url: Optional[str]) -> Optional[str]:
        if not image_url:
            return None

        image_url = image_url.strip()
        if not image_url or image_url.startswith("data:") or image_url.endswith("/lazy.svg"):
            return None

        if image_url.startswith("//"):
            return "https:" + image_url

        return urljoin(self.base_url, image_url)

    def _delivery_zone(self, location: str) -> str:
        location_lower = (location or "").lower()
        if "outside" in location_lower:
            return "outside_beirut"
        if "beirut" in location_lower:
            return "inside_beirut"
        return "outside_beirut"

    def _shipping_fee_for_zone(self, delivery_zone: str) -> float:
        if delivery_zone == "inside_beirut":
            return self.SHIPPING_INSIDE_BEIRUT
        return self.SHIPPING_OUTSIDE_BEIRUT

    def _delivery_time_for_zone(self, delivery_zone: str) -> str:
        if delivery_zone == "inside_beirut":
            return self.DELIVERY_INSIDE_BEIRUT
        return self.DELIVERY_OUTSIDE_BEIRUT
