"""
HiCart Adapter
Handles product search and pricing from hicart.com
Uses simple HTTP requests (no Selenium needed)
"""

import logging
import random
import re
from typing import List, Optional
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

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

    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    ]
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })

    def _build_headers(self, referer: Optional[str] = None) -> dict:
        headers = {
            'User-Agent': random.choice(self.USER_AGENTS),
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        if referer:
            headers['Referer'] = referer
        return headers
    
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
            
            response = self.session.get(search_url, headers=self._build_headers(), timeout=15)
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
                    
                    # Extract image URL. HiCart lazy-loads product grid images in
                    # data-src, while src may be blank or a placeholder.
                    image_url = self._extract_image_url(item)
                    
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
            
            response = self.session.get(product_url, headers=self._build_headers(referer=self.BASE_URL), timeout=15)
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

            image_url = self._extract_image_url(soup)
            
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
                    'image_url': image_url,
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

    def _extract_image_url(self, soup_or_tag) -> Optional[str]:
        """Extract the best product image URL from a HiCart HTML fragment."""
        meta_image = soup_or_tag.find('meta', property='og:image')
        if meta_image:
            image_url = self._normalize_image_url(meta_image.get('content'))
            if image_url:
                return image_url

        image_selectors = [
            'img[itemprop="image"]',
            'a.product-image img',
            '.product-image-container img',
            '#gallery img',
            'img',
        ]

        for selector in image_selectors:
            for img_elem in soup_or_tag.select(selector):
                image_url = self._image_url_from_tag(img_elem)
                if image_url:
                    return image_url

        return None

    def _image_url_from_tag(self, img_elem) -> Optional[str]:
        """Read HiCart image attributes, including lazy-load fields."""
        for attr in ('data-image', 'data-src', 'data-original', 'data-lazy', 'src'):
            image_url = self._normalize_image_url(img_elem.get(attr))
            if image_url:
                return image_url

        srcset = img_elem.get('srcset')
        if srcset:
            first_src = srcset.split(',')[0].strip().split(' ')[0]
            return self._normalize_image_url(first_src)

        return None

    def _normalize_image_url(self, image_url: Optional[str]) -> Optional[str]:
        if not image_url:
            return None

        image_url = image_url.strip()
        if not image_url or image_url.startswith('data:'):
            return None

        if image_url.startswith('//'):
            return 'https:' + image_url

        if image_url.startswith('/'):
            return self.BASE_URL + image_url

        if image_url.startswith('http'):
            return image_url

        return f"{self.BASE_URL}/{image_url.lstrip('/')}"
    
    def get_source_name(self) -> str:
        """Return the name of this source"""
        return self.source_name

