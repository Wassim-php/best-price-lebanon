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

def inspect_calculate_shipping():
    """Find and click CALCULATE SHIPPING button, inspect the results."""
    
    base_url = "https://mobileleb.com"
    search_query = "laptop"
    
    print("=" * 80)
    print("MOBILELEB CALCULATE SHIPPING BUTTON INSPECTION")
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
            time.sleep(2)
            print("✓ Added to cart")
        except Exception as e:
            print(f"✗ Could not add to cart: {e}")
            return
        
        # --- 4. Navigate to cart page ---
        print("\n4. Navigating to cart page...")
        driver.get(f"{base_url}/cart")
        time.sleep(5)
        print("✓ On cart page")
        
        # --- 5. Check if cart has items ---
        print("\n5. Checking cart status...")
        body_text = driver.find_element(By.TAG_NAME, "body").text
        
        if "empty" in body_text.lower():
            print("✗ Cart is EMPTY - stopping inspection")
            return
        else:
            print("✓ Cart has items")
        
        # --- 6. Find CALCULATE SHIPPING button ---
        print("\n6. Looking for CALCULATE SHIPPING button...")
        try:
            calc_btn = driver.find_element(By.CSS_SELECTOR, 'button.get-rates')
            print("✓ Found CALCULATE SHIPPING button")
            print(f"   Button text: '{calc_btn.text}'")
            print(f"   Button class: '{calc_btn.get_attribute('class')}'")
            
            # --- 7. Inspect form elements before clicking ---
            print("\n7. Inspecting form elements BEFORE clicking button...")
            
            # Look for address/location inputs
            inputs = driver.find_elements(By.TAG_NAME, "input")
            print(f"   Total inputs: {len(inputs)}")
            
            for i, inp in enumerate(inputs):
                try:
                    inp_type = inp.get_attribute("type") or "unknown"
                    inp_name = inp.get_attribute("name") or ""
                    inp_id = inp.get_attribute("id") or ""
                    inp_placeholder = inp.get_attribute("placeholder") or ""
                    inp_value = inp.get_attribute("value") or ""
                    
                    if inp_name or inp_id or inp_placeholder:
                        print(f"\n   Input {i}:")
                        print(f"     Type: {inp_type}")
                        if inp_name:
                            print(f"     Name: {inp_name}")
                        if inp_id:
                            print(f"     ID: {inp_id}")
                        if inp_placeholder:
                            print(f"     Placeholder: {inp_placeholder}")
                        if inp_value:
                            print(f"     Value: {inp_value}")
                except:
                    pass
            
            # Look for selects/dropdowns
            selects = driver.find_elements(By.TAG_NAME, "select")
            print(f"\n   Total selects/dropdowns: {len(selects)}")
            
            for i, sel in enumerate(selects):
                try:
                    sel_name = sel.get_attribute("name") or ""
                    sel_id = sel.get_attribute("id") or ""
                    options = sel.find_elements(By.TAG_NAME, "option")
                    opt_texts = [opt.text for opt in options[:10]]
                    
                    if sel_name or sel_id:
                        print(f"\n   Select {i}:")
                        if sel_name:
                            print(f"     Name: {sel_name}")
                        if sel_id:
                            print(f"     ID: {sel_id}")
                        print(f"     Options: {opt_texts}")
                except:
                    pass
            
            # Look for radio buttons
            radios = driver.find_elements(By.CSS_SELECTOR, 'input[type="radio"]')
            print(f"\n   Total radio buttons: {len(radios)}")
            
            for i, radio in enumerate(radios[:10]):
                try:
                    radio_name = radio.get_attribute("name") or ""
                    radio_value = radio.get_attribute("value") or ""
                    radio_id = radio.get_attribute("id") or ""
                    parent_text = radio.find_element(By.XPATH, "..").text or ""
                    
                    print(f"\n   Radio {i}:")
                    print(f"     Name: {radio_name}")
                    print(f"     Value: {radio_value}")
                    print(f"     ID: {radio_id}")
                    print(f"     Parent text: {parent_text[:80]}")
                except:
                    pass
            
            # --- 8. Click CALCULATE SHIPPING button ---
            print("\n8. Clicking CALCULATE SHIPPING button...")
            driver.execute_script("arguments[0].click();", calc_btn)
            time.sleep(3)
            print("✓ Clicked CALCULATE SHIPPING button")
            
            # --- 9. Inspect page after clicking ---
            print("\n9. Inspecting page AFTER clicking button...")
            
            # Look for new radio buttons or options
            radios_after = driver.find_elements(By.CSS_SELECTOR, 'input[type="radio"]')
            print(f"   Radio buttons now: {len(radios_after)}")
            
            if len(radios_after) > len(radios):
                print("\n   ✓ NEW RADIO BUTTONS APPEARED!")
                for i, radio in enumerate(radios_after[len(radios):]):
                    try:
                        radio_name = radio.get_attribute("name") or ""
                        radio_value = radio.get_attribute("value") or ""
                        parent_text = radio.find_element(By.XPATH, "..").text or ""
                        
                        print(f"\n   New Radio {i}:")
                        print(f"     Name: {radio_name}")
                        print(f"     Value: {radio_value}")
                        print(f"     Parent text: {parent_text[:100]}")
                    except:
                        pass
            
            # Look for new text appearing
            body_text_after = driver.find_element(By.TAG_NAME, "body").text
            
            if "beirut" in body_text_after.lower():
                print("\n   ✓ Found 'Beirut' text on page")
            
            if "shipping" in body_text_after.lower():
                print("   ✓ Found 'Shipping' text on page")
            
            # Print shipping-related text
            print("\n   Looking for shipping/rate information:")
            lines = body_text_after.split("\n")
            for i, line in enumerate(lines):
                if any(kw in line.lower() for kw in ["shipping", "rate", "beirut", "delivery", "price"]):
                    print(f"   Line {i}: {line[:100]}")
            
        except Exception as e:
            print(f"\n✗ Could not find CALCULATE SHIPPING button: {e}")
            import traceback
            traceback.print_exc()
        
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
    inspect_calculate_shipping()
