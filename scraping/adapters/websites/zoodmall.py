"""
ZoodMall Adapter using Selenium for Cloudflare bypass
Handles web scraping for zoodmall.com.lb  
"""

import logging
import re
import time
from typing import List, Dict, Any
from urllib.parse import quote

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

from ..base import BaseAdapter, OfferData

logger = logging.getLogger(__name__)


class ZoodMallAdapter(BaseAdapter):
    """Adapter for ZoodMall Lebanon using Selenium to bypass Cloudflare"""
    
    source_name = "zoodmall"
    BASE_URL = "https://www.zoodmall.com.lb"
    
    # Store metadata for scoring
    STORE_RATING = 3  # Out of 5.0
    DELIVERY_DAYS = 5  # Typical delivery time in days
    SEARCH_URL = BASE_URL + "/en/search/?q={}"
    
    # Shipping and delivery estimates
    SHIPPING_FEE = 4.75  # USD - door delivery to Lebanon
    TAX_RATE = 0.0  # No additional taxes
    DELIVERY_TIME = "2-7 business days"  # Typical delivery time (Mar 4-9 from Mar 2)
    
    def __init__(self):
        """Initialize adapter with Selenium driver"""
        self.driver = None
        # self._init_driver()

    def _ensure_driver(self):
        """Lazy-load the driver only when needed"""
        if self.driver is None:
            self._init_driver()    
    
    def _init_driver(self):
        """Initialize Chrome WebDriver with anti-detection settings"""
        if self.driver:
            return
        
        chrome_options = Options()
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Add options for Docker environment
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-software-rasterizer')
        chrome_options.add_argument('--remote-debugging-port=9222')
        
        try:
            # Try to use system chromedriver first (Docker), fallback to webdriver-manager (local)
            try:
                # Docker environment - use installed chromedriver
                service = Service('/usr/local/bin/chromedriver')
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                logger.info("Chrome driver initialized with system chromedriver")
            except Exception as e:
                # Local environment - use webdriver-manager
                logger.info(f"System chromedriver not found, using webdriver-manager: {e}")
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                logger.info("Chrome driver initialized with webdriver-manager")
            
            # Remove webdriver property
            self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': '''
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    })
                '''
            })
        except Exception as e:
            logger.error(f"Failed to initialize Chrome driver: {e}")
            raise
    
    def _get_page_html(self, url: str, wait_for_selector: str = None, timeout: int = 30) -> str:
        """
        Load a page with Selenium and return HTML
        
        Args:
            url: URL to load
            wait_for_selector: CSS selector to wait for (optional)
            timeout: Maximum wait time in seconds
        """
        self._ensure_driver()
        try:
            self.driver.get(url)
            
            # Wait for Cloudflare check and JavaScript to load products
            if wait_for_selector:
                WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, wait_for_selector))
                )
            else:
                # Wait for page to fully load with JavaScript
                time.sleep(8)  # Give time for JS to render products
            
            return self.driver.page_source
        except Exception as e:
            logger.error(f"Error loading page {url}: {e}")
            return ""
    
    def search(self, query: str, limit: int = 10, page: int = 1) -> List[OfferData]:
        """
        Search for products on ZoodMall using Selenium
        
        Args:
            query: Search query string
            limit: Maximum number of results
            page: Page number (not used, returns first page results)
        """
        self._ensure_driver()
        try:
            search_url = self.SEARCH_URL.format(quote(query))
            logger.info(f"Searching ZoodMall with Selenium: {search_url}")
            
            # Load page
            self.driver.get(search_url)
            
            # Wait for product cards to load (JavaScript-rendered)
            try:
                WebDriverWait(self.driver, 30).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "a.product-mini, div.product-card, div[class*='product']"))
                )
                # Extra wait for all products to render
                time.sleep(3)
            except:
                logger.warning("Timeout waiting for products to load")
                # Continue anyway, maybe some products loaded
            
            # Get page HTML after JavaScript execution
            html = self.driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            
            # Try multiple selectors for product cards
            product_cards = soup.find_all('a', class_='product-mini', limit=limit * 2)
            
            if not product_cards:
                product_cards = soup.find_all('div', class_='product-card', limit=limit * 2)
            
            if not product_cards:
                # Fallback: find any div with "product" in class name
                product_cards = soup.find_all('div', class_=lambda c: c and 'product' in c.lower(), limit=limit * 2)
            
            if not product_cards:
                logger.warning(f"No products found for query: {query}")
                return []
            
            logger.info(f"Found {len(product_cards)} product cards")
            
            offers = []
            for card in product_cards[:limit]:
                try:
                    offer = self._parse_product_card(card)
                    if offer:
                        offers.append(offer)
                except Exception as e:
                    logger.error(f"Error parsing product card: {e}")
                    continue
            
            logger.info(f"Found {len(offers)} products on ZoodMall")
            return offers
            
        except Exception as e:
            logger.error(f"Error searching ZoodMall: {e}")
            return []
    
    def _parse_product_card(self, card) -> OfferData:
        """Parse a product card and extract offer data"""
        try:
            # Extract URL
            product_url = ''
            if card.name == 'a':
                product_url = card.get('href', '')
            else:
                link = card.find('a')
                if link:
                    product_url = link.get('href', '')
            
            if product_url and not product_url.startswith('http'):
                product_url = self.BASE_URL + product_url
            
            # Extract title from product-mini__title div
            title = ''
            title_elem = card.find('div', class_='product-mini__title')
            if title_elem:
                title = title_elem.get_text(strip=True)
            
            # Extract price from product-mini__totalLocalPrice
            price = self._extract_price(card)
            
            # Extract image
            img_tag = card.find('img')
            image_url = ''
            if img_tag:
                image_url = img_tag.get('src', img_tag.get('data-src', ''))
            if image_url and not image_url.startswith('http'):
                image_url = self.BASE_URL + image_url
            
            # Need at least title and price
            if not title or not price:
                return None
            
            return OfferData(
                source=self.source_name,
                title=title,
                url=product_url,
                item_price=float(price),
                currency="USD",
                image_url=image_url,
                in_stock=True,
            )
        except Exception as e:
            logger.error(f"Error parsing product card: {e}")
            return None
    
    def _extract_price(self, container) -> float:
        """Extract price from product container, avoiding crossed-out prices"""
        try:
            # ZoodMall uses product-mini__totalLocalPrice class on search pages
            price_elem = container.find(class_='product-mini__totalLocalPrice')
            
            if not price_elem:
                # On detail pages, look for price__un_sale (current price, not crossed out)
                # Don't specify tag - ZoodMall uses div on detail pages, span on search pages
                price_elem = container.find(class_='price__un_sale')
            
            if not price_elem:
                # Try price__actual but avoid price__sale (crossed out)
                price_actual = container.find(class_='price__actual')
                if price_actual and 'price__sale' not in price_actual.get('class', []):
                    price_elem = price_actual
            
            if not price_elem:
                # Fallback selectors
                price_elem = container.find('span', class_='product-price')
            if not price_elem:
                price_elem = container.find('div', class_='price')
            
            if price_elem:
                # Get text and extract price (format: "USD\n 75")
                price_text = price_elem.get_text(strip=True)
                # Remove currency and extract number
                price_text = price_text.replace('USD', '').replace('$', '').strip()
                # Extract numeric value
                match = re.search(r'[\d,]+\.?\d*', price_text.replace(',', ''))
                if match:
                    return float(match.group())
            
            return 0.0
        except Exception as e:
            logger.error(f"Error extracting price: {e}")
            return 0.0
    
    def get_detailed_pricing(self, product_url: str, location: str = "outside beirut") -> Dict[str, Any]:
        """
        Get detailed pricing for a specific product
        
        Args:
            product_url: Full URL to the product page
            location: Delivery location (not used for ZoodMall - international shipping)
        """
        self._ensure_driver()
        try:
            logger.info(f"Getting detailed pricing for: {product_url}")
            
            # Load productpage
            self.driver.get(product_url)
            
            # Wait for price to load - try multiple strategies
            try:
                # Wait for any price-related element to appear
                WebDriverWait(self.driver, 30).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "[class*='price']"))
                )
                # Extra wait for JavaScript to fully render all prices
                time.sleep(5)
            except:
                logger.warning("Timeout waiting for price elements to load, continuing anyway")
                time.sleep(3)  # Wait a bit anyway
            
            html = self.driver.page_source
            
            if not html:
                return self._default_pricing()
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract price - prioritize actual sale price, not crossed-out price
            base_price = 0.0
            price_elem = None
            
            # Try price__un_sale first (the actual current price, not crossed out)
            # Note: ZoodMall uses DIV not SPAN for price elements on detail pages
            price_elem = soup.find(class_='price__un_sale')  # Don't specify tag - could be div or span
            if price_elem:
                logger.info(f"Found price via price__un_sale")
            
            # If not found try price__actual (but check it's not also price__sale)
            if not price_elem:
                price_actual = soup.find(class_='price__actual')  # Don't specify tag
                # Make sure it doesn't also have price__sale class (crossed out)
                if price_actual:
                    classes = price_actual.get('class', [])
                    logger.info(f"Found price__actual with classes: {classes}")
                    if 'price__sale' not in classes:
                        price_elem = price_actual
                    else:
                        logger.info(f"Skipping price__actual because it has price__sale (crossed out)")
            
            # Fallback to product-price container and get the last price (usually the sale price)
            if not price_elem:
                logger.info(f"Trying fallback: looking in product-price container")
                product_price_div = soup.find('div', class_='product-price')
                if product_price_div:
                    # Find all price divs/spans and get the one with price__un_sale class
                    all_price_elems = product_price_div.find_all(class_=lambda x: x and 'price' in str(x).lower())
                    logger.info(f"Found {len(all_price_elems)} price elements in product-price div")
                    # Try to find price__un_sale first
                    for elem in all_price_elems:
                        if 'price__un_sale' in elem.get('class', []):
                            price_elem = elem
                            logger.info(f"Found price__un_sale in fallback")
                            break
                    # If still not found, get the last element
                    if not price_elem and all_price_elems:
                        price_elem = all_price_elems[-1]
                        logger.info(f"Using last price element as fallback")
            
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                # Remove currency symbols and whitespace
                price_text = price_text.replace('USD', '').replace('$', '').strip()
                # Extract numeric value (handles formats like "USD 75" or "USD\n              75")
                match = re.search(r'([\d,]+\.?\d*)', price_text.replace(',', ''))
                if match:
                    base_price = float(match.group(1))
                    logger.info(f"✓ Extracted price: ${base_price}, classes: {price_elem.get('class')}")
            else:
                # Try to reuse _extract_price with the whole page
                base_price = self._extract_price(soup)
                logger.info(f"Used _extract_price fallback: {base_price}")
            
            # Extract title
            title_elem = soup.find('h1', class_='product-title')
            if not title_elem:
                title_elem = soup.find('div', class_='product-name')
            title = title_elem.get_text(strip=True) if title_elem else "Product"
            
            # Extract image
            img_elem = soup.find('img', class_='product-image')
            if not img_elem:
                img_elem = soup.find('img')
            image_url = img_elem.get('src', '') if img_elem else ''
            if image_url and not image_url.startswith('http'):
                image_url = self.BASE_URL + image_url
            
            return {
                'base_price': base_price,
                'shipping_fee': self.SHIPPING_FEE,
                'tax': self.TAX_RATE,
                'total_price': base_price + self.SHIPPING_FEE,
                'delivery_time': self.DELIVERY_TIME,
                'product_url': product_url,
                'image_url': image_url,
                'title': title
            }
            
        except Exception as e:
            logger.error(f"Error getting detailed pricing: {e}")
            return self._default_pricing()
    
    def _default_pricing(self) -> Dict[str, Any]:
        """Return default pricing structure"""
        return {
            'base_price': 0.0,
            'shipping_fee': self.SHIPPING_FEE,
            'tax': self.TAX_RATE,
            'total_price': self.SHIPPING_FEE,
            'delivery_time': self.DELIVERY_TIME,
            'product_url': '',
            'image_url': '',
            'title': 'Product'
        }
    
    def __del__(self):
        """Cleanup: quit driver when object is destroyed"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Chrome driver closed")
            except Exception as e:
                logger.error(f"Error closing driver: {e}")
