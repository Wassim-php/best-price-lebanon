"""
Inspector script to find the exact elements on Abed Tahan website
for cart view, delivery location selection, and shipping fee.

This will help us determine the correct CSS selectors.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import time

def inspect_abdeltahan():
    """
    Opens AbedTahan, adds a product to cart, and inspects the HTML/elements.
    """
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # REQUIRED for Docker
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-software-rasterizer')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    driver = None
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_page_load_timeout(30)
        
        # Find a product on search page
        print("=" * 70)
        print("STEP 1: Searching for a product...")
        print("=" * 70)
        
        driver.get("https://abedtahan.com/search?q=laptop&options[prefix]=last")
        time.sleep(3)
        
        # Find first product link
        try:
            product_link = driver.find_element(By.CSS_SELECTOR, "li.grid__item h3.card__heading a")
            product_url = product_link.get_attribute("href")
            if product_url.startswith("/"):
                product_url = "https://abedtahan.com" + product_url
            print(f"✓ Found product: {product_url}\n")
            
            driver.get(product_url)
            time.sleep(2)
        except Exception as e:
            print(f"✗ Could not find product: {e}\n")
            return
        
        # ===================== STEP 2: Inspect Add to Cart Button =====================
        print("=" * 70)
        print("STEP 2: Looking for 'ADD TO CART' button...")
        print("=" * 70)
        
        try:
            # Try different selectors
            selectors = [
                (By.NAME, "add"),
                (By.CSS_SELECTOR, "button[name='add']"),
                (By.CSS_SELECTOR, "button.add-to-cart"),
                (By.CSS_SELECTOR, "button[aria-label*='Add']"),
                (By.XPATH, "//button[contains(text(), 'Add')]"),
            ]
            
            add_btn = None
            found_selector = None
            for by, selector in selectors:
                try:
                    add_btn = driver.find_element(by, selector)
                    found_selector = (by, selector)
                    break
                except:
                    pass
            
            if add_btn:
                print(f"✓ Found with selector: {found_selector}")
                print(f"  Tag: {add_btn.tag_name}")
                print(f"  Class: {add_btn.get_attribute('class')}")
                print(f"  ID: {add_btn.get_attribute('id')}")
                print(f"  Name: {add_btn.get_attribute('name')}")
                print(f"  Text: {add_btn.text}\n")
                
                # Click it
                print("  → Clicking 'Add to Cart'...")
                driver.execute_script("arguments[0].click();", add_btn)
                time.sleep(2)
            else:
                print("✗ Could not find add to cart button\n")
                return
        except Exception as e:
            print(f"✗ Error: {e}\n")
        
        # ===================== STEP 3: Inspect Cart View Button =====================
        print("=" * 70)
        print("STEP 3: Looking for 'VIEW CART' button/link...")
        print("=" * 70)
        
        try:
            cart_selectors = [
                (By.CSS_SELECTOR, "a[href='/cart']"),
                (By.CSS_SELECTOR, "a.cart-link"),
                (By.CSS_SELECTOR, "button.cart-button"),
                (By.CSS_SELECTOR, "button[data-cart-toggle]"),
                (By.CSS_SELECTOR, ".cart-button"),
                (By.XPATH, "//a[contains(text(), 'Cart')]"),
                (By.XPATH, "//button[contains(text(), 'View')]"),
            ]
            
            cart_btn = None
            found_selector = None
            for by, selector in cart_selectors:
                try:
                    cart_btn = driver.find_element(by, selector)
                    found_selector = (by, selector)
                    break
                except:
                    pass
            
            if cart_btn:
                print(f"✓ Found with selector: {found_selector}")
                print(f"  Tag: {cart_btn.tag_name}")
                print(f"  Class: {cart_btn.get_attribute('class')}")
                print(f"  ID: {cart_btn.get_attribute('id')}")
                print(f"  Href/Data: {cart_btn.get_attribute('href') or cart_btn.get_attribute('data-cart-toggle')}")
                print(f"  Text: {cart_btn.text}\n")
                
                print("  → Clicking cart button...")
                driver.execute_script("arguments[0].click();", cart_btn)
                time.sleep(3)
            else:
                print("✗ Could not find cart view button")
                print("  → It might be in a drawer/modal that opened automatically\n")
        except Exception as e:
            print(f"✗ Error: {e}\n")
        
        # ===================== STEP 4: Inspect Delivery Location Options =====================
        print("=" * 70)
        print("STEP 4: Looking for DELIVERY LOCATION options...")
        print("(Inside Beirut / Outside Beirut)")
        print("=" * 70)
        
        try:
            # Look for radio buttons
            radios = driver.find_elements(By.CSS_SELECTOR, "input[type='radio']")
            print(f"Found {len(radios)} radio buttons on page\n")
            
            if radios:
                for i, radio in enumerate(radios[:10]):  # Show first 10
                    name = radio.get_attribute('name')
                    value = radio.get_attribute('value')
                    radio_id = radio.get_attribute('id')
                    label_text = ""
                    
                    # Try to find associated label
                    try:
                        label = driver.find_element(By.CSS_SELECTOR, f"label[for='{radio_id}']")
                        label_text = label.text
                    except:
                        pass
                    
                    print(f"  Radio {i+1}:")
                    print(f"    Name: {name}")
                    print(f"    Value: {value}")
                    print(f"    ID: {radio_id}")
                    print(f"    Label: {label_text}\n")
            else:
                print("✗ No radio buttons found")
                
                # Try select dropdowns
                selects = driver.find_elements(By.CSS_SELECTOR, "select")
                print(f"Found {len(selects)} select dropdowns\n")
                
                for i, select in enumerate(selects[:5]):
                    name = select.get_attribute('name')
                    options = select.find_elements(By.TAG_NAME, "option")
                    print(f"  Select {i+1} (name: {name}):")
                    for opt in options[:5]:
                        print(f"    - {opt.text} (value: {opt.get_attribute('value')})\n")
        except Exception as e:
            print(f"✗ Error: {e}\n")
        
        # ===================== STEP 5: Inspect Shipping Fee Display =====================
        print("=" * 70)
        print("STEP 5: Looking for SHIPPING FEE display...")
        print("=" * 70)
        
        try:
            # Look for any text containing "shipping" or "delivery"
            all_elements = driver.find_elements(By.XPATH, "//*")
            
            shipping_elements = []
            for elem in all_elements:
                try:
                    text = elem.text.lower()
                    if "shipping" in text or "delivery" in text:
                        if elem.is_displayed() and text.strip():  # Must be visible and have text
                            parent_class = elem.get_attribute('class')
                            parent_tag = elem.tag_name
                            if len(text) < 200:  # Avoid huge blocks
                                shipping_elements.append((parent_tag, parent_class, text[:100]))
                except:
                    pass
            
            if shipping_elements:
                print(f"Found {len(shipping_elements)} elements with 'shipping' or 'delivery':\n")
                for tag, cls, txt in shipping_elements[:10]:
                    print(f"  <{tag} class='{cls}'>")
                    print(f"    Text: {txt}\n")
            else:
                print("✗ No shipping-related text found yet\n")
        except Exception as e:
            print(f"✗ Error: {e}\n")
        
        # ===================== STEP 6: Full Page Dump (for debugging) =====================
        print("=" * 70)
        print("STEP 6: Current page source (first 2000 chars)...")
        print("=" * 70)
        page_source = driver.page_source
        print(page_source[:2000])
        print("\n... (truncated)")
        
        print("\n" + "=" * 70)
        print("INSPECTION COMPLETE!")
        print("=" * 70)
        print("\nBrowser is still open. Press Ctrl+C when done inspecting manually.")
        print("To inspect the page manually, use browser DevTools (F12).\n")
        
        # Keep browser open
        input("Press Enter to close browser...")
        
    except Exception as e:
        print(f"Fatal error: {e}")
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    inspect_abdeltahan()
