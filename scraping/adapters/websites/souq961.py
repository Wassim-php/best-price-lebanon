import re
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
    extract_all_prices,
    PRICE_REGEX as _PRICE_RE,
    get_default_headers,
    build_product_url,
    build_search_url,
    extract_delivery_location_display,
    create_pricing_result,
)


class Souq961Adapter(BaseAdapter):
    source_name = "961souq"
    base_url = "https://961souq.com"

    def search(self, query: str, limit: int = 10, page: int = 1) -> List[OfferData]:
        # Example: https://961souq.com/search?q=hp+victus&page=2
        search_url = build_search_url(self.base_url, query, page)

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

            raw_price = price_el.get_text(" ", strip=True)
            item_price = extract_price(raw_price)
            if item_price == 0.0:
                continue

            url = build_product_url(href, self.base_url)

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
        Scrape detailed pricing including shipping and taxes by simulating checkout.
        
        Args:
            product_url: Full URL to the product page
            location: Delivery location - "inside beirut" or "outside beirut" (default: "outside beirut")
        
        Returns:
            Dictionary containing pricing details
        """
        # Format location for display
        location_display = extract_delivery_location_display(location)
        
        driver = None
        try:
            driver = create_chrome_driver(headless=True, timeout=30)
            
            # Navigate to product page
            driver.get(product_url)
            time.sleep(2)
            
            # Step 1: Add to cart
            try:
                add_to_cart_btn = wait_for_element(
                    driver,
                    '.add-to-cart-button, button[name="add"]',
                    timeout=10,
                    clickable=True
                )
                if not add_to_cart_btn:
                    return create_pricing_result(
                        error="Could not add to cart",
                        breakdown={"delivery_location": location_display}
                    )
                safe_click(driver, add_to_cart_btn)
                time.sleep(2)
            except TimeoutException:
                return create_pricing_result(
                    error="Could not add to cart",
                    breakdown={"delivery_location": location_display}
                )
            
            # Step 2: Proceed to checkout
            try:
                # Open cart if needed
                cart_button = wait_for_element(
                    driver,
                    '.cart-button, .cart-toggle, button[aria-label*="Cart"]',
                    timeout=3,
                    clickable=True
                )
                if cart_button:
                    safe_click(driver, cart_button)
                    time.sleep(1)
                
                # Click checkout button
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
            except TimeoutException:
                return create_pricing_result(
                    error="Could not navigate to checkout",
                    breakdown={"delivery_location": location_display}
                )
            
            # Get initial total (item price before shipping)
            initial_total = 0.0
            try:
                summary = driver.find_element(By.CSS_SELECTOR, '[class*="summary"], [class*="order-summary"], aside')
                summary_text = summary.text
                if 'total' in summary_text.lower() or '$' in summary_text:
                    initial_total = extract_price(summary_text)
            except:
                pass
            
            # Select country (Lebanon) to trigger shipping calculation
            try:
                # Wait for checkout page to load
                wait_for_element(driver, '[name="countryCode"], select', timeout=10)
                time.sleep(2)
                
                # Select Lebanon from country dropdown
                try:
                    country_select = driver.find_element(By.NAME, "countryCode")
                    # Select first option (Lebanon)
                    driver.execute_script("""
                        var select = arguments[0];
                        if (select.selectedIndex !== 0) {
                            select.selectedIndex = 0;
                            select.dispatchEvent(new Event('change', { bubbles: true }));
                        }
                    """, country_select)
                    time.sleep(3)  # Wait for shipping options to load
                except Exception as e:
                    pass
                
                # Select shipping method and extract its price
                selected_shipping_price = 0.0
                delivery_time = None
                try:
                    # First, make sure "Ship" method is selected (not "Pick up")
                    try:
                        # Look for the shipping method section and click "Ship" option
                        ship_radio = wait_for_element(
                            driver,
                            'input[type="radio"][value="ship_to_address"]',
                            timeout=5
                        )
                        if ship_radio:
                            safe_click(driver, ship_radio)
                            time.sleep(3)  # Wait for shipping options to appear
                    except TimeoutException:
                        pass
                    
                    # Now wait for the "Shipping method" section with actual shipping options
                    time.sleep(2)
                    
                    # Find all radio buttons on the page
                    all_radios = driver.find_elements(By.CSS_SELECTOR, 'input[type="radio"]')
                    
                    # Filter to find shipping method radios
                    shipping_method_radios = []
                    inside_beirut_radios = []
                    outside_beirut_radios = []
                    
                    for radio in all_radios:
                        try:
                            # Check if this radio button has a price associated with it
                            parent = radio.find_element(By.XPATH, "../..")
                            parent_text = parent.text
                            # Look for shipping-specific keywords to avoid payment methods
                            if '$' in parent_text and ('beirut' in parent_text.lower() or 'kg' in parent_text.lower()) and 'payment' not in parent_text.lower() and 'card' not in parent_text.lower():
                                shipping_method_radios.append(radio)
                                # Categorize by location
                                if 'inside beirut' in parent_text.lower():
                                    inside_beirut_radios.append(radio)
                                elif 'outside beirut' in parent_text.lower():
                                    outside_beirut_radios.append(radio)
                        except:
                            continue
                    
                    # Select shipping based on location parameter
                    selected_radio = None
                    location_lower = location.lower().strip()
                    
                    if 'inside' in location_lower and inside_beirut_radios:
                        selected_radio = inside_beirut_radios[0]
                    elif 'outside' in location_lower and outside_beirut_radios:
                        selected_radio = outside_beirut_radios[0]
                    elif shipping_method_radios:
                        # Fallback to first available option
                        selected_radio = shipping_method_radios[0]
                    
                    if selected_radio:
                        # Extract price and delivery time from selected option
                        try:
                            parent = selected_radio.find_element(By.XPATH, "../..")
                            shipping_text = parent.text
                            
                            # Extract shipping price
                            prices = extract_all_prices(shipping_text)
                            if prices:
                                selected_shipping_price = prices[-1]
                            
                            # Extract delivery time
                            shipping_lower = shipping_text.lower()
                            
                            # If shipping is free, set delivery time to 3 to 5 days
                            if selected_shipping_price == 0.0 or 'free' in shipping_lower:
                                delivery_time = "3 to 5 days"
                            elif 'same day' in shipping_lower:
                                delivery_time = "Same day"
                            elif '3 to 5 days' in shipping_lower or '3-5 days' in shipping_lower:
                                delivery_time = "3 to 5 days"
                            elif '1 to 2 days' in shipping_lower or '1-2 days' in shipping_lower:
                                delivery_time = "1 to 2 days"
                            elif 'next day' in shipping_lower:
                                delivery_time = "Next day"
                            else:
                                # Try to extract any pattern like "X to Y days" or "X days"
                                import re
                                time_match = re.search(r'(\d+\s*(?:to|-)\s*\d+\s*days?|\d+\s*days?|same\s*day|next\s*day)', shipping_lower)
                                if time_match:
                                    delivery_time = time_match.group(1).capitalize()
                        except Exception as e:
                            pass
                        
                        # Click the selected shipping option
                        driver.execute_script("arguments[0].click();", selected_radio)
                        time.sleep(3)  # Wait for prices to update
                        
                except Exception as e:
                    pass
                
            except TimeoutException:
                print("Could not load checkout form")
            
            # Step 3: Extract pricing from order summary
            item_price = initial_total  # Item price is the initial total before shipping
            shipping_fee = selected_shipping_price  # Shipping from selected option
            tax_amount = 0.0
            total_price = 0.0
            
            try:
                # Wait for prices to update after shipping selection
                time.sleep(2)
                
                # Get updated order summary
                summary = driver.find_element(By.CSS_SELECTOR, '[class*="summary"], [class*="order-summary"], aside')
                summary_text = summary.text
                
                # Parse the summary text for updated total
                lines = summary_text.split('\n')
                for i, line in enumerate(lines):
                    line_lower = line.lower()
                    
                    # Look for subtotal/item price (if shown separately)
                    if 'subtotal' in line_lower:
                        # Check current line and next line for price
                        if '$' in line:
                            found_price = extract_price(line)
                            if found_price > 0:
                                item_price = found_price
                        elif i + 1 < len(lines) and '$' in lines[i + 1]:
                            found_price = extract_price(lines[i + 1])
                            if found_price > 0:
                                item_price = found_price
                    
                    # Look for shipping (if shown separately)
                    elif 'shipping' in line_lower or 'delivery' in line_lower:
                        if 'free' not in line_lower:
                            if '$' in line:
                                found_shipping = extract_price(line)
                                if found_shipping > 0:
                                    shipping_fee = found_shipping
                            elif i + 1 < len(lines) and '$' in lines[i + 1]:
                                found_shipping = extract_price(lines[i + 1])
                                if found_shipping > 0:
                                    shipping_fee = found_shipping
                        else:
                            # Free shipping detected
                            shipping_fee = 0.0
                            delivery_time = "3 to 5 days"
                    
                    # Look for tax
                    elif 'tax' in line_lower or 'vat' in line_lower:
                        if '$' in line:
                            tax_amount = extract_price(line)
                        elif i + 1 < len(lines) and '$' in lines[i + 1]:
                            tax_amount = extract_price(lines[i + 1])
                    
                    # Look for final total
                    elif 'total' in line_lower and 'subtotal' not in line_lower:
                        if '$' in line:
                            total_price = extract_price(line)
                        elif i + 1 < len(lines) and '$' in lines[i + 1]:
                            total_price = extract_price(lines[i + 1])
                
                # Calculate final values
                if total_price == 0.0:
                    # If no total found in summary, calculate it
                    total_price = item_price + shipping_fee + tax_amount
                elif item_price > 0 and tax_amount == 0.0 and total_price > item_price:
                    # Calculate tax from the difference
                    remaining = total_price - item_price - shipping_fee
                    if remaining > 0:
                        tax_amount = remaining
                
                # If shipping is free and delivery time not set, default to 3-5 days
                if shipping_fee == 0.0 and delivery_time is None:
                    delivery_time = "3 to 5 days"
                
            except Exception as e:
                print(f"Error extracting pricing: {e}")
                return {
                    "item_price": 0.0,
                    "shipping_fee": None,
                    "tax_amount": None,
                    "total_price": 0.0,
                    "currency": "USD",
                    "delivery_time": None,
                    "breakdown": {"error": str(e), "delivery_location": location_display}
                }
            
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
                    "delivery_location": location_display
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
