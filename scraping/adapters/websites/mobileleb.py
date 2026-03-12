import re
import json
from typing import List, Optional, Dict, Any
from urllib.parse import quote_plus, urljoin

import requests
from bs4 import BeautifulSoup

from ..base import BaseAdapter, OfferData

# Regex to match prices: 1234.56 or 1,234.56
_PRICE_RE = re.compile(r"(\d+(?:,\d{3})*(?:\.\d+)?)")

class MobileLebAdapter(BaseAdapter):
    source_name = "mobileleb"
    base_url = "https://mobileleb.com"
    
    # Store metadata for scoring
    STORE_RATING = 4.3  # Out of 5.0
    DELIVERY_DAYS = 3  # Typical delivery time in days

    def search(self, query: str, limit: int = 10, page: int = 1) -> List[OfferData]:
        # Mobileleb (Shopify) search URL
        search_url = f"{self.base_url}/search?q={quote_plus(query)}&type=product"
        if page and page > 1:
            search_url += f"&page={page}"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        }

        try:
            r = requests.get(search_url, headers=headers, timeout=25)
            r.raise_for_status()

            soup = BeautifulSoup(r.text, "lxml")
            offers: List[OfferData] = []

            # Wokiee Theme uses 'div.tt-product' for product cards
            cards = soup.select("div.tt-product")

            for card in cards:
                # 1. Extract Title
                title_el = card.select_one("h2.tt-title a")
                if not title_el:
                    # Sometimes title is in h3 in search view
                    title_el = card.select_one("h3.tt-title a")
                
                if not title_el:
                    continue

                title = title_el.get_text(" ", strip=True)
                href = title_el.get("href")
                url = urljoin(self.base_url, href)

                # 2. Extract Price
                # Mobileleb structure: <div class="tt-price"><span class="new-price">$99.00</span>...</div>
                # Or just <div class="tt-price"><span>$99.00</span></div>
                price_text = ""
                new_price_el = card.select_one(".new-price")
                if new_price_el:
                    price_text = new_price_el.get_text(strip=True)
                else:
                    # Fallback to any span inside tt-price
                    price_el = card.select_one(".tt-price")
                    if price_el:
                        price_text = price_el.get_text(strip=True)

                m = _PRICE_RE.search(price_text)
                if not m:
                    continue
                item_price = float(m.group(1).replace(',', ''))

                # 3. Extract Image
                # Mobileleb uses lazy-loaded images stored in data-optionimages JSON
                image_url = None
                
                # Try to extract from data-optionimages JSON in quickview button
                try:
                    quickview_btn = card.select_one(".tt-btn-quickview")
                    if quickview_btn and quickview_btn.get("data-optionimages"):
                        images_json = quickview_btn.get("data-optionimages")
                        images_dict = json.loads(images_json)
                        if images_dict:
                            first_image = next(iter(images_dict.values()))
                            if first_image.startswith("//"):
                                image_url = "https:" + first_image
                            else:
                                image_url = first_image
                except:
                    pass
                
                # Fallback: try img tag with data-src
                if not image_url:
                    img_el = card.select_one(".tt-img img")
                    if img_el:
                        src = img_el.get("data-src") or img_el.get("src") or img_el.get("srcset")
                        if src:
                            src = src.split(",")[0].split(" ")[0]
                            if src.startswith("//"):
                                image_url = "https:" + src
                            else:
                                image_url = src

                # 4. Extract Stock Status
                # Wokiee theme usually has a badge: <span class="tt-label-our-stock">Out of stock</span>
                # Or a specific class on the product div
                in_stock = True
                stock_badge = card.select_one(".soldout_product_badge")
                if stock_badge:
                    # If the badge exists and does NOT have 'hidden' class, it is out of stock
                    classes = stock_badge.get("class", [])
                    if "hidden" not in classes:
                        in_stock = False
                
                # Check for "Sold Out" text explicitly
                if "sold out" in card.get_text().lower():
                    in_stock = False

                offers.append(
                    OfferData(
                        source=self.source_name,
                        title=title,
                        url=url,
                        item_price=item_price,
                        currency="USD",
                        image_url=image_url,
                        in_stock=in_stock,
                    )
                )

                if len(offers) >= limit:
                    break

            return offers

        except Exception as e:
            print(f"Error searching Mobileleb: {e}")
            return []

    def get_detailed_pricing(self, product_url: str, location: str = "outside beirut") -> Dict[str, Any]:
        """
        Get detailed pricing with fixed shipping fees (no taxes).
        
        Args:
            product_url: Full URL to the product page
            location: Delivery location - "inside beirut" or "outside beirut" (default: "outside beirut")
                     Inside Beirut: $3 shipping, 1-2 days delivery
                     Outside Beirut: $5 shipping, 3-5 days delivery
        
        Returns:
            Dictionary containing:
                - item_price: Base product price
                - shipping_fee: Fixed shipping cost ($3 or $5)
                - tax_amount: Always None (no taxes)
                - total_price: item_price + shipping_fee
                - currency: Currency code (USD)
                - delivery_time: "1-2 days" for inside Beirut, "3-5 days" for outside Beirut
                - breakdown: Additional pricing details
        """
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        }
        
        try:
            # Fetch product page with simple HTTP request
            print(f"Loading product: {product_url}")
            r = requests.get(product_url, headers=headers, timeout=15)
            r.raise_for_status()
            
            soup = BeautifulSoup(r.text, "lxml")
            
            # Extract price from product page
            item_price = 0.0
            price_el = soup.select_one('.new-price, .price-item--sale, .tt-price span')
            if price_el:
                price_text = price_el.get_text(strip=True)
                m = _PRICE_RE.search(price_text)
                if m:
                    item_price = float(m.group(1).replace(',', ''))
                    print(f"✓ Product price: ${item_price}")
            
            if item_price == 0.0:
                print("⚠ Could not find price on product page")
                return {
                    "item_price": 0.0,
                    "shipping_fee": None,
                    "tax_amount": None,
                    "total_price": 0.0,
                    "currency": "USD",
                    "delivery_time": "1-2 business days",
                    "breakdown": {"error": "Could not find product price"}
                }
            
            # Apply fixed shipping fee based on location
            location_lower = location.lower().strip()
            
            if location_lower == "inside beirut":
                shipping_fee = 3.0
                delivery_time = "1-2 business days"
                print(f"✓ Inside Beirut: $3 shipping, 1-2 days delivery")
            else:
                shipping_fee = 5.0
                delivery_time = "3-5 business days"
                print(f"✓ Outside Beirut: $5 shipping, 3-5 days delivery")
            
            # No taxes for mobileleb
            tax_amount = 0.0
            total_price = item_price + shipping_fee
            
            return {
                "item_price": item_price,
                "shipping_fee": shipping_fee,
                "tax_amount": None,
                "total_price": total_price,
                "currency": "USD",
                "delivery_time": delivery_time,
                "breakdown": {
                    "subtotal": item_price,
                    "shipping": shipping_fee,
                    "tax": None,
                    "total": total_price,
                    "delivery_time": delivery_time,
                    "delivery_location": location
                }
            }
            
        except Exception as e:
            print(f"✗ Error in get_detailed_pricing: {e}")
            import traceback
            traceback.print_exc()
            return {
                "item_price": 0.0,
                "shipping_fee": None,
                "tax_amount": None,
                "total_price": 0.0,
                "currency": "USD",
                "delivery_time": "1-2 business days",
                "breakdown": {"error": str(e)}
            }