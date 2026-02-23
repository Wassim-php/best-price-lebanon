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

def inspect_mobileleb_detailed():
    """Detailed inspection of Mobileleb cart page structure and buttons."""
    
    base_url = "https://mobileleb.com"
    search_query = "laptop"
    
    print("=" * 80)
    print("MOBILELEB DETAILED CART INSPECTION")
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
        time.sleep(3)
        print("✓ Product page loaded")
        
        body_text = driver.find_element(By.TAG_NAME, "body").text
        price_match = _PRICE_RE.search(body_text)
        if price_match:
            print(f"   Price: ${price_match.group(1)}")
        
        # --- 3. Add to cart ---
        print("\n3. Adding to cart...")
        try:
            add_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'ADD TO CART')] | //button[contains(text(), 'Add to cart')] | //button[contains(text(), 'ADD TO BAG')]"))
            )
            driver.execute_script("arguments[0].click();", add_btn)
            time.sleep(2)
            print("✓ Added to cart")
        except TimeoutException:
            print("✗ Could not find ADD TO CART button")
            return
        
        # --- 4. Keep page on product for 10 seconds to observe session ---
        print("\n4. Waiting 10 seconds before navigating away...")
        time.sleep(10)
        print("✓ Waited")
        
        # --- 5. Navigate to cart page ---
        print("\n5. Navigating to cart page directly...")
        driver.get(f"{base_url}/cart")
        time.sleep(5)
        print("✓ On cart page")
        
        body_html = driver.find_element(By.TAG_NAME, "html").get_attribute("outerHTML")
        
        # --- 6. Check if cart has items ---
        print("\n6. Analyzing cart page structure...")
        body_text = driver.find_element(By.TAG_NAME, "body").text
        
        if "empty" in body_text.lower():
            print("✗ Cart is EMPTY")
        else:
            print("✓ Cart has items")
        
        # --- 7. List ALL buttons on page with their properties ---
        print("\n7. ALL BUTTONS ON CART PAGE:")
        buttons = driver.find_elements(By.TAG_NAME, "button")
        print(f"   Total buttons found: {len(buttons)}\n")
        
        for i, btn in enumerate(buttons):
            try:
                btn_text = btn.text.strip()
                btn_id = btn.get_attribute("id") or "(no id)"
                btn_class = btn.get_attribute("class") or "(no class)"
                btn_name = btn.get_attribute("name") or "(no name)"
                aria_label = btn.get_attribute("aria-label") or "(no aria-label)"
                
                if btn_text:
                    print(f"   [{i}] TEXT: '{btn_text}'")
                    print(f"        ID: {btn_id}, NAME: {btn_name}")
                    print(f"        CLASS: {btn_class[:80]}")
                    print(f"        ARIA-LABEL: {aria_label}")
                    print()
            except Exception as e:
                print(f"   [{i}] Error reading button: {e}\n")
        
        # --- 8. Look for input fields (address, location, etc.) ---
        print("\n8. INPUT FIELDS ON CART PAGE:")
        inputs = driver.find_elements(By.TAG_NAME, "input")
        print(f"   Total inputs found: {len(inputs)}\n")
        
        for i, inp in enumerate(inputs[:20]):  # Show first 20
            try:
                inp_type = inp.get_attribute("type") or "(no type)"
                inp_id = inp.get_attribute("id") or "(no id)"
                inp_name = inp.get_attribute("name") or "(no name)"
                inp_placeholder = inp.get_attribute("placeholder") or "(no placeholder)"
                
                if inp_name or inp_id or inp_placeholder:
                    print(f"   [{i}] TYPE: {inp_type}, ID: {inp_id}")
                    print(f"        NAME: {inp_name}, PLACEHOLDER: {inp_placeholder}")
                    print()
            except Exception as e:
                print(f"   [{i}] Error reading input: {e}\n")
        
        # --- 9. Look for select/dropdown elements ---
        print("\n9. DROPDOWNS ON CART PAGE:")
        selects = driver.find_elements(By.TAG_NAME, "select")
        print(f"   Total selects found: {len(selects)}\n")
        
        for i, sel in enumerate(selects):
            try:
                sel_id = sel.get_attribute("id") or "(no id)"
                sel_name = sel.get_attribute("name") or "(no name)"
                options = sel.find_elements(By.TAG_NAME, "option")
                print(f"   [{i}] ID: {sel_id}, NAME: {sel_name}")
                print(f"        Options: {[opt.text for opt in options[:5]]}")
                print()
            except Exception as e:
                print(f"   [{i}] Error reading select: {e}\n")
        
        # --- 10. Check page source for "calculate" keyword ---
        print("\n10. SEARCHING PAGE SOURCE FOR KEY TERMS:")
        page_source = driver.page_source.lower()
        
        terms = ["calculate", "shipping", "estimate", "delivery", "address", "beirut", "location"]
        for term in terms:
            if term in page_source:
                # Find context around keyword
                idx = page_source.find(term)
                context_start = max(0, idx - 100)
                context_end = min(len(page_source), idx + 100)
                context = driver.page_source[context_start:context_end].strip()
                
                print(f"   ✓ '{term}' found at position {idx}")
                print(f"      Context: ...{context}...")
                print()
        
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
    inspect_mobileleb_detailed()
