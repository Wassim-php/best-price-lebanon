"""
HiCart Adapter
Handles product search and pricing from hicart.com
Uses simple HTTP requests (no Selenium needed)
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import quote
from typing import List
import logging
import re

from ..base import BaseAdapter, OfferData

logger = logging.getLogger(__name__)


class HiCartAdapter(BaseAdapter):
    """Adapter for HiCart e-commerce site"""
    
    source_name = "HiCart"
    BASE_URL = "https://www.hicart.com"
    SEARCH_URL = f"{BASE_URL}/catalogsearch/result/?q={{}}"
    
    # Fixed pricing rules
    SHIPPING_FEE = 4.0  # Always $4
    TAX_RATE = 0.0  # No taxes
    DELIVERY_DAYS = 5  # Always 5 days
    
    # Store metadata for scoring
    STORE_RATING = 4.0  # Out of 5.0
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
        })
    
    def search(self, query: str, limit: int = 10, page: int = 1) -> List[OfferData]:
        """
        Search for products on HiCart
        Returns list of OfferData objects
        
        Args:
            query: Search query string
            limit: Maximum number of results (not used, returns all)
            page: Page number (not used, single page results)
        """
        try:
            search_url = self.SEARCH_URL.format(quote(query))
            logger.info(f"Searching HiCart: {search_url}")
            
            response = self.session.get(search_url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'lxml')
            products = []
            
            # Find product containers - HiCart uses <li> tags with class "item"
            product_items = soup.find_all('li', class_=lambda x: x and 'item' in x and 'col-xs-6' in x)
            
            logger.info(f"Found {len(product_items)} products on HiCart")
            
            for item in product_items:
                try:
                    # Extract product name and URL
                    name_elem = item.find('h2', class_='product-name')
                    if not name_elem:
                        continue
                    
                    link = name_elem.find('a')
                    if not link:
                        continue
                    
                    name = link.get_text().strip()
                    url = link.get('href', '')
                    
                    if not url.startswith('http'):
                        url = self.BASE_URL + url
                    
                    # Extract price
                    price_elem = item.find('span', class_='price')
                    if not price_elem:
                        continue
                    
                    price_text = price_elem.get_text().strip()
                    price = self._extract_price(price_text)
                    
                    if price is None:
                        logger.warning(f"Could not extract price from: {price_text}")
                        continue
                    
                    # Extract image URL
                    image_url = None
                    img_elem = item.find('img')
                    if img_elem:
                        image_url = img_elem.get('src', '')
                        if image_url and not image_url.startswith('http'):
                            image_url = self.BASE_URL + image_url
                    
                    products.append(
                        OfferData(
                            source=self.source_name,
                            title=name,
                            url=url,
                            item_price=price,
                            currency='USD',
                            in_stock=True,  # Assume in stock if listed
                            image_url=image_url,
                        )
                    )
                    
                except Exception as e:
                    logger.error(f"Error parsing HiCart product: {e}")
                    continue
            
            return products
            
        except Exception as e:
            logger.error(f"Error searching HiCart: {e}")
            return []
    
    def get_detailed_pricing(self, product_url: str, location: str = "outside beirut") -> dict:
        """
        Get detailed pricing with fixed shipping fees (no taxes).
        
        Args:
            product_url: Full URL to product page
            location: User location (not used, shipping and delivery are fixed for HiCart)
        
        Returns:
            Dictionary containing:
                - item_price: Base product price
                - shipping_fee: Always $4
                - tax_amount: Always 0 (no taxes)
                - total_price: item_price + shipping_fee
                - currency: Currency code (USD)
                - delivery_time: Always "5 days"
                - breakdown: Additional details
        """
        try:
            logger.info(f"Fetching HiCart product details: {product_url}")
            
            response = self.session.get(product_url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Extract price - try meta tag first (most reliable)
            item_price = None
            meta_price = soup.find('meta', property='product:price:amount')
            if meta_price:
                try:
                    item_price = float(meta_price.get('content', '0'))
                except (ValueError, TypeError):
                    pass
            
            # Fallback to price box
            if item_price is None:
                price_box = soup.find('div', class_='price-box')
                if price_box:
                    # Check for special price first (sale price)
                    special_price = price_box.find('span', class_='special-price')
                    if special_price:
                        price_elem = special_price.find('span', class_='price')
                    else:
                        # Regular price
                        regular_price = price_box.find('span', class_='regular-price')
                        if regular_price:
                            price_elem = regular_price.find('span', class_='price')
                        else:
                            price_elem = price_box.find('span', class_='price')
                    
                    if price_elem:
                        price_text = price_elem.get_text().strip()
                        item_price = self._extract_price(price_text)
            
            if item_price is None:
                logger.error("Could not extract product price")
                return {
                    "item_price": 0.0,
                    "shipping_fee": self.SHIPPING_FEE,
                    "tax_amount": 0.0,
                    "total_price": self.SHIPPING_FEE,
                    "currency": "USD",
                    "delivery_time": "3-7 business days",
                    "breakdown": {"error": "Could not find product price"}
                }
            
            # Extract product title
            title_elem = soup.find('h1', class_='product-name')
            if not title_elem:
                title_elem = soup.find('h1')
            title = title_elem.get_text().strip() if title_elem else "Unknown Product"
            
            # Check availability
            availability_elem = soup.find('p', class_='availability')
            in_stock = True
            if availability_elem:
                avail_text = availability_elem.get_text().strip().lower()
                in_stock = 'in stock' in avail_text
            
            # Fixed calculations - HiCart always has same shipping and delivery
            shipping_fee = self.SHIPPING_FEE  # Always $4
            tax_amount = 0.0  # No taxes
            total_price = item_price + shipping_fee
            delivery_time = "3-7 business days"  # Typical range
            
            logger.info(f"✓ HiCart pricing: ${item_price} + ${shipping_fee} shipping = ${total_price}")
            
            return {
                'item_price': item_price,
                'shipping_fee': shipping_fee,
                'tax_amount': tax_amount,
                'total_price': total_price,
                'currency': 'USD',
                'delivery_time': delivery_time,
                'breakdown': {
                    'title': title,
                    'in_stock': in_stock,
                    'url': product_url,
                    'note': 'HiCart has fixed $4 shipping, no taxes, and 5 days delivery for all locations'
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting HiCart product details: {e}")
            return {
                "item_price": 0.0,
                "shipping_fee": self.SHIPPING_FEE,
                "tax_amount": 0.0,
                "total_price": self.SHIPPING_FEE,
                "currency": "USD",
                "delivery_time": "3-7 business days",
                "breakdown": {"error": str(e)}
            }
    
    def _extract_price(self, price_text: str) -> float:
        """Extract numeric price from text like '$11.50'"""
        try:
            # Remove currency symbols and whitespace
            cleaned = re.sub(r'[^\d.,]', '', price_text)
            # Handle possible comma as decimal separator
            cleaned = cleaned.replace(',', '')
            return float(cleaned)
        except (ValueError, AttributeError):
            return None
    
    def get_source_name(self) -> str:
        """Return the name of this source"""
        return self.source_name

