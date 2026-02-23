#!/usr/bin/env python
"""
Debug the exact workflow: ADD → CONTINUE → VIEW CART → CALCULATE SHIPPING
"""
import os
import sys
sys.path.insert(0, "/app")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "best_price_lebanon.settings")

import django
django.setup()

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import re

base_url = "https://mobileleb.com"
product_url = "https://mobileleb.com/products/anker-prime-charger-100w-3-port-gan-usb-c-charger-block-foldable-compact"

print("=" * 80)
print("STEP-BY-STEP WORKFLOW DEBUG")
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
    
    # STEP 1: Load product
    print("\n[STEP 1] Load product page...")
    driver.get(product_url)
    time.sleep(2)
    print(f"  ✓ URL: {driver.current_url[:50]}...")
    
    # STEP 2: Click ADD TO CART
    print("\n[STEP 2] Click ADD TO CART...")
    add_btn = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.addtocart-js, button[name="add"]'))
    )
    driver.execute_script("arguments[0].click();", add_btn)
    time.sleep(3)
    print("  ✓ Clicked ADD TO CART")
    
    # STEP 3: Click CONTINUE in popup
    print("\n[STEP 3] Click CONTINUE in popup...")
    try:
        continue_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'CONTINUE') or contains(text(), 'Continue')]"))
        )
        driver.execute_script("arguments[0].click();", continue_btn)
        time.sleep(3)
        print("  ✓ Clicked CONTINUE")
    except Exception as e:
        print(f"  ⚠ CONTINUE not found: {e}")
    
    # STEP 4: Click VIEW CART
    print("\n[STEP 4] Click VIEW CART in popup...")
    try:
        view_cart = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'View')] | //a[contains(text(), 'View Cart')]"))
        )
        driver.execute_script("arguments[0].click();", view_cart)
        time.sleep(5)
        print("  ✓ Clicked VIEW CART")
        print(f"  Current URL: {driver.current_url}")
    except Exception as e:
        print(f"  ⚠ VIEW CART not found: {e}")
        time.sleep(2)
    
    # STEP 5: Verify on cart page
    print("\n[STEP 5] Verify cart page...")
    page_text = driver.find_element(By.TAG_NAME, "body").text
    if "empty" in page_text.lower():
        print("  ✗ Cart is EMPTY!")
    else:
        print("  ✓ Cart has items")
    
    # STEP 6: Click CALCULATE SHIPPING
    print("\n[STEP 6] Click CALCULATE SHIPPING...")
    try:
        calc_btn = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'CALCULATE')] | //button[contains(text(), 'Calculate')]"))
        )
        print(f"  ✓ Found CALCULATE button: '{calc_btn.text.strip()}'")
        driver.execute_script("arguments[0].click();", calc_btn)
        time.sleep(5)
        print("  ✓ Clicked CALCULATE SHIPPING")
    except Exception as e:
        print(f"  ✗ CALCULATE button not found: {e}")
    
    # STEP 7: Extract shipping fee
    print("\n[STEP 7] Extract shipping fee...")
    page_text = driver.find_element(By.TAG_NAME, "body").text
    
    # Look for shipping fee
    lines = page_text.split('\n')
    for i, line in enumerate(lines):
        if 'shipping' in line.lower() or 'delivery' in line.lower():
            print(f"  Line {i}: {line.strip()[:80]}")
    
    # Try to extract price from lines mentioning shipping
    _PRICE_RE = re.compile(r"(\d+(?:,\d{3})*(?:\.\d+)?)")
    shipping_found = False
    for i, line in enumerate(lines):
        line_lower = line.lower().strip()
        if ('shipping' in line_lower or 'delivery' in line_lower or 'fee' in line_lower) and '$' in line:
            prices = _PRICE_RE.findall(line)
            if prices:
                fee = float(prices[-1].replace(',', ''))
                print(f"  ✓ Found shipping fee: ${fee}")
                shipping_found = True
                break
    
    if not shipping_found:
        print("  ✗ No shipping fee found in page")
    
    print("\n" + "=" * 80)
    print("Workflow complete!")
    print("=" * 80)

except Exception as e:
    print(f"\n✗ ERROR: {e}")
    import traceback
    traceback.print_exc()
finally:
    if driver:
        driver.quit()
