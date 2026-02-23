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

def inspect_mobileleb_product_page():
    """Inspect what buttons are available on Mobileleb product page."""
    
    base_url = "https://mobileleb.com"
    search_query = "laptop"
    
    print("=" * 80)
    print("MOBILELEB PRODUCT PAGE INSPECTION")
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
            print(f"✓ Found product: {product_url}")
        except:
            print("✗ Could not find product")
            return
        
        # --- 2. Load product page ---
        print("\n2. Loading product page...")
        driver.get(product_url)
        time.sleep(5)
        print("✓ Product page loaded\n")
        
        body_text = driver.find_element(By.TAG_NAME, "body").text
        price_match = _PRICE_RE.search(body_text)
        if price_match:
            print(f"   Price found: ${price_match.group(1)}\n")
        
        # --- 3. List ALL buttons on product page ---
        print("=" * 80)
        print("ALL BUTTONS ON PRODUCT PAGE")
        print("=" * 80)
        buttons = driver.find_elements(By.TAG_NAME, "button")
        print(f"Total buttons found: {len(buttons)}\n")
        
        for i, btn in enumerate(buttons):
            try:
                btn_text = btn.text.strip()
                btn_id = btn.get_attribute("id") or ""
                btn_class = btn.get_attribute("class") or ""
                btn_name = btn.get_attribute("name") or ""
                aria_label = btn.get_attribute("aria-label") or ""
                
                print(f"Button {i}:")
                print(f"  Text: '{btn_text}'")
                if btn_id:
                    print(f"  ID: {btn_id}")
                if btn_class:
                    print(f"  Class: {btn_class[:100]}...")
                if btn_name:
                    print(f"  Name: {btn_name}")
                if aria_label:
                    print(f"  Aria-label: {aria_label}")
                print()
                
            except Exception as e:
                print(f"Button {i}: Error reading - {e}\n")
        
        # --- 4. Look for add to cart more broadly ---
        print("=" * 80)
        print("SEARCHING FOR 'ADD TO CART' RELATED ELEMENTS")
        print("=" * 80)
        
        # Search by text
        try:
            xpath = "//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'add to')]"
            elements = driver.find_elements(By.XPATH, xpath)
            print(f"\nFound {len(elements)} elements containing 'add to':\n")
            for i, elem in enumerate(elements[:10]):
                print(f"  [{i}] Tag: {elem.tag_name}, Text: '{elem.text.strip()[:80]}'")
        except Exception as e:
            print(f"Error searching for 'add to' elements: {e}")
        
        # Search for cart keyword
        try:
            xpath = "//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'cart')]"
            elements = driver.find_elements(By.XPATH, xpath)
            print(f"\nFound {len(elements)} elements containing 'cart':\n")
            for i, elem in enumerate(elements[:10]):
                print(f"  [{i}] Tag: {elem.tag_name}, Text: '{elem.text.strip()[:80]}'")
        except Exception as e:
            print(f"Error searching for 'cart' elements: {e}")
        
        # --- 5. Check page source for cart keywords ---
        print("\n" + "=" * 80)
        print("PAGE SOURCE KEYWORDS")
        print("=" * 80)
        page_source = driver.page_source.lower()
        
        keywords = ["cart", "calculate", "deliver", "beirut", "add", "buy"]
        for kw in keywords:
            count = page_source.count(kw)
            if count > 0:
                print(f"✓ '{kw}': found {count} times")
            else:
                print(f"✗ '{kw}': not found")
        
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
    inspect_mobileleb_product_page()
