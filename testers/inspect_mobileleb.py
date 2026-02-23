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

def inspect_mobileleb_structure():
    """Inspect Mobileleb cart page structure to understand shipping calculation."""
    
    base_url = "https://mobileleb.com"
    search_query = "laptop"
    
    print("=" * 80)
    print("MOBILELEB CART PAGE STRUCTURE INSPECTION")
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
            print("✗ Could not find product link")
            return
        
        # --- 2. Navigate to product page ---
        print("\n2. Loading product page...")
        driver.get(product_url)
        time.sleep(2)
        print("✓ Product page loaded")
        
        # Get product title and price
        try:
            title = driver.find_element(By.CSS_SELECTOR, 'h1, .product-title').text
            print(f"   Product: {title[:60]}...")
        except:
            title = "Unknown"
        
        try:
            price_element = driver.find_element(By.CSS_SELECTOR, '.new-price, .price-item--sale, .tt-price span')
            price_text = price_element.text
            m = _PRICE_RE.search(price_text)
            if m:
                price = float(m.group(1).replace(',', ''))
                print(f"   Price: ${price}")
        except Exception as e:
            print(f"   Could not extract price: {e}")
        
        # --- 3. Add to Cart ---
        print("\n3. Adding to cart...")
        try:
            add_to_cart_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[name="add"], .btn-addtocart'))
            )
            driver.execute_script("arguments[0].click();", add_to_cart_btn)
            time.sleep(3)
            print("✓ Added to cart")
            
            # Check if a cart drawer or popup appeared
            page_text = driver.find_element(By.TAG_NAME, "body").text
            if "added to cart" in page_text.lower() or "continue shopping" in page_text.lower():
                print("   ℹ Cart notification detected")
        except Exception as e:
            print(f"✗ Could not add to cart: {e}")
            return
        
        # --- 4. Handle Cart Drawer - Press Continue ---
        print("\n4. Handling cart interaction...")
        try:
            # After adding to cart, a drawer should appear with "CONTINUE" button
            print("   Looking for CONTINUE button...")
            continue_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'CONTINUE')] | //button[contains(text(), 'Continue')]"))
            )
            print("   ✓ Found CONTINUE button")
            driver.execute_script("arguments[0].click();", continue_btn)
            time.sleep(3)
            print("   ✓ Clicked CONTINUE button")
        except TimeoutException:
            print("   ⚠ Could not find CONTINUE button")
        except Exception as e:
            print(f"   ⚠ Error with CONTINUE button: {e}")
        
        # --- 5. Navigate to Cart Page ---
        print("\n5. Navigating to cart page...")
        try:
            print("   Looking for VIEW CART button...")
            view_cart_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, '/cart')] | //button[contains(text(), 'View Cart')] | //button[contains(text(), 'VIEW CART')]"))
            )
            print("   ✓ Found VIEW CART button")
            driver.execute_script("arguments[0].click();", view_cart_btn)
            time.sleep(3)
            print("   ✓ Navigated to cart page")
        except TimeoutException:
            print("   No VIEW CART button, navigating directly to cart URL...")
            driver.get(f"{base_url}/cart")
            time.sleep(3)
            print("   ✓ Navigated to cart page via URL")
        except Exception as e:
            print(f"   ✗ Error navigating to cart: {e}")
            return
        
        # --- 5. Inspect Cart Page Structure ---
        print("\n5. Inspecting cart page structure...")
        body_text = driver.find_element(By.TAG_NAME, "body").text
        print("\n--- Cart Page Text (first 2000 chars) ---")
        print(body_text[:2000])
        print("\n")
        
        # --- 6. Look for shipping calculator ---
        print("\n6. Looking for shipping calculator...")
        page_html = driver.page_source
        
        # Look for buttons
        buttons = driver.find_elements(By.TAG_NAME, "button")
        print(f"   Found {len(buttons)} buttons on page")
        for i, btn in enumerate(buttons[:10]):
            try:
                btn_text = btn.text.strip()
                if btn_text:
                    print(f"   Button {i}: '{btn_text}'")
            except:
                pass
        
        # Look for calculator/calculate text
        if "Calculate" in page_html or "calculate" in page_html.lower():
            print("   ✓ Found 'Calculate' text on page")
        else:
            print("   - No 'Calculate' text found")
        
        if "Shipping" in page_html or "shipping" in page_html.lower():
            print("   ✓ Found 'Shipping' text on page")
        else:
            print("   - No 'Shipping' text found")
        
        # --- 7. Look for radio buttons ---
        print("\n7. Looking for shipping location radio buttons...")
        all_radios = driver.find_elements(By.CSS_SELECTOR, 'input[type="radio"]')
        print(f"   Found {len(all_radios)} radio buttons")
        
        for i, radio in enumerate(all_radios):
            try:
                # Get parent context
                parent = radio.find_element(By.XPATH, "../..")
                parent_text = parent.text
                if parent_text:
                    print(f"   Radio {i}: {parent_text[:100]}")
                    
                    # Check if it mentions beirut and has a price
                    if "beirut" in parent_text.lower() and "$" in parent_text:
                        print(f"            → SHIPPING OPTION FOUND")
            except:
                pass
        
        # --- 8. Try to click shipping calculator if exists ---
        print("\n8. Attempting to click shipping calculator...")
        try:
            # Look for button with text containing "Calculate"
            calc_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Calculate')] | //button[contains(text(), 'Shipping')]")
            calc_btn_text = calc_btn.text
            print(f"   Found button: '{calc_btn_text}'")
            driver.execute_script("arguments[0].click();", calc_btn)
            time.sleep(2)
            print("   ✓ Clicked shipping calculator")
        except NoSuchElementException:
            print("   - No shipping calculator button found")
        except Exception as e:
            print(f"   - Could not click button: {e}")
        
        # --- 9. Re-inspect after calculator click ---
        print("\n9. Cart page structure after calculator click...")
        body_text = driver.find_element(By.TAG_NAME, "body").text
        print("\n--- Updated Cart Page Text (first 2000 chars) ---")
        print(body_text[:2000])
        print("\n")
        
        # Look for radio buttons again
        all_radios = driver.find_elements(By.CSS_SELECTOR, 'input[type="radio"]')
        print(f"\n   Found {len(all_radios)} radio buttons after calculator")
        
        inside_beirut_count = 0
        outside_beirut_count = 0
        
        for i, radio in enumerate(all_radios):
            try:
                parent = radio.find_element(By.XPATH, "../..")
                parent_text = parent.text
                if parent_text:
                    print(f"   Radio {i}: {parent_text[:120]}")
                    
                    if "beirut" in parent_text.lower() and "$" in parent_text:
                        if "inside" in parent_text.lower():
                            inside_beirut_count += 1
                            print(f"            → INSIDE BEIRUT OPTION")
                        elif "outside" in parent_text.lower():
                            outside_beirut_count += 1
                            print(f"            → OUTSIDE BEIRUT OPTION")
            except:
                pass
        
        print(f"\n   Summary: Inside Beirut options: {inside_beirut_count}, Outside Beirut options: {outside_beirut_count}")
        
        # --- 10. Get full page source for analysis ---
        print("\n10. Full page HTML snapshot (cart section):")
        page_source = driver.page_source
        
        # Try to find cart total section
        if '<noscript>' not in page_source:
            cart_section_start = page_source.find('cart')
            if cart_section_start > 0:
                print(page_source[max(0, cart_section_start-200):min(len(page_source), cart_section_start+500)])
        
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
    inspect_mobileleb_structure()
