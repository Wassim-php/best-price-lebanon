"""
Example: souq961.py refactored to use utils

This demonstrates how to use the new utils to make your adapters cleaner and more maintainable.
"""

import re
from typing import List, Optional, Dict, Any
from urllib.parse import quote_plus, urljoin
import time

import requests
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By

from ..base import BaseAdapter, OfferData
from ..utils import (
    # Selenium helpers
    create_chrome_driver,
    safe_click,
    wait_for_element,
    scroll_to_bottom,
    find_element_with_fallbacks,
    
    # Price helpers
    extract_price,
    PRICE_REGEX,
    extract_all_prices,
    
    # Request helpers
    get_default_headers,
    
    # URL helpers
    build_product_url,
    build_search_url,
    
    # Extraction helpers
    extract_delivery_location_display,
    create_pricing_result,
)


class Souq961AdapterRefactored(BaseAdapter):
    """
    Refactored Souq961 adapter using utils for better code organization.
    """
    source_name = "961souq"
    base_url = "https://961souq.com"

    def search(self, query: str, limit: int = 10, page: int = 1) -> List[OfferData]:
        """Search for products using cleaner code with utils."""
        
        # Use helper to build search URL
        search_url = build_search_url(self.base_url, query, page)
        
        # Use helper to get headers
        headers = get_default_headers()
        
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
            
            # Use helper to extract price
            raw_price = price_el.get_text(" ", strip=True)
            item_price = extract_price(raw_price)
            if item_price == 0.0:
                continue

            # Use helper to build product URL
            url = build_product_url(href, self.base_url)
            
            # Extract image
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
                    in_stock=True,
                )
            )

            if len(offers) >= limit:
                break

        return offers

    def get_detailed_pricing(self, product_url: str, location: str = "outside beirut") -> Dict[str, Any]:
        """
        Get detailed pricing using utils for cleaner code.
        """
        # Use helper to format location
        location_display = extract_delivery_location_display(location)
        
        # Use helper to create driver
        driver = None
        try:
            driver = create_chrome_driver(headless=True, timeout=30)
            
            # Navigate to product page
            driver.get(product_url)
            time.sleep(2)
            
            # Step 1: Add to cart
            add_btn = wait_for_element(
                driver,
                '.add-to-cart-button, button[name="add"]',
                timeout=10,
                clickable=True
            )
            
            if not add_btn:
                return create_pricing_result(
                    error="Could not add to cart",
                    breakdown={"delivery_location": location_display}
                )
            
            safe_click(driver, add_btn)
            time.sleep(2)
            
            # Step 2: Navigate to checkout
            # Try to open cart
            cart_btn = wait_for_element(
                driver,
                '.cart-button, .cart-toggle, button[aria-label*="Cart"]',
                timeout=3,
                clickable=True
            )
            if cart_btn:
                safe_click(driver, cart_btn)
                time.sleep(1)
            
            # Click checkout
            checkout_btn = wait_for_element(
                driver,
                '.cart-checkout-button, button[aria-label*="Checkout"], .checkout-button',
                timeout=10,
                clickable=True
            )
            
            if not checkout_btn:
                return create_pricing_result(
                    error="Could not navigate to checkout",
                    breakdown={"delivery_location": location_display}
                )
            
            safe_click(driver, checkout_btn)
            time.sleep(5)
            
            # Get initial total
            initial_total = 0.0
            try:
                summary = driver.find_element(By.CSS_SELECTOR, '[class*="summary"], [class*="order-summary"], aside')
                summary_text = summary.text
                if 'total' in summary_text.lower() or '$' in summary_text:
                    initial_total = extract_price(summary_text)
            except:
                pass
            
            # Select country and shipping
            wait_for_element(driver, '[name="countryCode"], select', timeout=10)
            time.sleep(2)
            
            # ... rest of the checkout logic ...
            # (shortened for example - would include shipping selection, etc.)
            
            # Use helper to create standardized result
            return create_pricing_result(
                item_price=initial_total,
                shipping_fee=5.0,  # Example
                tax_amount=0.0,
                currency="USD",
                delivery_time="3 to 5 days",
                breakdown={
                    "delivery_location": location_display,
                    "note": "Refactored using utils"
                }
            )
            
        except Exception as e:
            print(f"Error in get_detailed_pricing: {e}")
            return create_pricing_result(
                error=str(e),
                breakdown={"delivery_location": location_display}
            )
        finally:
            if driver:
                driver.quit()
