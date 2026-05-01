import re
import logging
from typing import List, Optional, Dict, Any
from urllib.parse import quote_plus, urljoin

import requests
from bs4 import BeautifulSoup

from ..base import BaseAdapter, OfferData

logger = logging.getLogger(__name__)

# Regex to match prices
_PRICE_RE = re.compile(r"(\d+(?:,\d{3})*(?:\.\d+)?)")


class BeytechAdapter(BaseAdapter):
    """Adapter for Beytech Lebanon (beytech.com.lb) - WordPress/WooCommerce"""
    
    source_name = "beytech"
    base_url = "https://www.beytech.com.lb"
    
    # Store metadata for scoring
    STORE_RATING = 4.5  # Out of 5.0
    DELIVERY_DAYS = 2   # Typical delivery time in days
    
    # Shipping and delivery estimates
    SHIPPING_FEE = 5.0  # USD - flat delivery fee across all Lebanon
    TAX_RATE = 0.0      # No additional taxes
    DELIVERY_TIME = "2-3 business days"
    
    def search(self, query: str, limit: int = 10, page: int = 1) -> List[OfferData]:
        """
        Search for products on Beytech using WordPress search
        
        Args:
            query: Search query string
            limit: Maximum number of results
            page: Page number
        """
        try:
            # Beytech uses WordPress search: /?s=query
            search_url = f"{self.base_url}/?s={quote_plus(query)}"
            if page and page > 1:
                search_url += f"&paged={page}"
            
            logger.info(f"Searching Beytech: {search_url}")
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept-Language": "en-US,en;q=0.9",
            }
            
            r = requests.get(search_url, headers=headers, timeout=25)
            r.raise_for_status()
            
            soup = BeautifulSoup(r.text, "html.parser")
            offers: List[OfferData] = []
            
            # WordPress/WooCommerce search results - product articles
            product_cards = soup.select("article.product")
            
            logger.info(f"Found {len(product_cards)} product cards")
            
            for card in product_cards:
                try:
                    offer = self._parse_product_card(card, headers=headers)
                    if offer:
                        offers.append(offer)
                        if len(offers) >= limit:
                            break
                except Exception as e:
                    logger.error(f"Error parsing product card: {e}")
                    continue
            
            logger.info(f"Found {len(offers)} products from Beytech")
            return offers
        
        except Exception as e:
            logger.error(f"Error searching Beytech: {e}")
            return []
    
    def _parse_product_card(self, card, headers: Dict[str, str]) -> Optional[OfferData]:
        """Parse a WordPress/WooCommerce product card"""
        try:
            # Extract product URL
            url = ""
            link = card.select_one("a")
            
            if link:
                url = link.get("href", "")
                if url and not url.startswith("http"):
                    url = urljoin(self.base_url, url)
            
            if not url:
                logger.debug("No URL found in card")
                return None
            
            # Extract title
            title = ""
            title_link = card.select_one("h2 a") or card.select_one("a")
            
            if title_link:
                title = title_link.get_text(strip=True)
            
            if not title or len(title) < 3:
                logger.debug("No valid title found")
                return None
            
            # Extract image
            image_url = ""
            img = card.select_one("img.wp-post-image") or card.select_one("img")
            
            if img:
                image_url = img.get("src") or img.get("data-src") or ""
                if image_url and not image_url.startswith("http"):
                    image_url = urljoin(self.base_url, image_url)
            
            # Fetch the product page to get the price (not on search page)
            price = self._fetch_product_price(url, headers)
            
            if price is None or price <= 0:
                logger.debug(f"No valid price for {title}")
                return None
            
            return OfferData(
                source=self.source_name,
                title=title,
                url=url,
                item_price=float(price),
                currency="USD",
                image_url=image_url,
                in_stock=True,
            )
        
        except Exception as e:
            logger.error(f"Error parsing product card: {e}")
            return None
    
    def _fetch_product_price(self, product_url: str, headers: Dict[str, str]) -> Optional[float]:
        """
        Fetch price from product page.
        Note: Beytech doesn't show prices on search results, only on product pages.
        """
        try:
            r = requests.get(product_url, headers=headers, timeout=15)
            soup = BeautifulSoup(r.text, "html.parser")
            
            # Look for the main product price in the main product section
            # Try to find the primary product price container first
            product_summary = soup.select_one(".product-summary") or soup.select_one(".summary") or soup.select_one(".product")
            
            if product_summary:
                # Look for price class elements within the summary (these are main product prices)
                price_elem = product_summary.select_one(".price")
                
                if price_elem:
                    # The structure is usually "Original price was: X. Current price is: Y."
                    # We want the current price (last number)
                    price_text = price_elem.get_text(strip=True)
                    
                    # Extract all numbers from the text
                    matches = _PRICE_RE.findall(price_text)
                    if matches:
                        # Use the last price (current price)
                        return float(matches[-1].replace(",", ""))
            
            # Fallback: look for woocommerce price in the product area
            # But filter out sidebar/related products by looking in main content
            main_content = soup.select_one(".woocommerce-notices-wrapper") or soup.select_one("main") or soup.select_one("[role='main']")
            
            if main_content:
                # Get price elements from main content
                price_elems = main_content.select(".woocommerce-Price-amount.amount")
                
                # The first price element in main content should be the product price
                if price_elems:
                    price_text = price_elems[0].get_text(strip=True)
                    price_text = price_text.replace("USD", "").replace("$", "").strip()
                    match = _PRICE_RE.search(price_text)
                    if match:
                        return float(match.group(1).replace(",", ""))
            
            return None
        
        except Exception as e:
            logger.error(f"Error fetching product price: {e}")
            return None
    
    def get_detailed_pricing(self, product_url: str, location: str = "outside beirut") -> Dict[str, Any]:
        """
        Get detailed pricing for a Beytech product
        
        Args:
            product_url: Full URL to the product page
            location: Delivery location (not used - flat $5 fee for all)
        
        Returns:
            Dict with pricing details
        """
        try:
            logger.info(f"Getting detailed pricing for: {product_url}")
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept-Language": "en-US,en;q=0.9",
            }
            
            r = requests.get(product_url, headers=headers, timeout=25)
            r.raise_for_status()
            
            soup = BeautifulSoup(r.text, "html.parser")
            
            # Extract base price - use same logic as _fetch_product_price
            base_price = 0.0
            
            # Try main product section first
            product_summary = soup.select_one(".product-summary") or soup.select_one(".summary") or soup.select_one(".product")
            
            if product_summary:
                price_elem = product_summary.select_one(".price")
                
                if price_elem:
                    price_text = price_elem.get_text(strip=True)
                    matches = _PRICE_RE.findall(price_text)
                    if matches:
                        base_price = float(matches[-1].replace(",", ""))
            
            # Fallback to woocommerce price
            if base_price == 0.0:
                main_content = soup.select_one(".woocommerce-notices-wrapper") or soup.select_one("main") or soup.select_one("[role='main']")
                
                if main_content:
                    price_elems = main_content.select(".woocommerce-Price-amount.amount")
                    if price_elems:
                        price_text = price_elems[0].get_text(strip=True)
                        price_text = price_text.replace("USD", "").replace("$", "").strip()
                        match = _PRICE_RE.search(price_text)
                        if match:
                            base_price = float(match.group(1).replace(",", ""))
            
            # Extract title
            title = ""
            title_elem = soup.select_one("h1.product-title") or soup.select_one("h1")
            if title_elem:
                title = title_elem.get_text(strip=True)
            
            # Extract image
            image_url = ""
            img = soup.select_one("img.wp-post-image") or soup.select_one("img[class*='product-image']")
            if img:
                image_url = img.get("src") or img.get("data-src") or ""
                if image_url and not image_url.startswith("http"):
                    image_url = urljoin(self.base_url, image_url)
            
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
