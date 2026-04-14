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
        Scrape detailed pricing including shipping and taxes by simulating checkout.
        
        Args:
            product_url: Full URL to the product page
            location: Delivery location - "inside beirut" or "outside beirut" (default: "outside beirut")
            
        Returns:
            Dictionary containing:
                - item_price: Base product price
                - shipping_fee: Shipping cost
                - tax_amount: Tax amount
                - total_price: Final total price
                - currency: Currency code
                - delivery_time: Estimated delivery time
                - breakdown: Additional pricing details if available
        """
        # Format location for display
        location_lower = location.lower().strip()
        if 'inside' in location_lower:
            location_display = "Beirut (inside Beirut)"
        elif 'outside' in location_lower:
            location_display = "Koura (outside Beirut)"
        else:
            location_display = location.title()
        
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        driver = None
        try:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            driver.set_page_load_timeout(30)
            
            # Navigate to product page
            driver.get(product_url)
            time.sleep(2)
            
            # Step 1: Add to cart
            try:
                add_to_cart_btn = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, '.add-to-cart-button, button[name="add"]'))
                )
                driver.execute_script("arguments[0].click();", add_to_cart_btn)
                time.sleep(2)
            except TimeoutException:
                return {
                    "item_price": 0.0,
                    "shipping_fee": None,
                    "tax_amount": None,
                    "total_price": 0.0,
                    "currency": "USD",
                    "delivery_time": None,
                    "breakdown": {"error": "Could not add to cart", "delivery_location": location_display}
                }
            
            # Step 2: Proceed to checkout
            try:
                # Open cart if needed
                try:
                    cart_button = WebDriverWait(driver, 3).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, '.cart-button, .cart-toggle, button[aria-label*="Cart"]'))
                    )
                    driver.execute_script("arguments[0].click();", cart_button)
                    time.sleep(1)
                except TimeoutException:
                    pass
                
                # Click checkout button
                checkout_btn = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, '.cart-checkout-button, button[aria-label*="Checkout"], .checkout-button'))
                )
                driver.execute_script("arguments[0].click();", checkout_btn)
                time.sleep(5)
            except TimeoutException:
                return {
                    "item_price": 0.0,
                    "shipping_fee": None,
                    "tax_amount": None,
                    "total_price": 0.0,
                    "currency": "USD",
                    "delivery_time": None,
                    "breakdown": {"error": "Could not navigate to checkout", "delivery_location": location_display}
                }
            
            # Get initial total (item price before shipping)
            initial_total = 0.0
            try:
                summary = driver.find_element(By.CSS_SELECTOR, '[class*="summary"], [class*="order-summary"], aside')
                summary_text = summary.text
                if 'total' in summary_text.lower() or '$' in summary_text:
                    parsed_total = _extract_last_price(summary_text)
                    if parsed_total is not None:
                        initial_total = parsed_total
            except:
                pass
            
            # Select country (Lebanon) to trigger shipping calculation
            try:
                # Wait for checkout page to load
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '[name="countryCode"], select'))
                )
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
                        ship_radio = WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="radio"][value="ship_to_address"]'))
                        )
                        driver.execute_script("arguments[0].click();", ship_radio)
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
                            extracted_shipping = _extract_last_price(shipping_text)
                            if extracted_shipping is not None:
                                selected_shipping_price = extracted_shipping
                            
                            # Extract delivery time
                            shipping_lower = shipping_text.lower()
                            
                            # If shipping is free, set delivery time to 3 to 5 days
                            if selected_shipping_price == 0.0 or 'free' in shipping_lower:
                                delivery_time = "3-5 business days"
                            elif 'same day' in shipping_lower:
                                delivery_time = "1-1 business days"
                            elif '3 to 5 days' in shipping_lower or '3-5 days' in shipping_lower:
                                delivery_time = "3-5 business days"
                            elif '1 to 2 days' in shipping_lower or '1-2 days' in shipping_lower:
                                delivery_time = "1-2 business days"
                            elif 'next day' in shipping_lower:
                                delivery_time = "1-2 business days"
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
                            parsed_subtotal = _extract_last_price(line)
                            if parsed_subtotal is not None:
                                item_price = parsed_subtotal
                        elif i + 1 < len(lines) and '$' in lines[i + 1]:
                            parsed_subtotal = _extract_last_price(lines[i + 1])
                            if parsed_subtotal is not None:
                                item_price = parsed_subtotal
                    
                    # Look for shipping (if shown separately)
                    elif 'shipping' in line_lower or 'delivery' in line_lower:
                        if 'free' not in line_lower:
                            if '$' in line:
                                found_shipping = _extract_last_price(line)
                                if found_shipping and found_shipping > 0:
                                    shipping_fee = found_shipping
                            elif i + 1 < len(lines) and '$' in lines[i + 1]:
                                found_shipping = _extract_last_price(lines[i + 1])
                                if found_shipping and found_shipping > 0:
                                    shipping_fee = found_shipping
                        else:
                            # Free shipping detected
                            shipping_fee = 0.0
                            delivery_time = "3-5 business days"
                    
                    # Look for tax
                    elif 'tax' in line_lower or 'vat' in line_lower:
                        if '$' in line:
                            parsed_tax = _extract_last_price(line)
                            if parsed_tax is not None:
                                tax_amount = parsed_tax
                        elif i + 1 < len(lines) and '$' in lines[i + 1]:
                            parsed_tax = _extract_last_price(lines[i + 1])
                            if parsed_tax is not None:
                                tax_amount = parsed_tax
                    
                    # Look for final total
                    elif 'total' in line_lower and 'subtotal' not in line_lower:
                        if '$' in line:
                            parsed_total = _extract_last_price(line)
                            if parsed_total is not None:
                                total_price = parsed_total
                        elif i + 1 < len(lines) and '$' in lines[i + 1]:
                            parsed_total = _extract_last_price(lines[i + 1])
                            if parsed_total is not None:
                                total_price = parsed_total
                
                # Calculate final values
                if total_price == 0.0:
                    # If no total found in summary, calculate it
                    total_price = item_price + shipping_fee + tax_amount
                elif item_price > 0 and tax_amount == 0.0 and total_price > item_price:
                    # Calculate tax from the difference
                    remaining = total_price - item_price - shipping_fee
                    if remaining > 0:
                        tax_amount = remaining

                # Normalize numeric outputs and make sure total includes shipping/tax.
                item_price = round(float(item_price or 0.0), 2)
                shipping_fee = round(float(shipping_fee or 0.0), 2)
                tax_amount = round(float(tax_amount or 0.0), 2)
                total_price = round(float(total_price or 0.0), 2)

                computed_total = round(item_price + shipping_fee + tax_amount, 2)
                if total_price <= 0.0 or computed_total > total_price:
                    total_price = computed_total
                
                # If shipping is free and delivery time not set, default to 3-5 days
                if shipping_fee == 0.0 and delivery_time is None:
                    delivery_time = "3-5 business days"
                
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
            
            return {
                "item_price": item_price,
                "shipping_fee": shipping_fee,
                "tax_amount": tax_amount,
                "total_price": total_price,
                "currency": "USD",
                "delivery_time": delivery_time,
                "breakdown": {
                    "subtotal": item_price,
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
        finally:
            if driver:
                driver.quit()
