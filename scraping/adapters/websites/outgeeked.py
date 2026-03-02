"""
OutGeeked Adapter
Handles product search and pricing from outgeeked.net
Uses simple HTTP requests (no Selenium needed)
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import quote
from typing import List, Dict, Any
import logging
import re
import json

from ..base import BaseAdapter, OfferData

logger = logging.getLogger(__name__)


class OutGeekedAdapter(BaseAdapter):
    """Adapter for OutGeeked e-commerce site (Shopify-based)"""
    
    source_name = "OutGeeked"
    BASE_URL = "https://outgeeked.net"
    SEARCH_URL = f"{BASE_URL}/search?options%5Bprefix%5D=last&q={{}}"
    
    # Fixed pricing rules
    SHIPPING_FEE = 3.0  # Flat rate $3 for all items
    TAX_RATE = 0.0  # No taxes
    
    # Delivery times based on location
    DELIVERY_INSIDE_BEIRUT = "2-5 days"
    DELIVERY_OUTSIDE_BEIRUT = "5-7 days"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
        })
    
    def search(self, query: str, limit: int = 10, page: int = 1) -> List[OfferData]:
        """
        Search for products on OutGeeked
        Returns list of OfferData objects
        
        Args:
            query: Search query string
            limit: Maximum number of results (not strictly enforced, returns all found)
            page: Page number (not used, single page results)
        """
        try:
            search_url = self.SEARCH_URL.format(quote(query))
            logger.info(f"Searching OutGeeked: {search_url}")
            
            response = self.session.get(search_url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'lxml')
            products = []
            
            # Find the search results container first (to avoid getting recommended products)
            search_container = soup.find('div', id='ProductsList')
            
            if not search_container:
                # Fallback: try to find by class
                search_container = soup.find('div', class_=lambda c: c and 'products-list' in ' '.join(c))
            
            if not search_container:
                # If no specific container found, use the whole page
                search_container = soup
                logger.warning("Could not find ProductsList container, searching entire page")
            
            # Find product containers within the search results section only
            product_items = search_container.find_all('div', class_='product-card')
            
            logger.info(f"Found {len(product_items)} products on OutGeeked")
            
            for item in product_items:
                try:
                    # Extract product name and URL
                    # Product link is in an <a> tag with href="/products/..."
                    link = item.find('a', href=lambda h: h and '/products/' in h)
                    if not link:
                        continue
                    
                    # Get product name from aria-label or find within the card
                    name = link.get('aria-label', '').strip()
                    if not name:
                        # Try finding the product title in nested elements
                        title_elem = item.find('h3') or item.find('h2') or item.find(['div', 'span'], class_=lambda c: c and 'title' in str(c).lower())
                        if title_elem:
                            name = title_elem.get_text().strip()
                    
                    if not name or name == 'View details':
                        continue
                    
                    url = link.get('href', '')
                    if url.startswith('/'):
                        url = self.BASE_URL + url
                    
                    # Extract price
                    # Look for sale price first, then regular price
                    price_elem = item.find('span', class_='f-price-item--sale')
                    if not price_elem:
                        price_elem = item.find('span', class_='f-price-item--regular')
                    if not price_elem:
                        price_elem = item.find('span', class_='f-price-item')
                    
                    if not price_elem:
                        logger.warning(f"Could not find price for: {name}")
                        continue
                    
                    price_text = price_elem.get_text().strip()
                    price = self._extract_price(price_text)
                    
                    if price is None:
                        logger.warning(f"Could not parse price from: {price_text}")
                        continue
                    
                    # Extract image URL
                    image_url = None
                    img_elem = item.find('img')
                    if img_elem:
                        # Shopify uses data-src or src
                        image_url = img_elem.get('data-src') or img_elem.get('src', '')
                        if image_url and image_url.startswith('//'):
                            image_url = 'https:' + image_url
                    
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
                    logger.error(f"Error parsing OutGeeked product: {e}")
                    continue
            
            return products[:limit] if limit else products
            
        except Exception as e:
            logger.error(f"Error searching OutGeeked: {e}")
            return []
    
    def get_detailed_pricing(self, product_url: str, location: str = "outside beirut") -> Dict[str, Any]:
        """
        Get detailed pricing with location-based delivery times.
        
        Args:
            product_url: Full URL to product page
            location: User location - "inside beirut" or "outside beirut"
        
        Returns:
            Dictionary containing:
                - item_price: Base product price
                - shipping_fee: Always $3
                - tax_amount: Always 0 (no taxes)
                - total_price: item_price + shipping_fee
                - currency: Currency code (USD)
                - delivery_time: Based on location (2-5 days inside, 5-7 days outside Beirut)
                - breakdown: Additional details
        """
        try:
            logger.info(f"Fetching OutGeeked product details: {product_url}")
            
            response = self.session.get(product_url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Extract price from Shopify JSON metadata (most reliable)
            item_price = None
            
            # Look for ShopifyAnalytics.meta script
            script_tag = soup.find('script', string=lambda t: t and 'ShopifyAnalytics.meta' in t)
            if script_tag:
                script_content = script_tag.string
                # Extract the meta object
                match = re.search(r'var meta = ({.*?});', script_content, re.DOTALL)
                if match:
                    try:
                        meta_json = json.loads(match.group(1))
                        # Get price from first variant (prices are in cents)
                        if 'product' in meta_json and 'variants' in meta_json['product']:
                            variants = meta_json['product']['variants']
                            if variants and len(variants) > 0:
                                # Price is in cents, convert to dollars
                                price_cents = variants[0].get('price')
                                if price_cents:
                                    item_price = float(price_cents) / 100
                                    logger.info(f"✓ Extracted price from JSON: ${item_price}")
                    except (json.JSONDecodeError, KeyError, ValueError) as e:
                        logger.warning(f"Failed to parse Shopify JSON: {e}")
            
            # Fallback: Extract price from HTML
            if item_price is None:
                price_elem = soup.find('span', class_='f-price-item--sale')
                if not price_elem:
                    price_elem = soup.find('span', class_='f-price-item--regular')
                if not price_elem:
                    price_elem = soup.find('span', class_='f-price-item')
                
                if price_elem:
                    price_text = price_elem.get_text().strip()
                    item_price = self._extract_price(price_text)
                    logger.info(f"✓ Extracted price from HTML: ${item_price}")
            
            if item_price is None:
                logger.error("Could not extract product price")
                return {
                    "item_price": 0.0,
                    "shipping_fee": self.SHIPPING_FEE,
                    "tax_amount": 0.0,
                    "total_price": self.SHIPPING_FEE,
                    "currency": "USD",
                    "delivery_time": self.DELIVERY_OUTSIDE_BEIRUT,
                    "breakdown": {"error": "Could not find product price"}
                }
            
            # Extract product title
            title_elem = soup.find('h1', class_='product__title')
            if not title_elem:
                title_elem = soup.find('h1')
            title = title_elem.get_text().strip() if title_elem else "Unknown Product"
            
            # Check availability
            add_button = soup.find('button', attrs={'name': 'add'})
            in_stock = bool(add_button and 'disabled' not in add_button.get('class', []))
            
            # Fixed calculations
            shipping_fee = self.SHIPPING_FEE  # Always $3
            tax_amount = 0.0  # No taxes
            total_price = item_price + shipping_fee
            
            # Determine delivery time based on location
            location_lower = location.lower().strip()
            if 'inside' in location_lower or location_lower == 'beirut':
                delivery_time = self.DELIVERY_INSIDE_BEIRUT
            else:
                delivery_time = self.DELIVERY_OUTSIDE_BEIRUT
            
            logger.info(f"✓ OutGeeked pricing: ${item_price} + ${shipping_fee} shipping = ${total_price}, delivery: {delivery_time}")
            
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
                    'note': f'OutGeeked has flat $3 shipping. Delivery: {self.DELIVERY_INSIDE_BEIRUT} inside Beirut, {self.DELIVERY_OUTSIDE_BEIRUT} outside Beirut.'
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting OutGeeked product details: {e}")
            return {
                "item_price": 0.0,
                "shipping_fee": self.SHIPPING_FEE,
                "tax_amount": 0.0,
                "total_price": self.SHIPPING_FEE,
                "currency": "USD",
                "delivery_time": self.DELIVERY_OUTSIDE_BEIRUT,
                "breakdown": {"error": str(e)}
            }
    
    def _extract_price(self, price_text: str) -> float:
        """Extract numeric price from text like '$75.00 USD' or 'From $99.00 USD'"""
        try:
            # Remove "From", "USD", and other text, keep only digits and decimal
            cleaned = re.sub(r'[^\d.]', '', price_text)
            if cleaned:
                return float(cleaned)
            return None
        except (ValueError, AttributeError):
            return None
    
    def get_source_name(self) -> str:
        """Return the name of this source"""
        return self.source_name
