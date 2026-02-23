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

def inspect_same_session_cart():
    """Don't use headless; navigate to /cart in same session immediately after ADD."""
    
    base_url = "https://mobileleb.com"
    search_query = "laptop"
    
    print("=" * 80)
    print("MOBILELEB - SAME SESSION CART NAVIGATION")
    print("=" * 80)
    
    # Keep headless for Docker
    chrome_options = Options()
    chrome_options.add_argument('--headless')  
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    driver = None
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_page_load_timeout(30)
        
        # --- 1. Search and load product ---
        print("\n1. Loading product page...")
        search_url = f"{base_url}/search?q={search_query}&type=product"
        driver.get(search_url)
        time.sleep(3)
        
        first_product = driver.find_element(By.CSS_SELECTOR, 'a[href*="/products/"]')
        product_url = first_product.get_attribute("href")
        print(f"   Product: {product_url.split('/')[-1][:40]}")
        
        driver.get(product_url)
        time.sleep(3)
        print("✓ On product page")
        
        # --- 2. Add to cart ---
        print("\n2. Adding to cart...")
        add_btn = driver.find_element(By.CSS_SELECTOR, 'button.addtocart-js')
        driver.execute_script("arguments[0].click();", add_btn)
        time.sleep(2)
        print("✓ Clicked ADD TO CART")
        
        # --- 3. IMMEDIATELY navigate to cart (don't wait for modal to fully process) ---
        print("\n3. Navigating to /cart immediately...")
        driver.get(f"{base_url}/cart")
        time.sleep(3)
        print("✓ Navigated to /cart")
        
        # --- 4. Check for CALCULATE SHIPPING button RIGHT AWAY ---
        print("\n4. Looking for CALCULATE SHIPPING button...")
        try:
            calc_btn = driver.find_element(By.CSS_SELECTOR, 'button.get-rates')
            print(f"✓ SUCCESS: Found CALCULATE SHIPPING button!")
            print(f"   Text: '{calc_btn.text}'")
            
            # Inspect form around the button
            print("\n5. Inspecting form elements near button...")
            
            # Find parent form or container
            parent = calc_btn.find_element(By.XPATH, "..")
            form_html = parent.get_attribute("outerHTML")
            print(f"   Parent container: {form_html[:300]}...")
            
            # Look for inputs in the same container
            inputs_nearby = parent.find_elements(By.TAG_NAME, "input")
            print(f"   Inputs in same container: {len(inputs_nearby)}")
            
            for inp in inputs_nearby:
                inp_type = inp.get_attribute("type") or ""
                inp_name = inp.get_attribute("name") or ""
                inp_id = inp.get_attribute("id") or ""
                inp_placeholder = inp.get_attribute("placeholder") or ""
                
                print(f"      Input: type={inp_type}, name={inp_name}, placeholder={inp_placeholder}")
            
            # Check for radio buttons (location)
            radios = parent.find_elements(By.CSS_SELECTOR, 'input[type="radio"]')
            print(f"   Radio buttons in same container: {len(radios)}")
            
            for i, radio in enumerate(radios):
                radio_value = radio.get_attribute("value") or ""
                label = radio.find_element(By.XPATH, "..").text
                print(f"      Radio {i}: value={radio_value}, label={label[:80]}")
            
            print("\n✓ CALCULATE SHIPPING button found successfully!")
            
        except NoSuchElementException:
            print("✗ CALCULATE SHIPPING button NOT found")
            
            # Check cart status
            body_text = driver.find_element(By.TAG_NAME, "body").text
            if "empty" in body_text.lower():
                print("   Cart is empty")
            else:
                print("   Cart appears to have content")
            
            # List all buttons
            buttons = driver.find_elements(By.TAG_NAME, "button")
            print(f"\n   Total buttons: {len(buttons)}")
            
            print("   Buttons with text:")
            for btn in buttons:
                text = btn.text.strip()
                if text:
                    cls = btn.get_attribute("class") or ""
                    print(f"      '{text}' | {cls[:60]}")
        
        print("\n" + "=" * 80)
        print("INSPECTION COMPLETE - Check browser window for visual verification")
        print("=" * 80)
        
        # Keep window open for 5 seconds so you can see it
        time.sleep(5)
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    inspect_same_session_cart()
