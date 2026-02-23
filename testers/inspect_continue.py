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

def inspect_continue_flow():
    """Click CONTINUE after ADD TO CART and see what appears."""
    
    base_url = "https://mobileleb.com"
    search_query = "laptop"
    
    print("=" * 80)
    print("MOBILELEB - ADD TO CART CONTINUE FLOW")
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
        print("\n1. Setting up...")
        search_url = f"{base_url}/search?q={search_query}&type=product"
        driver.get(search_url)
        time.sleep(3)
        
        first_product = driver.find_element(By.CSS_SELECTOR, 'a[href*="/products/"]')
        product_url = first_product.get_attribute("href")
        
        driver.get(product_url)
        time.sleep(3)
        print("✓ Product page ready")
        
        # --- 2. Click ADD TO CART ---
        print("\n2. Clicking ADD TO CART...")
        add_btn = driver.find_element(By.CSS_SELECTOR, 'button.addtocart-js')
        driver.execute_script("arguments[0].click();", add_btn)
        time.sleep(2)
        print("✓ Clicked ADD TO CART")
        
        # --- 3. Look for modal with CONTINUE button ---
        print("\n3. Looking for CONTINUE button...")
        try:
            continue_btn = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//button[contains(@class, 'ContinueButton')] | //*[contains(text(), 'CONTINUE')]"))
            )
            print(f"✓ Found CONTINUE button: '{continue_btn.text}'")
            
            # Before clicking, check what's in the modal
            print("\n4. Inspecting modal content BEFORE clicking CONTINUE...")
            modal = driver.find_element(By.XPATH, "//div[@role='dialog'] | //div[contains(@class, 'modal')]")
            modal_text = modal.text
            
            print("   Modal content (first 1000 chars):")
            print(f"   {modal_text[:1000]}")
            
            # Click CONTINUE
            print("\n5. Clicking CONTINUE button...")
            driver.execute_script("arguments[0].click();", continue_btn)
            time.sleep(4)
            print("✓ Clicked CONTINUE")
            
        except TimeoutException:
            print("✗ CONTINUE button not found")
            return
        
        # --- 4. After clicking CONTINUE, check page ---
        print("\n6. Checking page after CONTINUE click...")
        
        # Look for CALCULATE SHIPPING button
        try:
            calc_btn = driver.find_element(By.CSS_SELECTOR, 'button.get-rates')
            print(f"✓ FOUND CALCULATE SHIPPING BUTTON!")
            print(f"   Text: '{calc_btn.text}'")
            print(f"   Class: {calc_btn.get_attribute('class')}")
            
            # Check what page we're on
            current_url = driver.current_url
            print(f"   Current URL: {current_url}")
            
        except:
            print("✗ CALCULATE SHIPPING button not found after CONTINUE")
            
            # Check URL and page content
            current_url = driver.current_url
            print(f"   Current URL: {current_url}")
            
            body_text = driver.find_element(By.TAG_NAME, "body").text
            lines = body_text.split("\n")
            
            print("\n   Page content (cart/shipping related):")
            for line in lines:
                if any(kw in line.lower() for kw in ["cart", "calculate", "shipping", "address", "delivery"]):
                    print(f"      {line[:100]}")
        
        # --- 5. List all buttons on current page ---
        print("\n7. All buttons on current page:")
        buttons = driver.find_elements(By.TAG_NAME, "button")
        
        found_any = False
        for btn in buttons:
            text = btn.text.strip()
            if text and len(text) < 50:
                cls = btn.get_attribute("class") or ""
                print(f"   '{text}' | Class: {cls[:80]}")
                found_any = True
        
        if not found_any:
            print("   (No buttons with visible text found)")
        
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
    inspect_continue_flow()
