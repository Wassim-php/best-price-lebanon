import re
from typing import Optional
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

def inspect_cart_with_items():
    """Add to cart and check /cart multiple times with waits."""
    
    base_url = "https://mobileleb.com"
    search_query = "laptop"
    
    print("=" * 80)
    print("MOBILELEB - CART WITH ITEMS INSPECTION")
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
        
        # --- 1. Initial setup ---
        print("\n1. Setting up...")
        search_url = f"{base_url}/search?q={search_query}&type=product"
        driver.get(search_url)
        time.sleep(3)
        
        first_product = driver.find_element(By.CSS_SELECTOR, 'a[href*="/products/"]')
        product_url = first_product.get_attribute("href")
        
        driver.get(product_url)
        time.sleep(3)
        print("✓ On product page")
        
        # --- 2. Add to cart ---
        print("\n2. Adding to cart...")
        add_btn = driver.find_element(By.CSS_SELECTOR, 'button.addtocart-js')
        driver.execute_script("arguments[0].click();", add_btn)
        time.sleep(3)
        print("✓ Clicked ADD TO CART - waiting for processing...")
        
        # --- 3. Wait for page to process the add-to-cart ---
        print("\n3. Waiting for cart to process (5 seconds)...")
        time.sleep(5)
        
        # --- 4. Navigate to cart ---
        print("\n4. Navigating to /cart...")
        driver.get(f"{base_url}/cart")
        
        # --- 5. Wait multiple times and check for button ---
        print("\n5. Checking for CALCULATE SHIPPING button (waiting 2 sec intervals)...")
        
        button_found = False
        for attempt in range(5):
            time.sleep(2)
            print(f"   Attempt {attempt + 1}/5...")
            
            page_source = driver.page_source
            
            # Check if get-rates button is in the page source
            if "get-rates" in page_source.lower():
                print(f"   ✓ SUCCESS: Found 'get-rates' in page source at attempt {attempt + 1}")
                button_found = True
                break
            
            # Also try to find it via DOM
            try:
                calc_btn = driver.find_element(By.CSS_SELECTOR, 'button.get-rates')
                print(f"   ✓ SUCCESS: Found button in DOM at attempt {attempt + 1}")
                button_found = True
                break
            except NoSuchElementException:
                pass
            
            # Check what's in cart
            body_text = driver.find_element(By.TAG_NAME, "body").text
            if "empty" in body_text.lower():
                print(f"   ✗ Cart still empty")
            else:
                print(f"   ✓ Cart has content")
        
        if button_found:
            print("\n✓ CALCULATE SHIPPING button found!")
            
            # Now inspect the form around it
            try:
                calc_btn = driver.find_element(By.CSS_SELECTOR, 'button.get-rates')
                print(f"\n6. Button details:")
                print(f"   Text: '{calc_btn.text}'")
                print(f"   Class: {calc_btn.get_attribute('class')}")
                
                # Find parent container and inspect inputs
                parent = calc_btn.find_element(By.XPATH, "ancestor::form | ancestor::div[@class]")
                
                # Look for address/location inputs
                inputs = parent.find_elements(By.TAG_NAME, "input")
                print(f"\n7. Inputs in form ({len(inputs)} total):")
                for inp in inputs:
                    inp_type = inp.get_attribute("type") or ""
                    inp_name = inp.get_attribute("name") or ""
                    inp_placeholder = inp.get_attribute("placeholder") or ""
                    
                    if inp_type or inp_name or inp_placeholder:
                        print(f"   - Type: {inp_type}, Name: {inp_name}, Placeholder: {inp_placeholder}")
                
                # Look for radio buttons or select for location
                radios = parent.find_elements(By.CSS_SELECTOR, 'input[type="radio"]')
                print(f"\n8. Radio buttons ({len(radios)} total):")
                for i, radio in enumerate(radios[:5]):
                    radio_value = radio.get_attribute("value") or ""
                    radio_name = radio.get_attribute("name") or ""
                    parent_label = radio.find_element(By.XPATH, "..").text
                    print(f"   Radio {i}: name={radio_name}, value={radio_value}, label={parent_label[:80]}")
                
                # Look for selects
                selects = parent.find_elements(By.TAG_NAME, "select")
                print(f"\n9. Selects/dropdowns ({len(selects)} total):")
                for select in selects:
                    select_name = select.get_attribute("name") or ""
                    options = select.find_elements(By.TAG_NAME, "option")
                    opt_texts = [opt.text for opt in options[:5]]
                    print(f"   Select: name={select_name}, options={opt_texts}")
                
            except Exception as e:
                print(f"\n✗ Error inspecting form: {e}")
        
        else:
            print("\n✗ CALCULATE SHIPPING button NOT found after 5 attempts with 2-second waits")
            
            # Debug: Print what's on the page
            body_text = driver.find_element(By.TAG_NAME, "body").text
            print(f"\nPage status:")
            if "empty" in body_text.lower():
                print("   Cart is EMPTY")
            else:
                print("   Cart has content")
            
            # Print first 1500 chars of page source
            page_source = driver.page_source
            print(f"\nPage source preview (cart-related sections):")
            
            # Search for any shipping or calculate related text
            if "shipping" in page_source.lower():
                idx = page_source.lower().find("shipping")
                start = max(0, idx - 200)
                end = min(len(page_source), idx + 300)
                print(f"   'shipping' context: ...{page_source[start:end]}...")
            
            if "calculate" in page_source.lower():
                idx = page_source.lower().find("calculate")
                start = max(0, idx - 200)
                end = min(len(page_source), idx + 300)
                print(f"   'calculate' context: ...{page_source[start:end]}...")
        
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
    inspect_cart_with_items()
