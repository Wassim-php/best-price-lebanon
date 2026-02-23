import re
from typing import Optional
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

_PRICE_RE = re.compile(r"(\d+(?:,\d{3})*(?:\.\d+)?)")

def inspect_cart_persistence():
    """Try multiple approaches to access cart with items."""
    
    base_url = "https://mobileleb.com"
    search_query = "laptop"
    
    print("=" * 80)
    print("MOBILELEB - CART PERSISTENCE TEST")
    print("=" * 80)
    
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
        
        # --- 1. Search for a product ---
        print("\n1. Searching for products...")
        search_url = f"{base_url}/search?q={search_query}&type=product"
        driver.get(search_url)
        time.sleep(3)
        
        # Get first product link
        try:
            first_product = driver.find_element(By.CSS_SELECTOR, 'a[href*="/products/"]')
            product_url = first_product.get_attribute("href")
            print(f"✓ Found product: {product_url.split('/')[-1][:50]}")
        except:
            print("✗ Could not find product")
            return
        
        # --- 2. Load product page and add to cart ---
        print("\n2. Loading product page...")
        driver.get(product_url)
        time.sleep(3)
        
        body_text = driver.find_element(By.TAG_NAME, "body").text
        price_match = _PRICE_RE.search(body_text)
        price_str = price_match.group(1) if price_match else "N/A"
        print(f"✓ Product page loaded - Price: ${price_str}")
        
        # --- 3. Add to cart ---
        print("\n3. Adding to cart...")
        try:
            add_btn = driver.find_element(By.CSS_SELECTOR, 'button.addtocart-js')
            driver.execute_script("arguments[0].click();", add_btn)
            time.sleep(2)
            print("✓ Clicked ADD TO CART")
        except Exception as e:
            print(f"✗ Could not add to cart: {e}")
            return
        
        # --- 4. Wait and check for confirmation ---
        print("\n4. Waiting for add-to-cart confirmation...")
        time.sleep(3)
        
        body_text = driver.find_element(By.TAG_NAME, "body").text
        if "added" in body_text.lower() or "cart" in body_text.lower():
            print("✓ Detected add-to-cart message")
        
        # --- 5. Approach A: Navigate to /cart URL ---
        print("\n5. APPROACH A: Direct navigation to /cart")
        driver.get(f"{base_url}/cart")
        time.sleep(5)
        
        body_text = driver.find_element(By.TAG_NAME, "body").text
        if "empty" in body_text.lower():
            print("   ✗ Cart is empty via direct URL")
        else:
            print("   ✓ Cart has content")
            # Try to find CALCULATE button
            try:
                calc_btn = driver.find_element(By.CSS_SELECTOR, 'button.get-rates')
                print("   ✓ Found CALCULATE SHIPPING button")
            except:
                print("   ✗ No CALCULATE SHIPPING button")
        
        # --- 6. Go back to product and try again via the page ---
        print("\n6. APPROACH B: Stay on product page and access cart from header")
        driver.get(product_url)
        time.sleep(2)
        
        # Add to cart again
        try:
            add_btn = driver.find_element(By.CSS_SELECTOR, 'button.addtocart-js')
            driver.execute_script("arguments[0].click();", add_btn)
            time.sleep(2)
            print("✓ Item added to cart again")
        except:
            print("✗ Could not add to cart")
            return
        
        # Look for cart counter in header that shows new item
        print("   Looking for cart counter/icon in header...")
        
        # Find all elements with cart in class or aria-label
        cart_elements = driver.find_elements(By.XPATH, "//*[contains(@class, 'cart') or contains(@aria-label, 'Cart')]")
        print(f"   Found {len(cart_elements)} cart-related elements in header")
        
        # Try to find and click the actual cart link/icon
        try:
            # Look for the main cart icon in header
            cart_icon = driver.find_element(By.XPATH, "//a[contains(@href, '/cart')] | //*[@data-type='cart']")
            print("   ✓ Found cart link/icon")
            
            # Get the URL and navigate to it
            cart_url = cart_icon.get_attribute("href")
            if cart_url:
                print(f"   Navigating to: {cart_url}")
                driver.get(cart_url)
                time.sleep(5)
                
                body_text = driver.find_element(By.TAG_NAME, "body").text
                if "empty" in body_text.lower():
                    print("   ✗ Cart is empty via header link")
                else:
                    print("   ✓ Cart has content via header link")
                    # Try to find CALCULATE button
                    try:
                        calc_btn = driver.find_element(By.CSS_SELECTOR, 'button.get-rates')
                        print("   ✓ Found CALCULATE SHIPPING button!")
                    except:
                        print("   ✗ No CALCULATE SHIPPING button")
        except Exception as e:
            print(f"   ✗ Error accessing cart via header: {e}")
        
        print("\n" + "=" * 80)
        print("INSPECTION COMPLETE")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n✗ Inspection error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    inspect_cart_persistence()
