import re
from typing import Optional
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

def search_page_source():
    """Search raw HTML page source for CALCULATE SHIPPING button."""
    
    base_url = "https://mobileleb.com"
    
    print("=" * 80)
    print("MOBILELEB - PAGE SOURCE SEARCH FOR CALCULATE SHIPPING")
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
        
        # Test multiple URLs and states
        test_urls = [
            f"{base_url}/",
            f"{base_url}/cart",
            f"{base_url}/checkout",
        ]
        
        for url in test_urls:
            print(f"\n{'=' * 80}")
            print(f"URL: {url}")
            print('=' * 80)
            
            try:
                driver.get(url)
                time.sleep(3)
                
                page_source = driver.page_source
                
                # Search for button HTML
                if "get-rates" in page_source.lower():
                    print("✓ Found 'get-rates' in page source")
                    
                    # Find context around it
                    idx = page_source.lower().find("get-rates")
                    start = max(0, idx - 200)
                    end = min(len(page_source), idx + 300)
                    
                    print(f"\nContext around 'get-rates':")
                    print(page_source[start:end])
                else:
                    print("✗ 'get-rates' not found in page source")
                
                if "calculate" in page_source.lower() and "shipping" in page_source.lower():
                    print("\n✓ Found both 'calculate' and 'shipping' in page source")
                    
                    # Find CALCULATE SHIPPING sequence
                    pattern = r'<button[^>]*>'
                    buttons = re.findall(pattern, page_source)
                    
                    calc_buttons = [b for b in buttons if 'calculate' in b.lower() or 'get-rates' in b.lower()]
                    
                    if calc_buttons:
                        print(f"✓ Found {len(calc_buttons)} potential CALCULATE buttons:")
                        for btn in calc_buttons:
                            print(f"   {btn}")
                else:
                    print("✗ Missing 'calculate' or 'shipping' keywords")
                
                # Check if page has iframes
                iframes = driver.find_elements(By.TAG_NAME, "iframe")
                if iframes:
                    print(f"\n⚠ Page has {len(iframes)} iframes - button might be inside one")
                
            except Exception as e:
                print(f"✗ Error loading {url}: {e}")
        
        print("\n" + "=" * 80)
        print("SEARCH COMPLETE")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    search_page_source()
