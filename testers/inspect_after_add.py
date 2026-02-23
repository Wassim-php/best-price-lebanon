import re
from typing import Optional
import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

_PRICE_RE = re.compile(r"(\d+(?:,\d{3})*(?:\.\d+)?)")

def inspect_after_add_to_cart():
    """Inspect page immediately after ADD TO CART button click."""
    
    base_url = "https://mobileleb.com"
    search_query = "laptop"
    
    print("=" * 80)
    print("MOBILELEB - IMMEDIATELY AFTER ADD TO CART")
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
        
        # --- 1. Search and load product ---
        print("\n1. Searching for product...")
        search_url = f"{base_url}/search?q={search_query}&type=product"
        driver.get(search_url)
        time.sleep(3)
        
        first_product = driver.find_element(By.CSS_SELECTOR, 'a[href*="/products/"]')
        product_url = first_product.get_attribute("href")
        
        print("2. Loading product page...")
        driver.get(product_url)
        time.sleep(3)
        print("✓ Product page loaded")
        
        # --- 2. Click ADD TO CART ---
        print("\n3. Clicking ADD TO CART...")
        add_btn = driver.find_element(By.CSS_SELECTOR, 'button.addtocart-js')
        driver.execute_script("arguments[0].click();", add_btn)
        time.sleep(1)
        print("✓ Clicked ADD TO CART button")
        
        # --- 3. Immediately check for any visible buttons/elements ---
        print("\n4. Scanning page immediately after click (no additional wait)...")
        
        buttons = driver.find_elements(By.TAG_NAME, "button")
        print(f"   Total buttons visible: {len(buttons)}")
        
        print("\n   Buttons with text:")
        for i, btn in enumerate(buttons):
            text = btn.text.strip()
            if text:
                cls = btn.get_attribute("class") or ""
                print(f"   Button {i}: '{text}' | Class: {cls[:80]}")
        
        # Check specifically for get-rates class
        print("\n5. Looking for 'get-rates' button...")
        try:
            rates_btn = driver.find_element(By.CSS_SELECTOR, 'button.get-rates')
            print(f"   ✓ FOUND: '{rates_btn.text}' | Class: {rates_btn.get_attribute('class')}")
        except:
            print("   ✗ Not found in buttons")
        
        # --- 4. Wait 2 seconds and check again --- 
        print("\n6. Waiting 2 seconds...")
        time.sleep(2)
        
        buttons = driver.find_elements(By.TAG_NAME, "button")
        printed_any = False
        for btn in buttons:
            text = btn.text.strip()
            if "calculate" in text.lower() or "shipping" in text.lower() or "rate" in text.lower():
                cls = btn.get_attribute("class") or ""
                print(f"   ✓ Found: '{text}' | Class: {cls[:100]}")
                printed_any = True
        
        if not printed_any:
            print("   ✗ No calculate/shipping/rate buttons found")
        
        # --- 5. Check for modals/drawers ---
        print("\n7. Checking for modals/drawer overlays...")
        modals = driver.find_elements(By.XPATH, "//*[contains(@class, 'modal') or contains(@class, 'drawer') or contains(@class, 'popup')]")
        print(f"   Found {len(modals)} modal/drawer elements")
        
        # --- 6. Print full body text to see what's displayed ---
        print("\n8. Full page content (cart-related lines):")
        body_text = driver.find_element(By.TAG_NAME, "body").text
        lines = body_text.split("\n")
        
        cart_section_start = False
        for i, line in enumerate(lines):
            if "cart" in line.lower() or "calculate" in line.lower() or "shipping" in line.lower():
                cart_section_start = True
                print(f"   Line {i}: {line[:100]}")
            elif cart_section_start and i < len(lines) - 20:  # Print context around cart terms
                if line.strip():
                    print(f"   Line {i}: {line[:100]}")
        
        # --- 7. Wait longer and scan again ---
        print("\n9. Waiting 5 more seconds...")
        time.sleep(5)
        
        try:
            calc_btn = driver.find_element(By.CSS_SELECTOR, 'button.get-rates')
            print(f"   ✓ AFTER 5 SECS: Found CALCULATE SHIPPING button: '{calc_btn.text}'")
        except:
            print("   ✗ CALCULATE SHIPPING still not found")
        
        print("\n" + "=" * 80)
        print("INSPECTION COMPLETE")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    inspect_after_add_to_cart()
