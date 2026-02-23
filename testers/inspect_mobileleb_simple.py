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

def inspect_mobileleb_cart_drawer():
    """Inspect Mobileleb cart drawer and cart page for shipping calculation."""
    
    base_url = "https://mobileleb.com"
    search_query = "laptop"
    
    print("=" * 80)
    print("MOBILELEB CART DRAWER & PAGE INSPECTION")
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
        print("✓ Search page loaded")
        
        # Get first product link
        try:
            first_product = driver.find_element(By.CSS_SELECTOR, 'a[href*="/products/"]')
            product_url = first_product.get_attribute("href")
            print(f"✓ Found product")
        except:
            print("✗ Could not find product link")
            return
        
        # --- 2. Navigate to product page ---
        print("\n2. Loading product page...")
        driver.get(product_url)
        time.sleep(2)
        print("✓ Product page loaded")
        
        # Get product title and price
        try:
            price_element = driver.find_element(By.CSS_SELECTOR, '.new-price, .price-item--sale, .tt-price span')
            price_text = price_element.text
            m = _PRICE_RE.search(price_text)
            if m:
                price = float(m.group(1).replace(',', ''))
                print(f"   Price: ${price}")
        except Exception as e:
            print(f"   Could not extract price: {e}")
        
        # --- 3. Add to Cart ---
        print("\n3. Adding to cart...")
        try:
            add_to_cart_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[name="add"], .btn-addtocart'))
            )
            driver.execute_script("arguments[0].click();", add_to_cart_btn)
            time.sleep(2)
            print("✓ Added to cart")
        except Exception as e:
            print(f"✗ Could not add to cart: {e}")
            return
        
        # --- 4. Inspect Cart Drawer (After Add to Cart Pop-up) ---
        print("\n4. Inspecting cart drawer after add to cart...")
        try:
            drawer = driver.find_element(By.CSS_SELECTOR, '[role="dialog"], .cart-drawer, .drawer')
            drawer_text = drawer.text
            print(f"✓ Found cart drawer")
            print("\n--- Cart Drawer Content (first 1500 chars) ---")
            print(drawer_text[:1500])
            print("\n")
        except Exception as e:
            print(f"⚠ Could not find drawer: {e}")
        
        # --- 5. Click CONTINUE button in drawer ---
        print("\n5. Looking for CONTINUE button in drawer...")
        try:
            continue_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'CONTINUE')] | //button[contains(text(), 'Continue')]"))
            )
            print("✓ Found CONTINUE button")
            driver.execute_script("arguments[0].click();", continue_btn)
            time.sleep(2)
            print("✓ Clicked CONTINUE")
        except TimeoutException:
            print("⚠ No CONTINUE button found in drawer")
        
        # --- 6. Click VIEW CART button ---
        print("\n6. Looking for VIEW CART button...")
        try:
            view_cart_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, '/cart')] | //button[contains(text(), 'View Cart')] | //button[contains(text(), 'VIEW CART')]"))
            )
            print("✓ Found VIEW CART button")
            driver.execute_script("arguments[0].click();", view_cart_btn)
            time.sleep(4)
            print("✓ Navigated to cart page (View Cart button)")
        except TimeoutException:
            print("⚠ No VIEW CART button, trying direct navigation...")
            driver.get(f"{base_url}/cart")
            time.sleep(4)
        
        # --- 7. Inspect Cart Page ---
        print("\n7. Inspecting cart page...")
        body_text = driver.find_element(By.TAG_NAME, "body").text
        
        if "empty" in body_text.lower():
            print("✗ Cart is empty on cart page")
        else:
            print("✓ Cart page has items")
        
        print("\n--- Cart Page Content (first 2000 chars) ---")
        print(body_text[:2000])
        print("\n")
        
        # --- 8. Look for shipping calculator elements ---
        print("\n8. Looking for shipping calculator elements...")
        
        # Calculate/Shipping button
        buttons = driver.find_elements(By.TAG_NAME, "button")
        print(f"   Found {len(buttons)} buttons")
        for i, btn in enumerate(buttons[:10]):
            try:
                btn_text = btn.text.strip()
                if btn_text:
                    print(f"   Button {i}: '{btn_text}'")
            except:
                pass
        
        # --- 9. Look for location/shipping radio buttons ---
        print("\n9. Looking for shipping location options...")
        radios = driver.find_elements(By.CSS_SELECTOR, 'input[type="radio"]')
        print(f"   Found {len(radios)} radio buttons")
        
        for i, radio in enumerate(radios):
            try:
                parent = radio.find_element(By.XPATH, "../.. | ..")
                parent_text = parent.text
                if parent_text and "beirut" in parent_text.lower():
                    print(f"   Radio {i}: {parent_text[:120]}")
            except:
                pass
        
        # --- 10. Check page source for shipping/location keywords ---
        print("\n10. Searching page source for shipping-related keywords...")
        page_source = driver.page_source.lower()
        
        keywords = ["calculate", "shipping", "beirut", "delivery", "location", "address"]
        found_keywords = []
        for kw in keywords:
            if kw in page_source:
                found_keywords.append(kw)
        
        if found_keywords:
            print(f"   ✓ Found keywords: {', '.join(found_keywords)}")
        else:
            print(f"   ✗ No shipping-related keywords found")
        
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
    inspect_mobileleb_cart_drawer()
