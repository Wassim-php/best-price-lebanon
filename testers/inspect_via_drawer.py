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

def inspect_via_drawer():
    """Add to cart and use drawer to access cart, not direct navigation."""
    
    base_url = "https://mobileleb.com"
    search_query = "laptop"
    
    print("=" * 80)
    print("MOBILELEB - ADD TO CART VIA DRAWER INSPECTION")
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
            print("✗ Could not find product")
            return
        
        # --- 2. Load product page ---
        print("\n2. Loading product page...")
        driver.get(product_url)
        time.sleep(3)
        print("✓ Product page loaded")
        
        # --- 3. Add to cart ---
        print("\n3. Adding to cart...")
        try:
            add_btn = driver.find_element(By.CSS_SELECTOR, 'button.addtocart-js')
            driver.execute_script("arguments[0].click();", add_btn)
            time.sleep(3)
            print("✓ Added to cart")
        except Exception as e:
            print(f"✗ Could not add to cart: {e}")
            return
        
        # --- 4. Look for cart icon/counter that shows item was added ---
        print("\n4. Looking for cart icon/badge with item count...")
        try:
            # Look for cart counter badge
            cart_badges = driver.find_elements(By.XPATH, "//*[contains(@class, 'cart')]//span[contains(text(), '1')] | //a[contains(@class, 'cart')]")
            print(f"   Found {len(cart_badges)} cart-related elements")
            
            # Click on cart icon to open drawer
            cart_links = driver.find_elements(By.XPATH, "//a[contains(@href, 'cart')] | //*[contains(@class, 'cart-icon')]")
            print(f"   Found {len(cart_links)} cart icon/link elements")
            
            if cart_links:
                print("   ✓ Found cart icon - clicking it...")
                driver.execute_script("arguments[0].click();", cart_links[0])
                time.sleep(3)
                print("   ✓ Clicked cart icon")
        except Exception as e:
            print(f"   ⚠ Error with cart icon: {e}")
        
        # --- 5. Look for modal/drawer that might have appeared ---
        print("\n5. Checking for cart drawer/modal...")
        
        # Check page content
        body_text = driver.find_element(By.TAG_NAME, "body").text
        
        if "view cart" in body_text.lower():
            print("   ✓ Found 'View Cart' text - clicking it...")
            try:
                view_cart = driver.find_element(By.XPATH, "//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'view cart')]")
                driver.execute_script("arguments[0].click();", view_cart)
                time.sleep(3)
                print("   ✓ Clicked 'View Cart'")
            except:
                print("   ✗ Could not click 'View Cart'")
        
        # --- 6. Check cart status now ---
        print("\n6. Checking cart status after drawer interaction...")
        body_text = driver.find_element(By.TAG_NAME, "body").text
        
        if "empty" in body_text.lower():
            print("   ✗ Cart still appears empty")
        else:
            print("   ✓ Cart appears to have items")
            
            # Print cart section content
            print("\n   Cart content:")
            lines = body_text.split("\n")
            for line in lines:
                if any(kw in line.lower() for kw in ["cart", "item", "price", "total", "shipping"]):
                    print(f"      {line[:100]}")
        
        # --- 7. Look for CALCULATE SHIPPING button regardless ---
        print("\n7. Looking for CALCULATE SHIPPING button...")
        try:
            calc_btn = driver.find_element(By.CSS_SELECTOR, 'button.get-rates')
            print("   ✓ FOUND CALCULATE SHIPPING button!")
            print(f"      Button text: '{calc_btn.text}'")
        except:
            print("   ✗ CALCULATE SHIPPING button not found")
            
            # Check what buttons exist
            buttons_text = ""
            buttons = driver.find_elements(By.TAG_NAME, "button")
            for btn in buttons:
                if btn.text.strip():
                    buttons_text += btn.text.strip() + " | "
            
            print(f"   Buttons found: {buttons_text[:200]}")
        
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
    inspect_via_drawer()
