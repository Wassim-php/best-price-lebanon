import re
import json
from typing import List, Optional, Dict, Any
from urllib.parse import quote_plus
import time

import requests
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from ..base import BaseAdapter, OfferData
from ..utils import (
    create_chrome_driver,
    safe_click,
    wait_for_element,
    get_page_text,
    extract_price,
    PRICE_REGEX as _PRICE_RE,
    get_default_headers,
    normalize_image_url,
    build_product_url,
    build_search_url,
    extract_image_url,
    create_pricing_result,
)

class MobileLebAdapter(BaseAdapter):
    source_name = "mobileleb"
    base_url = "https://mobileleb.com"

    def search(self, query: str, limit: int = 10, page: int = 1) -> List[OfferData]:
        # Mobileleb (Shopify) search URL
        search_url = build_search_url(
            self.base_url,
            query,
            page,
            extra_params="type=product"
        )

        headers = get_default_headers()

        try:
            r = requests.get(search_url, headers=headers, timeout=25)
            r.raise_for_status()

            soup = BeautifulSoup(r.text, "lxml")
            offers: List[OfferData] = []

            # Wokiee Theme uses 'div.tt-product' for product cards
            cards = soup.select("div.tt-product")

            for card in cards:
                # 1. Extract Title
                title_el = card.select_one("h2.tt-title a")
                if not title_el:
                    # Sometimes title is in h3 in search view
                    title_el = card.select_one("h3.tt-title a")
                
                if not title_el:
                    continue

                title = title_el.get_text(" ", strip=True)
                href = title_el.get("href")
                url = build_product_url(href, self.base_url)

                # 2. Extract Price
                # Mobileleb structure: <div class="tt-price"><span class="new-price">$99.00</span>...</div>
                # Or just <div class="tt-price"><span>$99.00</span></div>
                price_text = ""
                new_price_el = card.select_one(".new-price")
                if new_price_el:
                    price_text = new_price_el.get_text(strip=True)
                else:
                    # Fallback to any span inside tt-price
                    price_el = card.select_one(".tt-price")
                    if price_el:
                        price_text = price_el.get_text(strip=True)

                item_price = extract_price(price_text)
                if item_price == 0.0:
                    continue

                # 3. Extract Image
                # Use helper function for image extraction with fallbacks
                image_url = extract_image_url(
                    card,
                    selectors=[".tt-img img"],
                    data_attributes=["data-optionimages", "data-src", "src", "srcset"]
                )
                
                # Normalize protocol-relative URLs
                if image_url:
                    image_url = normalize_image_url(image_url)

                # 4. Extract Stock Status
                # Wokiee theme usually has a badge: <span class="tt-label-our-stock">Out of stock</span>
                # Or a specific class on the product div
                in_stock = True
                stock_badge = card.select_one(".soldout_product_badge")
                if stock_badge:
                    # If the badge exists and does NOT have 'hidden' class, it is out of stock
                    classes = stock_badge.get("class", [])
                    if "hidden" not in classes:
                        in_stock = False
                
                # Check for "Sold Out" text explicitly
                if "sold out" in card.get_text().lower():
                    in_stock = False

                offers.append(
                    OfferData(
                        source=self.source_name,
                        title=title,
                        url=url,
                        item_price=item_price,
                        currency="USD",
                        image_url=image_url,
                        in_stock=in_stock,
                    )
                )

                if len(offers) >= limit:
                    break

            return offers

        except Exception as e:
            print(f"Error searching Mobileleb: {e}")
            return []

    def get_detailed_pricing(self, product_url: str, location: str = "outside beirut") -> Dict[str, Any]:
        """
        Scrape detailed pricing including shipping by navigating to cart.
        
        Args:
            product_url: Full URL to the product page
            location: Delivery location - "inside beirut" or "outside beirut" (default: "outside beirut")
                     Note: Shipping fees are calculated on cart page; delivery time is fixed at 1-2 days
        
        Returns:
            Dictionary containing:
                - item_price: Base product price
                - shipping_fee: Shipping cost from cart calculation
                - tax_amount: Tax amount (if applicable)
                - total_price: Final total price
                - currency: Currency code
                - delivery_time: Fixed at "1-2 days" for all Lebanon
                - breakdown: Additional pricing details
        """
        driver = None
        try:
            driver = create_chrome_driver(headless=True, timeout=20)
            
            # --- 1. Load product page and get price ---
            print(f"Loading product: {product_url}")
            driver.get(product_url)
            time.sleep(2)
            
            item_price = 0.0
            try:
                price_element = driver.find_element(By.CSS_SELECTOR, '.price-item--sale, .new-price, .tt-price span')
                item_price = extract_price(price_element.text)
                print(f"✓ Product price: ${item_price}")
            except NoSuchElementException:
                print("⚠ Could not find price on product page")
            
            # --- 2. Calculate shipping based on location (fixed rates) ---
            # Mobileleb has fixed shipping rates:
            # - Beirut: $3.00 USD
            # - Outside Beirut: $5.00 USD
            shipping_fee = 0.0
            tax_amount = 0.0
            delivery_time = "1-2 days"
            
            location_lower = location.lower().strip()
            if location_lower == "inside beirut":
                shipping_fee = 3.0
                print(f"✓ Beirut shipping: $3.00")
            else:
                shipping_fee = 5.0
                print(f"✓ Outside Beirut ({location}) shipping: $5.00")
            
            # --- 3. Calculate total ---
            total_price = item_price + shipping_fee + tax_amount
            
            return create_pricing_result(
                item_price=item_price,
                shipping_fee=shipping_fee if shipping_fee > 0 else None,
                tax_amount=tax_amount if tax_amount > 0 else None,
                total_price=total_price,
                currency="USD",
                delivery_time=delivery_time,
                breakdown={
                    "subtotal": item_price,
                    "shipping": shipping_fee,
                    "tax": tax_amount,
                    "total": total_price,
                    "delivery_time": delivery_time,
                    "delivery_location": location
                }
            )
            
        except Exception as e:
            print(f"✗ Error in get_detailed_pricing: {e}")
            import traceback
            traceback.print_exc()
            return create_pricing_result(
                delivery_time="1-2 days",
                error=str(e)
            )
        finally:
            if driver:
                driver.quit()