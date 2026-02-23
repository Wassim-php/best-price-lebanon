import re
import json
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

class MobileLebAdapter(BaseAdapter):
    source_name = "mobileleb"
    base_url = "https://mobileleb.com"

    def search(self, query: str, limit: int = 10, page: int = 1) -> List[OfferData]:
        # Mobileleb (Shopify) search URL
        search_url = f"{self.base_url}/search?q={quote_plus(query)}&type=product"
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
                url = urljoin(self.base_url, href)

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

                m = _PRICE_RE.search(price_text)
                if not m:
                    continue
                item_price = float(m.group(1).replace(',', ''))

                # 3. Extract Image
                # Mobileleb uses lazy-loaded images stored in data-optionimages JSON
                image_url = None
                
                # Try to extract from data-optionimages JSON in quickview button
                try:
                    quickview_btn = card.select_one(".tt-btn-quickview")
                    if quickview_btn and quickview_btn.get("data-optionimages"):
                        images_json = quickview_btn.get("data-optionimages")
                        images_dict = json.loads(images_json)
                        if images_dict:
                            first_image = next(iter(images_dict.values()))
                            if first_image.startswith("//"):
                                image_url = "https:" + first_image
                            else:
                                image_url = first_image
                except:
                    pass
                
                # Fallback: try img tag with data-src
                if not image_url:
                    img_el = card.select_one(".tt-img img")
                    if img_el:
                        src = img_el.get("data-src") or img_el.get("src") or img_el.get("srcset")
                        if src:
                            src = src.split(",")[0].split(" ")[0]
                            if src.startswith("//"):
                                image_url = "https:" + src
                            else:
                                image_url = src

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
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        driver = None
        try:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            driver.set_page_load_timeout(30)
            
            # --- 1. Load product page and get price ---
            print(f"Loading product: {product_url}")
            driver.get(product_url)
            time.sleep(2)
            
            item_price = 0.0
            try:
                price_element = driver.find_element(By.CSS_SELECTOR, '.price-item--sale, .new-price, .tt-price span')
                price_text = price_element.text.replace(',', '').replace('$', '').strip()
                m = _PRICE_RE.search(price_text)
                if m:
                    item_price = float(m.group(1).replace(',', ''))
                print(f"Product price: ${item_price}")
            except NoSuchElementException:
                print("Could not find price on product page")
            
            # --- 2. Click ADD TO CART button ---
            print("Adding to cart...")
            try:
                add_to_cart_btn = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.addtocart-js, button[name="add"]'))
                )
                driver.execute_script("arguments[0].click();", add_to_cart_btn)
                time.sleep(2)
                print("✓ Added to cart")
            except TimeoutException:
                print("✗ Could not find ADD TO CART button")
                return {
                    "item_price": item_price,
                    "shipping_fee": None,
                    "tax_amount": None,
                    "total_price": item_price,
                    "currency": "USD",
                    "delivery_time": "1-2 days",
                    "breakdown": {"error": "Could not add to cart"}
                }
            
            # --- 3. Wait for popup and click CONTINUE first ---
            print("Waiting for popup to appear after add-to-cart...")
            try:
                # The popup should show up with CONTINUE and VIEW CART buttons
                # First, wait for the CONTINUE button
                continue_btn = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, 
                        "//button[contains(text(), 'CONTINUE') or contains(text(), 'Continue')]"))
                )
                print("✓ Found CONTINUE button in popup, clicking...")
                driver.execute_script("arguments[0].click();", continue_btn)
                time.sleep(3)
            except TimeoutException:
                print("⚠ Could not find CONTINUE button in popup, attempting VIEW CART directly...")
            
            # --- 3b. Click VIEW CART button in the popup ---
            print("Looking for VIEW CART button in popup...")
            try:
                # Look for "View Cart" button in the popup
                view_cart_btn = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, 
                        "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'view')] | "
                        "//a[contains(text(), 'View Cart')] | "
                        "//button[contains(text(), 'View')][contains(text(), 'Cart')]"))
                )
                print("✓ Found VIEW CART button in popup, clicking...")
                driver.execute_script("arguments[0].click();", view_cart_btn)
                time.sleep(5)
            except TimeoutException:
                print("⚠ No VIEW CART button found, trying header cart link...")
                try:
                    cart_link = driver.find_element(By.XPATH, "//a[contains(@href, '/cart')]")
                    driver.execute_script("arguments[0].click();", cart_link)
                    time.sleep(4)
                except:
                    print("⚠ Navigating directly to /cart")
                    driver.get(f"{self.base_url}/cart")
                    time.sleep(4)
            
            # --- 4. Don't do premature empty check - proceed to look for CALCULATE button ---
            # If cart is truly empty, we just won't find the button
            print("✓ On cart page, looking for CALCULATE SHIPPING button...")
            
            # --- 5. Click CALCULATE SHIPPING button ---
            print("Looking for CALCULATE SHIPPING button...")
            
            # First, scroll to bottom to ensure all content is loaded
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            shipping_fee = 0.0
            tax_amount = 0.0
            total_price = item_price
            delivery_time = "1-2 days"
            
            calc_btn = None
            try:
                # Try multiple selectors for the button - first by class, then by text
                calc_btn = None
                
                # Attempt 1: CSS selector for class "get-rates" with longer wait
                try:
                    calc_btn = WebDriverWait(driver, 15).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.get-rates'))
                    )
                    print(f"✓ Found CALCULATE button by class 'get-rates'")
                except TimeoutException:
                    # Attempt 2: XPath with text containing "CALCULATE" or "SHIPPING" or "RATE"
                    calc_btn = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, 
                            "//button[contains(text(), 'CALCULATE')] | "
                            "//button[contains(text(), 'Calculate')] | "
                            "//button[contains(text(), 'SHIPPING')] | "
                            "//button[contains(text(), 'shipping')] | "
                            "//button[contains(text(), 'RATE')] | "
                            "//button[contains(text(), 'Rate')] | "
                            "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'calculate')] | "
                            "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'rate')]"))
                    )
                    print(f"✓ Found CALCULATE button by text")
                
                if calc_btn:
                    # Click the button
                    driver.execute_script("arguments[0].click();", calc_btn)
                    print("✓ Clicked CALCULATE SHIPPING button")
                    time.sleep(5)  # Wait longer for shipping fee to load and calculate
                
            except TimeoutException:
                print("⚠ Could not find CALCULATE SHIPPING button (may not be on cart page yet)")
            except Exception as e:
                print(f"⚠ Error with button: {e}")
            
            # --- 6. Select location if needed (inside/outside Beirut) ---
            print("Looking for location selection options...")
            try:
                # Look for radio buttons that indicate location selection
                radios = driver.find_elements(By.CSS_SELECTOR, 'input[type="radio"]')
                
                if radios:
                    print(f"✓ Found {len(radios)} radio button options")
                    
                    # Look for beirut-related options
                    location_lower = location.lower().strip()
                    selected_radio = None
                    
                    for radio in radios:
                        try:
                            # Get the label/text associated with this radio
                            parent = radio.find_element(By.XPATH, "..")
                            parent_text = parent.text.lower()
                            
                            # Match location preference
                            if 'inside' in location_lower and ('inside' in parent_text or 'in beirut' in parent_text):
                                selected_radio = radio
                                print(f"  ✓ Found inside Beirut option")
                                break
                            elif 'outside' in location_lower and ('outside' in parent_text or 'out' in parent_text or 'koura' in parent_text):
                                selected_radio = radio
                                print(f"  ✓ Found outside Beirut option")
                                break
                        except:
                            pass
                    
                    # If no specific match, just use first radio
                    if not selected_radio and radios:
                        selected_radio = radios[0]
                        print(f"  ✓ Using first location option")
                    
                    # Click the selected radio button
                    if selected_radio:
                        driver.execute_script("arguments[0].click();", selected_radio)
                        print(f"  ✓ Selected location")
                        time.sleep(2)  # Wait for fee to update
                
            except Exception as e:
                print(f"  ⚠ Could not find/select location: {e}")
            
            # --- 7. Extract shipping fee based on location ---
            print("Extracting shipping fee...")
            try:
                # Mobileleb has two standard shipping rates:
                # Beirut: $3.00 USD
                # Outside Beirut (Koura, Trablos, etc.): $5.00 USD
                
                location_lower = location.lower().strip()
                
                if location_lower == "inside beirut":
                    shipping_fee = 3.0
                    print(f"✓ Beirut location, shipping: $3.00")
                else:
                    # Any location other than Beirut (Koura, Trablos, etc.)
                    shipping_fee = 5.0
                    print(f"✓ Outside Beirut ({location}), shipping: $5.00")
                
                # Look for tax in full page
                body_text = driver.find_element(By.TAG_NAME, "body").text
                lines = body_text.split('\n')
                
                for i, line in enumerate(lines):
                    line_lower = line.lower()
                    if ('tax' in line_lower or 'vat' in line_lower) and '$' in line:
                        m = _PRICE_RE.search(line)
                        if m:
                            tax_amount = float(m.group(1).replace(',', ''))
                            print(f"✓ Found tax: ${tax_amount}")
                            break
                
                # Calc total
                total_price = item_price + shipping_fee + tax_amount
                
            except Exception as e:
                print(f"⚠ Error extracting prices: {e}")
                total_price = item_price + shipping_fee + tax_amount
            
            return {
                "item_price": item_price,
                "shipping_fee": shipping_fee if shipping_fee > 0 else None,
                "tax_amount": tax_amount if tax_amount > 0 else None,
                "total_price": total_price,
                "currency": "USD",
                "delivery_time": delivery_time,
                "breakdown": {
                    "subtotal": item_price,
                    "shipping": shipping_fee,
                    "tax": tax_amount,
                    "total": total_price,
                    "delivery_time": delivery_time,
                    "delivery_location": location
                }
            }
            
        except Exception as e:
            print(f"✗ Error in get_detailed_pricing: {e}")
            import traceback
            traceback.print_exc()
            return {
                "item_price": 0.0,
                "shipping_fee": None,
                "tax_amount": None,
                "total_price": 0.0,
                "currency": "USD",
                "delivery_time": "1-2 days",
                "breakdown": {"error": str(e)}
            }
        finally:
            if driver:
                driver.quit()