"""Save Samsung A56 HTML to analyze price structure"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

chrome_options = Options()
chrome_options.add_argument('--headless=new')

driver = webdriver.Chrome(options=chrome_options)

url = 'https://www.zoodmall.com.lb/en/product/35484455/samsung-galaxy-a56-ctc-256g8ram-with-one-year-warranty-gift/'
print(f"Loading: {url}")

driver.get(url)
time.sleep(8)  # Wait longer for everything to load

html = driver.page_source

# Save full HTML
with open('testers/samsung_a56_page.html', 'w', encoding='utf-8') as f:
    f.write(html)

print(f"✓ Saved to: testers/samsung_a56_page.html")
print(f"✓ HTML length: {len(html)} bytes")

# Search for price-related text
if '425' in html:
    print("✓ Found '425' in HTML")
if '375' in html:
    print("✓ Found '375' in HTML")
if 'price__actual' in html:
    print("✓ Found 'price__actual' class in HTML")
if 'price__sale' in html:
    print("✓ Found 'price__sale' class in HTML")

driver.quit()
