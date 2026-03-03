"""Test ZoodMall with Playwright to bypass Cloudflare"""

from playwright.sync_api import sync_playwright
import time

query = "samsung a56"
search_url = f"https://www.zoodmall.com.lb/en/search/?q={query.replace(' ', '%20')}"

print("=" * 70)
print("TESTING ZOODMALL WITH PLAYWRIGHT")
print("=" * 70)
print(f"\nSearch URL: {search_url}\n")

with sync_playwright() as p:
    # Launch browser
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        viewport={'width': 1920, 'height': 1080}
    )
    
    page = context.new_page()
    
    try:
        print("Loading page...")
        page.goto(search_url, wait_until='domcontentloaded', timeout=30000)
        
        # Wait for Cloudflare challenge to complete
        print("Waiting for Cloudflare challenge...")
        time.sleep(5)
        
        # Check if we're past the challenge
        page_content = page.content()
        
        if 'Just a moment' in page_content or 'challenge' in page_content.lower():
            print("⚠️  Still seeing Cloudflare challenge, waiting longer...")
            time.sleep(10)
            page_content = page.content()
        
        # Save the HTML
        with open('testers/zoodmall_playwright_page.html', 'w', encoding='utf-8') as f:
            f.write(page_content)
        print("✓ HTML saved to: testers/zoodmall_playwright_page.html")
        
        print(f"\nPage title: {page.title()}")
        print(f"Page URL: {page.url}")
        print(f"Content length: {len(page_content)} characters")
        
        # Look for product containers
        print("\n" + "=" * 70)
        print("LOOKING FOR PRODUCTS")
        print("=" * 70)
        
        # Try different selectors
        selectors_to_try = [
            '.product',
            '.product-card',
            '.product-item',
            '[data-product]',
            '.item',
            'article',
        ]
        
        for selector in selectors_to_try:
            try:
                elements = page.locator(selector).all()
                if elements and len(elements) > 2:
                    print(f"\n✓ Found {len(elements)} elements with selector: {selector}")
                    
                    # Get details of first element
                    first = elements[0]
                    print(f"  First element HTML (first 200 chars):")
                    html = first.inner_html()
                    print(f"  {html[:200]}...")
                    break
            except:
                pass
        
        # Look for links
        print("\n" + "=" * 70)
        print("LOOKING FOR PRODUCT LINKS")
        print("=" * 70)
        
        links = page.locator('a[href*="/product"]').all()
        if not links:
            links = page.locator('a[href*="/p/"]').all()
        
        if links:
            print(f"\nFound {len(links)} product links")
            for i, link in enumerate(links[:5], 1):
                href = link.get_attribute('href')
                text = link.inner_text()
                if text and len(text) > 3:
                    print(f"  {i}. {text[:50]}")
                    print(f"     {href}")
        
        # Take a screenshot for reference
        page.screenshot(path='testers/zoodmall_screenshot.png')
        print("\n✓ Screenshot saved to: testers/zoodmall_screenshot.png")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        browser.close()

print("\n" + "=" * 70)
print("DONE")
print("=" * 70)
