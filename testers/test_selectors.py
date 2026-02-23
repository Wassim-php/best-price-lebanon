#!/usr/bin/env python3
"""Try finding button by text instead of class."""

import sys
sys.path.insert(0, '/app')

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.common import Select
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

def test_button_selectors():
    """Test different selectors for CALCULATE SHIPPING button."""
    
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
        
        print("Testing button selectors on /cart page...")
        
        # Go directly to cart
        driver.get(f"{base_url}/cart")
        time.sleep(3)
        
        # Test all possible selectors
        selectors_to_try = [
            ('button.get-rates', 'CSS: button.get-rates'),
            ('//button[@class="get-rates"]', 'XPath: get-rates class'),
            ('//button[contains(text(), "CALCULATE")]', 'XPath: contains CALCULATE'),
            ('//button[contains(text(), "Calculate")]', 'XPath: contains Calculate'),
            ('//button[contains(translate(text(), "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "calculate")]', 'XPath: case-insensitive'),
            ('//button[contains(@class, "shipping")]', 'XPath: has shipping in class'),
            ('//button[@title*="shipping"]', 'XPath: shipping in title'),
            ('//button[contains(text(), "Shipping")]', 'XPath: contains Shipping'),
            ('//button[contains(@aria-label, "shipping")]', 'XPath: has shipping aria-label'),
        ]
        
        print("\n" + "=" * 80)
        print("SELECTOR TEST RESULTS")
        print("=" * 80 + "\n")
        
        found_any = False
        for selector, description in selectors_to_try:
            try:
                if selector.startswith("//"):
                    elements = driver.find_elements(By.XPATH, selector)
                else:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                
                if elements:
                    print(f"✓ {description}")
                    print(f"  Found {len(elements)} element(s)")
                    for i, elem in enumerate(elements[:2]):
                        print(f"    [{i}] {elem.text[:60]}")
                    found_any = True
                else:
                    print(f"✗ {description} - 0 elements")
            except Exception as e:
                print(f"✗ {description} - Error: {str(e)[:60]}")
        
        if not found_any:
            print("\n⚠ No button selectors found ANY matches on empty /cart page")
            print("This is expected because cart is empty. In real usage with items, buttons will appear.")
        
        # Also check what buttons exist
        print("\n" + "=" * 80)
        print("ALL BUTTONS ON /CART PAGE")
        print("=" * 80)
        
        buttons = driver.find_elements(By.TAG_NAME, "button")
        print(f"\nTotal buttons: {len(buttons)}\n")
        
        for i, btn in enumerate(buttons):
            text = btn.text.strip()
            cls = btn.get_attribute("class") or ""
            if text:
                print(f"[{i}] Text: '{text}' | Class: {cls[:60]}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    test_button_selectors()
