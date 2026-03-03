"""
ZoodMall Adapter for Best Price Lebanon
Handles web scraping for zoodmall.com.lb  
Uses cloudscraper to bypass Cloudflare protection
"""

import logging
import re
import time
from typing import List, Dict, Any
from urllib.parse import quote
import cloudscraper
from bs4 import BeautifulSoup

from ..base import BaseAdapter, OfferData

logger = logging.getLogger(__name__)


class ZoodMallAdapter(BaseAdapter):
    """Adapter for ZoodMall Lebanon (zoodmall.com.lb)"""
    
    source_name = "zoodmall"
    BASE_URL = "https://www.zoodmall.com.lb"
    SEARCH_URL = BASE_URL + "/en/search/?q={}"
    
    # Shipping and delivery estimates (international shipping to Lebanon)
    SHIPPING_FEE = 5.0  # USD - estimated international shipping
    TAX_RATE = 0.0  # No additional taxes shown on site
    DELIVERY_TIME = "7-14 days"  # International shipping estimate
    
    def __init__(self):
        # Use cloudscraper with enhanced browser fingerprinting
        self.scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True,
            },
        )
        
        # Set comprehensive headers to better mimic a real browser
        self.scraper.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        })
    
    def search(self, query: str, limit: int = 10, page: int = 1) -> List[OfferData]:
        """
        Search for products on ZoodMall
        Returns list of OfferData objects
        
        Args:
            query: Search query string
            limit: Maximum number of results
            page: Page number (not used, returns first page results)
        """
        try:
            search_url = self.SEARCH_URL.format(quote(query))
            logger.info(f"Searching ZoodMall: {search_url}")
            
            # Try with retry logic for Cloudflare challenges
            max_retries = 2
            for attempt in range(max_retries):
                try:
                    response = self.scraper.get(search_url, timeout=30)
                    
                    # Check if we got Cloudflare challenge page
                    if response.status_code == 403:
                        logger.warning(f"Cloudflare 403 error (attempt {attempt + 1}/{max_retries})")
                        if attempt < max_retries - 1:
                            time.sleep(2 * (attempt + 1))  # Exponential backoff
                            continue
                        else:
                            logger.error("ZoodMall blocked by Cloudflare - requires proxy service for production")
                            return []
                    
                    response.raise_for_status()
                    break
                    
                except Exception as e:
                    if attempt < max_retries - 1:
                        logger.warning(f"Retry {attempt + 1}/{max_retries} after error: {e}")
                        time.sleep(2 * (attempt + 1))
                    else:
                        raise
            
            # Check if Cloudflare blocked us
            if 'Just a moment' in response.text or 'challenge' in response.text[:1000].lower():
                logger.error("Cloudflare challenge not bypassed - ZoodMall requires proxy service")
                return []
            
            soup = BeautifulSoup(response.text, 'lxml')
            products = []
            
            # Find product containers
            product_items = soup.find_all('div', class_='product-item-list')
            
            logger.info(f"Found {len(product_items)} products on ZoodMall")
            
            for item in product_items[:limit]:
                try:
                    # Find product link (contains title and URL)
                    link = item.find('a', class_='product-mini')
                    if not link:
                        continue
                    
                    # Extract title from link text
                    title_text = link.get_text(strip=True)
                    # Remove price info that sometimes appears in title
                    title = re.sub(r'USD\s*\d+.*$', '', title_text).strip()
                    
                    if not title or len(title) < 3:
                        continue
                    
                    # Extract URL
                    url = link.get('href', '')
                    if url.startswith('/'):
                        url = self.BASE_URL + url
                    
                    # Extract price
                    price_elem = item.find(class_='product-mini__totalLocalPrice')
                    if not price_elem:
                        logger.warning(f"Could not find price for: {title}")
                        continue
                    
                    price_text = price_elem.get_text(strip=True)
                    price = self._extract_price(price_text)
                    
                    if price is None:
                        logger.warning(f"Could not parse price from: {price_text}")
                        continue
                    
                    # Extract image URL
                    image_url = None
                    img_elem = item.find('img', src=lambda s: s and 'zoodmall' in s and 'flag' not in s.lower())
                    if img_elem:
                        image_url = img_elem.get('src', '')
                        if image_url and not image_url.startswith('http'):
                            image_url = 'https:' + image_url if image_url.startswith('//') else self.BASE_URL + image_url
                    
                    products.append(
                        OfferData(
                            source=self.source_name,
                            title=title,
                            url=url,
                            item_price=price,
                            currency='USD',
                            in_stock=True,  # Assume in stock if listed
                            image_url=image_url,
                        )
                    )
                    
                except Exception as e:
                    logger.error(f"Error parsing ZoodMall product: {e}")
                    continue
            
            return products
            
        except Exception as e:
            logger.error(f"Error searching ZoodMall: {e}")
            return []
    
    def _extract_price(self, price_text: str) -> float:
        """
        Extract numeric price from text like 'USD 409' or 'USD\n          409'
        
        Args:
            price_text: Raw price text from HTML
            
        Returns:
            Float price or None if parsing fails
        """
        try:
            # Remove currency symbols and extra whitespace
            cleaned = re.sub(r'[^\d.,]', '', price_text)
            cleaned = cleaned.strip()
            
            if not cleaned:
                return None
            
            # Handle comma as thousands separator
            cleaned = cleaned.replace(',', '')
            
            price = float(cleaned)
            return price
            
        except (ValueError, AttributeError) as e:
            logger.error(f"Failed to extract price from '{price_text}': {e}")
            return None
    
    def get_detailed_pricing(self, product_url: str, location: str = "beirut") -> Dict[str, Any]:
        """
        Get detailed pricing for a specific product.
        
        Args:
            product_url: Full URL to product page
            location: User location (not used for ZoodMall - fixed international shipping)
        
        Returns:
            Dictionary containing:
                - item_price: Base product price
                - shipping_fee: Shipping cost
                - tax_amount: Tax/customs estimate
                - total_price: Total delivered price
                - delivery_time: Estimated delivery time
                - currency: Price currency
        """
        try:
            logger.info(f"Getting detailed pricing for ZoodMall product: {product_url}")
            
            response = self.scraper.get(product_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Extract base price from product page
            # On product pages, the sale/actual price is in 'price__actual' class
            price_elem = soup.find(class_='price__actual')
            if not price_elem:
                # Fallback: try search page price selector
                price_elem = soup.find(class_='product-mini__totalLocalPrice')
            if not price_elem:
                # Final fallback: any price element
                price_elem = soup.find(class_=lambda c: c and 'price' in str(c).lower())
            
            if not price_elem:
                raise ValueError("Could not find price on product page")
            
            price_text = price_elem.get_text(strip=True)
            item_price = self._extract_price(price_text)
            
            if item_price is None:
                raise ValueError(f"Could not parse price: {price_text}")
            
            # Calculate total with fixed shipping
            shipping_fee = self.SHIPPING_FEE
            tax_amount = item_price * self.TAX_RATE
            total_price = item_price + shipping_fee + tax_amount
            
            return {
                'item_price': item_price,
                'shipping_fee': shipping_fee,
                'tax_amount': tax_amount,
                'total_price': total_price,
                'delivery_time': self.DELIVERY_TIME,
                'currency': 'USD',
            }
            
        except Exception as e:
            logger.error(f"Error getting detailed pricing from ZoodMall: {e}")
            raise
