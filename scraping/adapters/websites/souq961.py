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


class Souq961Adapter(BaseAdapter):
    source_name = "961souq"
    base_url = "https://961souq.com"

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
            m = _PRICE_RE.search(raw_price)
            if not m:
                continue
            item_price = float(m.group(1).replace(',', ''))

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

    def get_detailed_pricing(self, product_url: str) -> Dict[str, Any]:
        """
        Scrape detailed pricing including shipping and taxes by simulating checkout.
        Uses address in Koura, Lebanon for shipping calculation.
        
        Args:
            product_url: Full URL to the product page
            
        Returns:
            Dictionary containing:
                - item_price: Base product price
                - shipping_fee: Shipping cost
                - tax_amount: Tax amount
                - total_price: Final total price
                - currency: Currency code
                - breakdown: Additional pricing details if available
        """
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # Run in background
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        driver = None
        try:
            # Initialize Chrome driver
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            driver.set_page_load_timeout(30)
            
            # Navigate to product page
            driver.get(product_url)
            time.sleep(2)
            
            # Extract base price from product page
            item_price = 0.0
            try:
                price_element = driver.find_element(By.CSS_SELECTOR, '.product-price')
                price_text = price_element.text.replace(',', '').replace('$', '').strip()
                m = _PRICE_RE.search(price_text)
                if m:
                    item_price = float(m.group(1).replace(',', ''))
            except NoSuchElementException:
                print("Could not find price on product page")
            
            # Add to cart using Shopify button
            try:
                add_to_cart_btn = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, '.add-to-cart-button, button[name="add"]'))
                )
                # Use JavaScript click to avoid interception issues
                driver.execute_script("arguments[0].click();", add_to_cart_btn)
                time.sleep(2)  # Wait for cart to update
            except TimeoutException:
                print("Could not find add to cart button")
                return {
                    "item_price": item_price,
                    "shipping_fee": None,
                    "tax_amount": None,
                    "total_price": item_price,
                    "currency": "USD",
                    "breakdown": {"error": "Could not add to cart"}
                }
            
            # Open cart overlay
            try:
                cart_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, '.cart-button, .cart-toggle, button[aria-label*="Cart"]'))
                )
                driver.execute_script("arguments[0].click();", cart_button)
                time.sleep(2)
            except TimeoutException:
                print("Could not open cart")
            
            # Click "Continue to Checkout" button
            try:
                checkout_btn = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, '.cart-checkout-button, button[aria-label*="Checkout"], .checkout-button'))
                )
                driver.execute_script("arguments[0].click();", checkout_btn)
                time.sleep(5)  # Wait for checkout page to load
            except TimeoutException:
                print("Could not click checkout button")
                return {
                    "item_price": item_price,
                    "shipping_fee": None,
                    "tax_amount": None,
                    "total_price": item_price,
                    "currency": "USD",
                    "breakdown": {"error": "Could not navigate to checkout"}
                }
            
            # Fill in shipping address for Koura, Lebanon
            try:
                # Wait for checkout form to load - look for email field
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.NAME, "email"))
                )
                
                # Fill email (has both id and name="email")
                try:
                    email_field = driver.find_element(By.NAME, "email")
                    email_field.clear()
                    email_field.send_keys("test@example.com")
                    time.sleep(1)
                except NoSuchElementException:
                    pass
                
                # Fill first name (name="firstName")
                try:
                    first_name = driver.find_element(By.NAME, "firstName")
                    first_name.clear()
                    first_name.send_keys("Test")
                except NoSuchElementException:
                    pass
                
                # Fill last name (name="lastName")
                try:
                    last_name = driver.find_element(By.NAME, "lastName")
                    last_name.clear()
                    last_name.send_keys("User")
                except NoSuchElementException:
                    pass
                
                # Fill address (name="address1")
                try:
                    address_field = driver.find_element(By.NAME, "address1")
                    address_field.clear()
                    address_field.send_keys("Main Street, Koura")
                except NoSuchElementException:
                    pass
                
                # Fill city (name="city")
                try:
                    city_field = driver.find_element(By.NAME, "city")
                    city_field.clear()
                    city_field.send_keys("Koura")
                except NoSuchElementException:
                    pass
                
                # Select country (name="countryCode") - should already be Lebanon by default
                try:
                    country_select = driver.find_element(By.NAME, "countryCode")
                    # Country is usually pre-selected as Lebanon, but ensure it
                    if country_select.get_attribute("value") != "LB":
                        country_select.send_keys("Lebanon")
                    time.sleep(1)
                except NoSuchElementException:
                    pass
                
                # Fill phone number (name="phone")
                try:
                    phone_field = driver.find_element(By.NAME, "phone")
                    phone_field.clear()
                    phone_field.send_keys("71123456")
                except NoSuchElementException:
                    pass
                
                # Trigger shipping calculation by clicking outside or tabbing
                try:
                    # Click on a neutral element to trigger validation
                    driver.execute_script("document.activeElement.blur();")
                except:
                    pass
                
                # Wait for shipping method options to appear
                time.sleep(3)
                
                # Look for shipping method radio buttons or options
                try:
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, '[name="delivery_strategies"], input[type="radio"][name*="shipping"], input[type="radio"][name*="delivery"]'))
                    )
                    
                    # Select a shipping method (first available option)
                    try:
                        shipping_radios = driver.find_elements(By.NAME, "delivery_strategies")
                        if not shipping_radios:
                            shipping_radios = driver.find_elements(By.CSS_SELECTOR, 'input[type="radio"][name*="shipping"], input[type="radio"][name*="delivery"]')
                        
                        if shipping_radios and len(shipping_radios) > 0:
                            # Click the first shipping option
                            try:
                                shipping_radios[0].click()
                            except:
                                # Fallback to JavaScript click
                                driver.execute_script("arguments[0].click();", shipping_radios[0])
                            time.sleep(3)  # Wait for price update after selection
                        else:
                            time.sleep(2)  # Additional wait for prices to populate
                    except Exception:
                        time.sleep(2)
                    
                except TimeoutException:
                    time.sleep(3)
                
            except TimeoutException:
                print("Checkout form not found")
            
            # Extract pricing details from checkout summary
            shipping_fee = 0.0
            tax_amount = 0.0
            total_price = item_price
            breakdown = {}
            
            try:
                # Get order summary for total
                try:
                    summary_section = driver.find_element(By.CSS_SELECTOR, '[class*="summary"], [class*="order-summary"], aside')
                    summary_text = summary_section.text
                    
                    # Extract total from summary
                    if 'total' in summary_text.lower():
                        lines = summary_text.split('\n')
                        for line in lines:
                            if '$' in line:
                                m = _PRICE_RE.search(line)
                                if m:
                                    potential_total = float(m.group(1).replace(',', ''))
                                    if potential_total >= item_price:
                                        total_price = potential_total
                                        break
                
                except NoSuchElementException:
                    pass
                
                # Try to find the selected shipping method
                try:
                    # Look for checked radio button
                    selected_shipping = driver.find_element(By.CSS_SELECTOR, 'input[name="delivery_strategies"]:checked')
                    # Navigate up to find the price in the container
                    parent_container = selected_shipping.find_element(By.XPATH, "./ancestor::*[contains(@class, 'field') or contains(@class, 'option')][1]")
                    container_text = parent_container.text
                    
                    # Extract price from container
                    m = _PRICE_RE.search(container_text)
                    if m:
                        shipping_fee = float(m.group(1).replace(',', ''))
                except:
                    # Alternative: Look for all shipping prices and use the first one with $ sign
                    try:
                        shipping_elements = driver.find_elements(By.XPATH, "//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'delivery') or contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'shipping')]")
                        for elem in shipping_elements:
                            elem_text = elem.text
                            if '$' in elem_text and ('beirut' in elem_text.lower() or 'delivery' in elem_text.lower()):
                                m = _PRICE_RE.search(elem_text)
                                if m:
                                    shipping_fee = float(m.group(1).replace(',', ''))
                                    break
                    except:
                        pass
                    
                    # Final fallback: Calculate from total - item_price if we have a total
                    if shipping_fee == 0.0 and total_price > item_price:
                        shipping_fee = round(total_price - item_price, 2)
                
                # If we couldn't get shipping from selected method, look for all shipping options
                # Shopify Oxygen checkout uses React and loads prices dynamically
                page_text = driver.find_element(By.TAG_NAME, "body").text.lower()
                
                # Check if shipping is mentioned
                if "free shipping" in page_text or "free delivery" in page_text:
                    shipping_fee = 0.0
                    breakdown["shipping_note"] = "Free shipping"
                elif "calculated at checkout" in page_text or "calculated at shipping" in page_text:
                    shipping_fee = None
                    breakdown["shipping_note"] = "Calculated at checkout"
                
                # Look for any price elements on the page
                try:
                    # Try to find subtotal in various possible locations
                    price_elements = driver.find_elements(By.CSS_SELECTOR, '[class*="price"], [class*="total"], [class*="subtotal"]')
                    for elem in price_elements:
                        if elem.is_displayed():
                            text = elem.text
                            if text and '$' in text:
                                m = _PRICE_RE.search(text)
                                if m:
                                    # Store first price found (likely subtotal)
                                    if item_price == 0.0:
                                        item_price = float(m.group(1).replace(',', ''))
                except:
                    pass
                
                # Look for shipping rate text patterns
                try:
                    all_text_elements = driver.find_elements(By.XPATH, "//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'shipping') or contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'delivery')]")
                    for elem in all_text_elements:
                        if elem.is_displayed():
                            text = elem.text
                            if 'free' in text.lower():
                                shipping_fee = 0.0
                            else:
                                # Look for price near shipping text
                                try:
                                    parent = elem.find_element(By.XPATH, "./ancestor::*[contains(@class, 'line') or contains(@class, 'row')][1]")
                                    m = _PRICE_RE.search(parent.text)
                                    if m and shipping_fee == 0.0:  # Only set first time
                                        shipping_fee = float(m.group(1).replace(',', ''))
                                except:
                                    pass
                except:
                    pass
                
                # Look for tax/VAT
                try:
                    tax_elements = driver.find_elements(By.XPATH, "//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'tax') or contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'vat')]")
                    for elem in tax_elements:
                        if elem.is_displayed():
                            try:
                                parent = elem.find_element(By.XPATH, "./ancestor::*[contains(@class, 'line') or contains(@class, 'row')][1]")
                                m = _PRICE_RE.search(parent.text)
                                if m and tax_amount == 0.0:  # Only set first time
                                    tax_amount = float(m.group(1).replace(',', ''))
                            except:
                                pass
                except:
                    pass
                
                # Look for total/estimated total
                try:
                    total_elements = driver.find_elements(By.XPATH, "//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'total') or contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'payment')]")
                    for elem in total_elements:
                        if elem.is_displayed() and 'subtotal' not in elem.text.lower():
                            try:
                                parent = elem.find_element(By.XPATH, "./ancestor::*[contains(@class, 'line') or contains(@class, 'row') or contains(@class, 'total')][1]")
                                prices = _PRICE_RE.findall(parent.text)
                                if prices:
                                    # Take the largest price as total
                                    potential_total = max([float(p.replace(',', '')) for p in prices])
                                    if potential_total >= item_price:
                                        total_price = potential_total
                                        break
                            except:
                                pass
                except:
                    pass
                
                # Calculate tax if we have total but no explicit tax amount
                # Tax = Total - Item Price - Shipping
                if total_price > item_price:
                    calculated_fees = total_price - item_price
                    
                    # If we have shipping, subtract it to get tax
                    if shipping_fee is not None and shipping_fee > 0:
                        if tax_amount == 0.0:
                            tax_amount = round(calculated_fees - shipping_fee, 2)
                    # If shipping is 0 or None, all the difference is tax
                    elif shipping_fee == 0.0 or shipping_fee is None:
                        if tax_amount == 0.0:
                            tax_amount = round(calculated_fees, 2)
                
                # If we didn't find a total but have components, calculate it
                if total_price == item_price and shipping_fee is not None:
                    total_price = item_price + (shipping_fee or 0) + tax_amount
                
                breakdown = {
                    "subtotal": item_price,
                    "shipping": shipping_fee if shipping_fee is not None else 0.0,
                    "tax": tax_amount,
                    "total": total_price,
                    "delivery_location": "Koura, Lebanon"
                }
                
            except Exception as e:
                print(f"Error extracting pricing details: {e}")
                breakdown["error"] = str(e)
            
            return {
                "item_price": item_price,
                "shipping_fee": shipping_fee if shipping_fee > 0 else None,
                "tax_amount": tax_amount if tax_amount > 0 else None,
                "total_price": total_price,
                "currency": "USD",
                "breakdown": breakdown
            }
            
        except Exception as e:
            print(f"Error in get_detailed_pricing: {e}")
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
