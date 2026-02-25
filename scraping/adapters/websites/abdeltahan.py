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
    find_element_with_fallbacks,
    get_page_text,
    extract_price,
    PRICE_REGEX as _PRICE_RE,
    get_default_headers,
    normalize_image_url,
    build_product_url,
    build_search_url,
    extract_stock_status,
    create_pricing_result,
)

class AbedTahanAdapter(BaseAdapter):
    source_name = "abed_tahan"
    base_url = "https://abedtahan.com"

    def search(self, query: str, limit: int = 10, page: int = 1) -> List[OfferData]:
        # Abed Tahan Search URL structure
        search_url = build_search_url(
            self.base_url,
            query,
            page,
            extra_params="options[prefix]=last"
        )

        headers = get_default_headers()

        try:
            r = requests.get(search_url, headers=headers, timeout=25)
            r.raise_for_status()

            soup = BeautifulSoup(r.text, "lxml")
            offers: List[OfferData] = []
            
            # Abed Tahan uses 'li.grid__item' for products
            cards = soup.select("li.grid__item")

            for card in cards:
                # 1. Extract Title
                title_el = card.select_one("h3.card__heading a")
                if not title_el:
                    continue
                title = title_el.get_text(" ", strip=True)

                # 2. Extract Link (Relative URL)
                href = title_el.get("href")
                url = build_product_url(href, self.base_url)

                # 3. Extract Price
                # Check for sale price first, then regular price
                price_el = card.select_one(".price-item--sale")
                if not price_el:
                    price_el = card.select_one(".price-item--regular")
                
                if not price_el:
                    continue

                raw_price = price_el.get_text(strip=True)
                item_price = extract_price(raw_price)
                if item_price == 0.0:
                    continue

                # 4. Extract Image
                img_el = card.select_one(".card__media img")
                image_url: Optional[str] = None
                if img_el:
                    # Abed Tahan images are often protocol-relative (//cdn.shopify...)
                    src = img_el.get("src") or img_el.get("srcset", "").split(" ")[0]
                    image_url = normalize_image_url(src)

                # 5. Extract Stock Status
                in_stock = extract_stock_status(
                    card,
                    out_of_stock_selectors=[".sold-out-badge"]
                )

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
            print(f"Error searching Abed Tahan: {e}")
            return []

    def get_detailed_pricing(self, product_url: str, location: str = "outside beirut") -> Dict[str, Any]:
        """
        Scrapes detailed pricing for Shopify-based Abed Tahan.
        
        Args:
            product_url: Full URL to the product page
            location: Delivery location - "inside beirut" or "outside beirut" (default: "outside beirut")
        """
        driver = None
        try:
            driver = create_chrome_driver(headless=True, timeout=45)
            
            try:
                print(f"Loading product page: {product_url}")
                driver.get(product_url)
                print("✓ Product page loaded successfully")
            except TimeoutException:
                print("⚠ Timeout loading product page (continuing anyway)")
            
            time.sleep(2)
            
            # --- 1. Get Base Price ---
            item_price = 0.0
            try:
                print("Extracting base product price...")
                
                # Wait for price to be visible
                wait_for_element(driver, '[class*="price"]', timeout=5)
                
                # Try multiple selectors for price in order of preference
                selectors = [
                    'span.price-item--sale',
                    'span.price-item--regular',
                    'span.price__sale',
                    'span.price__regular',
                    '[class*="price"]:not([class*="compare"])',
                ]
                
                price_elem = find_element_with_fallbacks(driver, selectors)
                if price_elem:
                    item_price = extract_price(price_elem.text)
                    print(f"✓ Found price: ${item_price}")
                
                if item_price == 0.0:
                    # Last resort: get all text with $ and find first valid price
                    page_text = get_page_text(driver)
                    item_price = extract_price(page_text)
                    if item_price > 0:
                        print(f"✓ Found price from page text: ${item_price}")
                
                if item_price == 0.0:
                    print("⚠ Could not extract product price")
                    
            except Exception as e:
                print(f"Error extracting price: {e}")

            # --- 2. Add to Cart ---
            try:
                # Try specific name="add" button
                add_btn = wait_for_element(driver, '[name="add"]', timeout=5, clickable=True)
                if not add_btn:
                    return create_pricing_result(
                        item_price=item_price,
                        error="Could not add to cart (OOS?)"
                    )
                safe_click(driver, add_btn)
                time.sleep(2)
            except TimeoutException:
                return create_pricing_result(
                    item_price=item_price,
                    error="Could not add to cart (OOS?)"
                )

            # --- 3. Navigate to Checkout Page ---
            # Go directly to checkout where location options are available
            try:
                driver.get(f"{self.base_url}/checkout")
                time.sleep(5)
                print("Navigated to checkout page")
            except TimeoutException:
                print("Checkout page load timeout")
                return create_pricing_result(
                    item_price=item_price,
                    error="Could not load checkout page"
                )

            # --- 4. Select Delivery Location (Inside/Outside Beirut) ---
            shipping_fee = None
            delivery_time = None
            
            try:
                # Wait for radio buttons to be present on checkout page
                wait_for_element(driver, 'input[type="radio"]', timeout=10)
                
                # Find all radio buttons on checkout page
                radio_buttons = driver.find_elements(By.CSS_SELECTOR, 'input[type="radio"]')
                print(f"Found {len(radio_buttons)} radio buttons on checkout page")
                
                outside_beirut_selected = False
                
                # Try to find and select "Outside Beirut" option
                for i, radio in enumerate(radio_buttons):
                    try:
                        # Get the label text associated with this radio
                        radio_id = radio.get_attribute('id')
                        label_text = ""
                        
                        if radio_id:
                            try:
                                label = driver.find_element(By.CSS_SELECTOR, f'label[for="{radio_id}"]')
                                label_text = label.text.lower()
                            except:
                                pass
                        
                        # Also check all text near the radio element (up to 5 parents)
                        parent_text = ""
                        try:
                            for level in range(1, 6):
                                try:
                                    parent = radio.find_element(By.XPATH, f"./ancestor::*[{level}]")
                                    parent_text = parent.text.lower()
                                    if parent_text:
                                        break
                                except:
                                    pass
                        except:
                            pass
                        
                        full_text = (label_text + " " + parent_text).lower()
                        print(f"  Radio {i+1}: {full_text[:80]}")
                        
                        # Check if this is the "Outside Beirut" option
                        if "outside" in full_text or "out" in full_text or "rest" in full_text:
                            print(f"  → Selecting 'Outside Beirut' option")
                            radio.click()
                            outside_beirut_selected = True
                            delivery_time = "5-7 business days"
                            time.sleep(3)  # Wait for shipping fee to update
                            break
                    except Exception as e:
                        print(f"  Error checking radio {i+1}: {str(e)[:50]}")
                        pass
                
                # If "Outside Beirut" not found by text, select the second option (usually outside Beirut)
                if not outside_beirut_selected and len(radio_buttons) >= 2:
                    print(f"  → Couldn't find 'Outside Beirut' by text, selecting second option")
                    radio_buttons[1].click()
                    delivery_time = "5-7 business days"
                    time.sleep(3)
                    outside_beirut_selected = True
                
                if outside_beirut_selected:
                    print("✓ Selected: Outside Beirut")
                else:
                    print("⚠ Warning: Could not find delivery location options")
                    delivery_time = "5-7 business days"
                
            except TimeoutException:
                print("Timeout waiting for delivery location radio buttons")
            except Exception as e:
                print(f"Error selecting delivery location: {e}")

            # --- 5. Extract Shipping Fee and Totals ---
            tax_amount = None  # No tax in Lebanon
            total_price = item_price
            breakdown = {}

            try:
                # Wait a moment for prices to update after location selection
                time.sleep(3)
                
                # Extract shipping fee from checkout page
                print("Looking for shipping fee on checkout page...")
                
                try:
                    # Get all text on page to look for shipping-related elements
                    page_text = get_page_text(driver)
                    
                    # Look for visible elements containing "shipping" or "delivery" with a price
                    shipping_elements = driver.find_elements(By.XPATH, "//*[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'shipping') or contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'delivery')]")
                    
                    for elem in shipping_elements:
                        if elem.is_displayed():
                            elem_text = elem.text
                            print(f"  Found shipping element: {elem_text[:100]}")
                            
                            if "free" in elem_text.lower():
                                shipping_fee = 0.0
                                print("  → Free shipping")
                                break
                            else:
                                # Try to extract price from this element or its parent
                                found_fee = extract_price(elem_text)
                                if found_fee > 0 and shipping_fee is None:
                                    shipping_fee = found_fee
                                    print(f"  → Shipping fee: ${shipping_fee}")
                                    break
                                
                                # Try parent element if no price in direct text
                                try:
                                    parent = elem.find_element(By.XPATH, "./ancestor::*[1]")
                                    parent_text = parent.text
                                    found_fee = extract_price(parent_text)
                                    if found_fee > 0 and shipping_fee is None:
                                        shipping_fee = found_fee
                                        print(f"  → Shipping fee (from parent): ${shipping_fee}")
                                        break
                                except:
                                    pass
                                    pass
                except Exception as e:
                    print(f"  Error searching for shipping: {e}")
                
                # If still not found, look specifically for price elements near shipping text
                if shipping_fee is None:
                    print("  Trying alternative search for shipping fee...")
                    try:
                        # Find all elements with prices
                        price_elements = driver.find_elements(By.XPATH, "//*[contains(., '$') or contains(., 'USD')]")
                        for elem in price_elements:
                            if elem.is_displayed():
                                elem_text = elem.text
                                # Check if this price is near shipping text
                                if any(word in elem_text.lower() for word in ['shipping', 'delivery', 'fee']):
                                    found_fee = extract_price(elem_text)
                                    if found_fee > 0 and shipping_fee is None:
                                        shipping_fee = found_fee
                                        print(f"  → Found shipping fee: ${shipping_fee}")
                                        break
                    except Exception as e:
                        print(f"  Alternative search error: {e}")
                
                # Extract total price from checkout
                print("Looking for total price on checkout page...")
                try:
                    # Look for "Total" or "Order Total" text with price
                    total_elements = driver.find_elements(By.XPATH, "//*[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'total')]")
                    
                    for elem in total_elements:
                        if elem.is_displayed() and "subtotal" not in elem.text.lower():
                            elem_text = elem.text
                            potential_total = extract_price(elem_text)
                            if potential_total >= item_price:
                                total_price = potential_total
                                print(f"  → Total price: ${total_price}")
                                break
                except Exception as e:
                    print(f"  Error extracting total: {e}")
                
                # Calculate total if not explicitly found
                if total_price == item_price and shipping_fee is not None:
                    total_price = item_price + shipping_fee
                    print(f"  → Calculated total: ${total_price}")

                breakdown = {
                    "subtotal": item_price,
                    "shipping": shipping_fee,
                    "tax": tax_amount,
                    "total": total_price,
                    "delivery_location": "Koura, Lebanon (Outside Beirut)",
                    "delivery_time": delivery_time
                }

            except Exception as e:
                print(f"Error extracting pricing: {e}")
                breakdown["error"] = str(e)

            return create_pricing_result(
                item_price=item_price,
                shipping_fee=shipping_fee,
                tax_amount=tax_amount,
                total_price=total_price,
                currency="USD",
                breakdown=breakdown
            )

        except Exception as e:
            print(f"Error detailed scraping: {e}")
            return create_pricing_result(
                error=str(e)
            )
        finally:
            if driver:
                driver.quit()