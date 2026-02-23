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

def inspect_cart_buttons():
    """Inspect what those 21 buttons are on empty cart page."""
    
    base_url = "https://mobileleb.com"
    
    print("=" * 80)
    print("MOBILELEB EMPTY CART PAGE - BUTTON INSPECTION")
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
        
        # --- 1. Navigate directly to cart page ---
        print("\n1. Navigating to cart page...")
        driver.get(f"{base_url}/cart")
        time.sleep(5)
        print("✓ On cart page\n")
        
        # --- 2. List ALL buttons on cart page with full details ---
        print("=" * 80)
        print("ALL BUTTONS ON EMPTY CART PAGE")
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
                btn_onclick = btn.get_attribute("onclick") or ""
                btn_type = btn.get_attribute("type") or ""
                
                print(f"\n[BUTTON {i}]")
                print(f"  Text: '{btn_text}'")
                if btn_type:
                    print(f"  Type: {btn_type}")
                if btn_id:
                    print(f"  ID: {btn_id}")
                if btn_name:
                    print(f"  Name: {btn_name}")
                if btn_class:
                    print(f"  Class: {btn_class[:100]}")
                if aria_label:
                    print(f"  Aria-label: {aria_label}")
                if btn_onclick:
                    print(f"  OnClick: {btn_onclick[:100]}")
                
            except Exception as e:
                print(f"\n[BUTTON {i}] Error reading - {e}")
        
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
    inspect_cart_buttons()
