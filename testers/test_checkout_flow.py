"""
Test the actual checkout flow to verify our automation will work.
This will attempt to add a product to cart and see the checkout form.
Run from testers directory: python test_checkout_flow.py
"""
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Test product
product_url = "https://961souq.com/products/apple-iphone-15"

chrome_options = Options()
chrome_options.add_argument('--headless=new')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

driver = webdriver.Chrome(options=chrome_options)

try:
    print("1. Loading product page...")
    driver.get(product_url)
    time.sleep(3)
    
    # Try to close any popups/cookie banners
    print("2. Closing popups if any...")
    try:
        # Common close button selectors
        close_buttons = driver.find_elements(By.CSS_SELECTOR, 
            'button[aria-label="Close"], .close, .modal-close, [class*="close"], button[class*="dismiss"]')
        for btn in close_buttons:
            if btn.is_displayed():
                btn.click()
                time.sleep(1)
                print("   ✓ Closed popup")
    except:
        pass
    
    # Check for price
    print("3. Looking for price...")
    try:
        price = driver.find_element(By.CSS_SELECTOR, '.product-price')
        print(f"   ✓ Found price: {price.text}")
    except:
        print("   ✗ Could not find price")
    
    # Check for add to cart button
    print("4. Looking for add to cart button...")
    try:
        btn = driver.find_element(By.CSS_SELECTOR, '.add-to-cart-button')
        print(f"   ✓ Found button: {btn.text}")
        print(f"   Button is enabled: {btn.is_enabled()}")
        
        # Scroll to button
        driver.execute_script("arguments[0].scrollIntoView(true);", btn)
        time.sleep(1)
        
        # Try regular click first
        try:
            btn.click()
        except:
            # Fallback to JavaScript click
            print("   Regular click failed, trying JavaScript click...")
            driver.execute_script("arguments[0].click();", btn)
        
        time.sleep(3)
        print("   ✓ Clicked add to cart")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        driver.quit()
        exit()
    
    # Open cart and proceed to checkout properly
    print("5. Opening cart overlay...")
    try:
        cart_button = driver.find_element(By.CSS_SELECTOR, '.cart-button, .cart-toggle, button[aria-label*="Cart"]')
        driver.execute_script("arguments[0].click();", cart_button)
        time.sleep(2)
        print("   ✓ Opened cart")
    except Exception as e:
        print(f"   ✗ Could not open cart: {e}")
    
    print("6. Clicking 'Continue to Checkout' button...")
    try:
        checkout_btn = driver.find_element(By.CSS_SELECTOR, '.cart-checkout-button, button[aria-label*="Checkout"], .checkout-button')
        driver.execute_script("arguments[0].click();", checkout_btn)
        time.sleep(5)  # Wait longer for checkout page to load
        print("   ✓ Clicked checkout button")
    except Exception as e:
        print(f"   ✗ Could not click checkout: {e}")
    
    print(f"7. Current URL: {driver.current_url}")
    
    # Check if we're on checkout page
    if 'checkout' in driver.current_url:
        print("   ✓ On checkout page")
        
        # Save page source to inspect
        with open('checkout_page.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        print("   ✓ Saved checkout page HTML to checkout_page.html")
        
        # Look for form fields
        print("\n8. Looking for checkout form fields...")
        
        fields_to_check = [
            ("email", "Email field"),
            ("TextField0", "First name"),
            ("TextField1", "Last name"),
            ("TextField2", "Address"),
            ("TextField3", "City"),
            ("Select0", "Country"),
            ("TextField4", "Phone"),
        ]
        
        for field_id, field_name in fields_to_check:
            try:
                elem = driver.find_element(By.ID, field_id)
                print(f"   ✓ Found {field_name}: ID={field_id}, Type={elem.get_attribute('type')}")
            except:
                print(f"   ✗ {field_name} (ID={field_id}) not found")
        
        # Look for price summary elements
        print("\n9. Looking for price summary elements...")
        
        selectors_to_check = [
            ('[data-subtotal-line]', 'Subtotal'),
            ('[data-shipping-line]', 'Shipping'),
            ('[data-tax-line]', 'Tax'),
            ('[data-checkout-total-price-target]', 'Total'),
            ('.payment-due__price', 'Payment due'),
        ]
        
        for selector, name in selectors_to_check:
            try:
                elem = driver.find_element(By.CSS_SELECTOR, selector)
                print(f"   ✓ Found {name}: {elem.text}")
            except:
                print(f"   ✗ {name} ({selector}) not found")
        
    else:
        print("   ✗ Not on checkout page - might need authentication")
        print(f"   Redirected to: {driver.current_url}")
    
    print("\n✓ Inspection complete! Check checkout_page.html for details.")
    
except Exception as e:
    print(f"\n✗ Error during inspection: {e}")
    import traceback
    traceback.print_exc()
finally:
    driver.quit()
