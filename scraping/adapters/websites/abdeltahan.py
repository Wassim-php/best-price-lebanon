import re
from typing import List, Optional, Dict, Any
from urllib.parse import quote_plus, urljoin
import time

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

from ..base import BaseAdapter, OfferData

# Regex to match prices: 1234.56 or 1,234.56
_PRICE_RE = re.compile(r"(\d+(?:,\d{3})*(?:\.\d+)?)")

class AbedTahanAdapter(BaseAdapter):
    source_name = "abed_tahan"
    base_url = "https://abedtahan.com"

    def search(self, query: str, limit: int = 10, page: int = 1) -> List[OfferData]:
        # Abed Tahan Search URL structure
        search_url = f"{self.base_url}/search?q={quote_plus(query)}&options[prefix]=last"
        if page and page > 1:
            search_url += f"&page={page}"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        }

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
                url = urljoin(self.base_url, href)

                # 3. Extract Price
                # Check for sale price first, then regular price
                price_el = card.select_one(".price-item--sale")
                if not price_el:
                    price_el = card.select_one(".price-item--regular")
                
                if not price_el:
                    continue

                raw_price = price_el.get_text(strip=True).replace("USD", "").replace("$", "")
                m = _PRICE_RE.search(raw_price)
                if not m:
                    continue
                item_price = float(m.group(1).replace(',', ''))

                # 4. Extract Image
                img_el = card.select_one(".card__media img")
                image_url: Optional[str] = None
                if img_el:
                    # Abed Tahan images are often protocol-relative (//cdn.shopify...)
                    src = img_el.get("src") or img_el.get("srcset", "").split(" ")[0]
                    if src.startswith("//"):
                        image_url = "https:" + src
                    else:
                        image_url = src

                # 5. Extract Stock Status
                # Logic: If .sold-out-badge has 'hidden' class -> In Stock. Else -> Out of Stock.
                in_stock = True
                badge = card.select_one(".sold-out-badge")
                if badge:
                    classes = badge.get("class", [])
                    if "hidden" not in classes:
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
            print(f"Error searching Abed Tahan: {e}")
            return []

    def get_detailed_pricing(self, product_url: str, location: str = "outside beirut") -> Dict[str, Any]:
        """
        Scrapes detailed pricing for Shopify-based Abed Tahan.
        
        Args:
            product_url: Full URL to the product page
            location: Delivery location - "inside beirut" or "outside beirut" (default: "outside beirut")
        """
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--start-maximized')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        driver = None
        try:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            driver.set_page_load_timeout(45)
            
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
                try:
                    WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, '[class*="price"]'))
                    )
                except:
                    pass
                
                # Try multiple selectors for price in order of preference
                selectors = [
                    ('span.price-item--sale', 'Sale price'),
                    ('span.price-item--regular', 'Regular price'),
                    ('span.price__sale', 'Alternate sale'),
                    ('span.price__regular', 'Alternate regular'),
                    ('[class*="price"]:not([class*="compare"])', 'Generic price'),
                ]
                
                for selector, desc in selectors:
                    try:
                        elements = driver.find_elements(By.CSS_SELECTOR, selector)
                        for elem in elements:
                            if elem.is_displayed():
                                text = elem.text.strip()
                                if text and '$' in text:
                                    m = _PRICE_RE.search(text)
                                    if m:
                                        item_price = float(m.group(1).replace(',', ''))
                                        print(f"✓ Found {desc}: ${item_price}")
                                        break
                        if item_price > 0:
                            break
                    except:
                        pass
                
                if item_price == 0.0:
                    # Last resort: get all text with $ and find first valid price
                    page_text = driver.find_element(By.TAG_NAME, "body").text
                    matches = _PRICE_RE.findall(page_text)
                    if matches:
                        for match in matches:
                            price = float(match.replace(',', ''))
                            if 10 > price > 0:  # Reasonable price range
                                item_price = price
                                print(f"✓ Found price from page text: ${item_price}")
                                break
                
                if item_price == 0.0:
                    print("⚠ Could not extract product price")
                    
            except Exception as e:
                print(f"Error extracting price: {e}")

            # --- 2. Add to Cart ---
            try:
                # Try specific name="add" button
                add_btn = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.NAME, "add"))
                )
                driver.execute_script("arguments[0].click();", add_btn)
                time.sleep(2)
            except TimeoutException:
                return {
                    "item_price": item_price,
                    "shipping_fee": None,
                    "tax_amount": None,
                    "total_price": item_price,
                    "currency": "USD",
                    "breakdown": {"error": "Could not add to cart (OOS?)"}
                }

            # --- 3. Navigate to Checkout Page ---
            # Go directly to checkout where location options are available
            try:
                driver.get(f"{self.base_url}/checkout")
                time.sleep(5)
                print("Navigated to checkout page")
            except TimeoutException:
                print("Checkout page load timeout")
                return {
                    "item_price": item_price,
                    "shipping_fee": None,
                    "tax_amount": None,
                    "total_price": item_price,
                    "currency": "USD",
                    "breakdown": {"error": "Could not load checkout page"}
                }

            # --- 4. Select Delivery Location (Inside/Outside Beirut) ---
            shipping_fee = None
            delivery_time = None
            
            try:
                # Wait for radio buttons to be present on checkout page
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="radio"]'))
                )
                
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
                    page_text = driver.find_element(By.TAG_NAME, "body").text
                    
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
                                m = _PRICE_RE.search(elem_text)
                                if m and shipping_fee is None:
                                    shipping_fee = float(m.group(1).replace(',', ''))
                                    print(f"  → Shipping fee: ${shipping_fee}")
                                    break
                                
                                # Try parent element if no price in direct text
                                try:
                                    parent = elem.find_element(By.XPATH, "./ancestor::*[1]")
                                    parent_text = parent.text
                                    m = _PRICE_RE.search(parent_text)
                                    if m and shipping_fee is None:
                                        shipping_fee = float(m.group(1).replace(',', ''))
                                        print(f"  → Shipping fee (from parent): ${shipping_fee}")
                                        break
                                except:
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
                                    m = _PRICE_RE.search(elem_text)
                                    if m and shipping_fee is None:
                                        shipping_fee = float(m.group(1).replace(',', ''))
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
                            m = _PRICE_RE.search(elem_text)
                            if m:
                                potential_total = float(m.group(1).replace(',', ''))
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

            return {
                "item_price": item_price,
                "shipping_fee": shipping_fee,
                "tax_amount": tax_amount,
                "total_price": total_price,
                "currency": "USD",
                "breakdown": breakdown
            }

        except Exception as e:
            print(f"Error detailed scraping: {e}")
            return {
                "item_price": 0.0,
                "shipping_fee": None,
                "tax_amount": None,
                "total_price": 0.0,
                "currency": "USD",
                "breakdown": {"error": str(e)}
            }
        finally:
            if driver:
                driver.quit()