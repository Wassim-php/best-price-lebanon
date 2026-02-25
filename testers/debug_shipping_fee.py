#!/usr/bin/env python3
"""Debug test for Mobileleb shipping fee extraction."""

import sys
sys.path.insert(0, '/app')

from scraping.adapters.websites.mobileleb import MobileLebAdapter
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import re

_PRICE_RE = re.compile(r"(\d+(?:,\d{3})*(?:\.\d+)?)")

def debug_mobileleb():
    """Debug shipping fee extraction by manually stepping through."""
    
    base_url = "https://mobileleb.com"
    search_query = "laptop"
    
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
        
        print("=" * 80)
        print("MOBILELEB SHIPPING FEE DEBUG")
        print("=" * 80)
        
        # --- 1. Search ---
        print("\n1. Searching for products...")
        search_url = f"{base_url}/search?q={search_query}&type=product"
        driver.get(search_url)
        time.sleep(3)
        
        first_product = driver.find_element(By.CSS_SELECTOR, 'a[href*="/products/"]')
        product_url = first_product.get_attribute("href")
        print(f"✓ Found product")
        
        # --- 2. Load product ---
        print("\n2. Loading product...")
        driver.get(product_url)
        time.sleep(2)
        
        # Get price
        try:
            price_element = driver.find_element(By.CSS_SELECTOR, '.price-item--sale, .new-price, .tt-price span')
            price_text = price_element.text.replace(',', '').replace('$', '').strip()
            m = _PRICE_RE.search(price_text)
            if m:
                item_price = float(m.group(1).replace(',', ''))
            print(f"✓ Product price: ${item_price}")
        except:
            item_price = 0.0
        
        # --- 3. Add to cart ---
        print("\n3. Adding to cart...")
        add_btn = driver.find_element(By.CSS_SELECTOR, 'button.addtocart-js, button[name="add"]')
        driver.execute_script("arguments[0].click();", add_btn)
        time.sleep(2)
        print("✓ Added to cart")
        
        # --- 4. Wait for popup and click View Cart ---
        print("\n4. Waiting for cart popup...")
        time.sleep(2)
        
        try:
            view_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, 
                    "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'view')] | "
                    "//a[contains(text(), 'View Cart')] | "
                    "//button[contains(text(), 'Cart')]"))
            )
            print("✓ Found View Cart button in popup")
            driver.execute_script("arguments[0].click();", view_btn)
            time.sleep(4)
        except Exception as e:
            print(f"✗ Error with popup: {e}")
            driver.get(f"{base_url}/cart")
            time.sleep(4)
        
        # --- 5. Find CALCULATE SHIPPING button ---
        print("\n5. Finding CALCULATE SHIPPING button...")
        try:
            calc_btn = driver.find_element(By.CSS_SELECTOR, 'button.get-rates')
            print("✓ Found CALCULATE SHIPPING button")
            
            # Print button and surrounding HTML
            button_html = calc_btn.get_attribute("outerHTML")
            print(f"\nButton HTML: {button_html}")
            
            # Get parent container
            parent = calc_btn.find_element(By.XPATH, "..")
            parent_html = parent.get_attribute("outerHTML")
            print(f"\nParent container length: {len(parent_html)} chars")
            print(f"Parent text before click:\n{parent.text[:500]}\n")
            
        except Exception as e:
            print(f"✗ Button not found: {e}")
            return
        
        # --- 6. Click button and analyze result ---
        print("6. Clicking CALCULATE SHIPPING button...")
        driver.execute_script("arguments[0].click();", calc_btn)
        time.sleep(4)
        
        # Get updated parent text
        try:
            parent = calc_btn.find_element(By.XPATH, "..")
            parent_text = parent.text
            print(f"\nParent text AFTER click:")
            print(parent_text)
            print(f"\n--- Analysis ---")
            
            # Look for price patterns
            prices = _PRICE_RE.findall(parent_text)
            if prices:
                print(f"Found prices in parent: {prices}")
            
            # Look for keywords
            if 'shipping' in parent_text.lower():
                print("✓ Found 'shipping' keyword")
            if 'delivery' in parent_text.lower():
                print("✓ Found 'delivery' keyword")
            if 'fee' in parent_text.lower():
                print("✓ Found 'fee' keyword")
            
            # Print each line
            lines = parent_text.split('\n')
            print(f"\nLines in parent ({len(lines)} total):")
            for i, line in enumerate(lines):
                if line.strip():
                    print(f"  [{i}] {line}")
                    
        except Exception as e:
            print(f"Error accessing parent: {e}")
        
        # --- 7. Also check full page ---
        print("\n7. Full page body text (first 2000 chars):")
        body_text = driver.find_element(By.TAG_NAME, "body").text
        print(body_text[:2000])
        
        # Look for shipping in full page
        print("\n--- Searching full page for shipping fee ---")
        if 'shipping' in body_text.lower():
            # Find the section with shipping
            idx = body_text.lower().find('shipping')
            start = max(0, idx - 100)
            end = min(len(body_text), idx + 200)
            print(f"Context around 'shipping': ...{body_text[start:end]}...")
        
        print("\n" + "=" * 80)
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    debug_mobileleb()
