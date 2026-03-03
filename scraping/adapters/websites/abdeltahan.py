import re
from typing import List, Optional, Dict, Any
from urllib.parse import quote_plus, urljoin

import requests
from bs4 import BeautifulSoup

from ..base import BaseAdapter, OfferData

# Regex to match prices: 1234.56 or 1,234.56
_PRICE_RE = re.compile(r"(\d+(?:,\d{3})*(?:\.\d+)?)")

class AbedTahanAdapter(BaseAdapter):
        source_name = "abed_tahan"
        base_url = "https://abedtahan.com"

        def search(self, query: str, limit: int = 10, page: int = 1) -> List[OfferData]:
            # Abed Tahan Search URL structure
            search_url = f"{self.base_url}/search?q={quote_plus(query)}&options[prefix]=last"
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
                
                # Abed Tahan uses 'li.grid__item' for products
                cards = soup.select("li.grid__item")

                for card in cards:
                    # 1. Extract Title
                    title_el = card.select_one("h3.card__heading a")
                    if not title_el:
                        continue
                    title = title_el.get_text(" ", strip=True)

                    # 2. Extract Link (Relative URL)
                    href = title_el.get("href")
                    url = urljoin(self.base_url, href)

                    # 3. Extract Price
                    # Try sale price from card first (more reliable in search results)
                    price_el = card.select_one("span.card_sale_price")
                    if not price_el:
                        # Fallback to generic price-item selectors
                        price_el = card.select_one(".price-item--sale")
                    if not price_el:
                        price_el = card.select_one(".price-item--regular")
                    
                    if not price_el:
                        continue

                    raw_price = price_el.get_text(strip=True).replace("USD", "").replace("$", "").strip()
                    matches = _PRICE_RE.findall(raw_price)
                    if not matches:
                        continue
                    
                    # Take first valid price
                    item_price = 0.0
                    for match in matches:
                        price = float(match.replace(',', ''))
                        if 1 <= price <= 50000:
                            item_price = price
                            break
                    
                    if item_price == 0:
                        continue

                    # 4. Extract Image
                    img_el = card.select_one(".card__media img")
                    image_url: Optional[str] = None
                    if img_el:
                        # Abed Tahan images are often protocol-relative (//cdn.shopify...)
                        src = img_el.get("src") or img_el.get("srcset", "").split(" ")[0]
                        if src.startswith("//"):
                            image_url = "https:" + src
                        else:
                            image_url = src

                    # 5. Extract Stock Status
                    # Logic: If .sold-out-badge has 'hidden' class -> In Stock. Else -> Out of Stock.
                    in_stock = True
                    badge = card.select_one(".sold-out-badge")
                    if badge:
                        classes = badge.get("class", [])
                        if "hidden" not in classes:
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
                print(f"Error searching Abed Tahan: {e}")
                return []

        def get_detailed_pricing(self, product_url: str, location: str = "outside beirut") -> Dict[str, Any]:
            """
            Get detailed pricing with fixed shipping rules (no taxes).
            
            Args:
                product_url: Full URL to the product page
                location: Delivery location - "inside beirut" or "outside beirut" (default: "outside beirut")
            
            Shipping Rules:
                - Free shipping for orders above $350
                - $4 inside Beirut (for orders under $350)
                - $7 outside Beirut (for orders under $350)
                
            Returns:
                Dictionary containing:
                    - item_price: Base product price
                    - shipping_fee: Calculated shipping cost
                    - tax_amount: Always None (no taxes)
                    - total_price: item_price + shipping_fee
                    - currency: USD
                    - breakdown: Detailed pricing
            """
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept-Language": "en-US,en;q=0.9",
            }
            
            try:
                # Fetch product page
                print(f"Loading product: {product_url}")
                r = requests.get(product_url, headers=headers, timeout=15)
                r.raise_for_status()
                
                soup = BeautifulSoup(r.text, "lxml")
                
                # Extract price from product page
                item_price = 0.0
                
                # Method 1: Try to extract from Shopify product JSON (most reliable)
                try:
                    # Look for ShopifyAnalytics meta data which contains product info
                    for script in soup.find_all('script'):
                        if script.string and 'ShopifyAnalytics.meta' in script.string and '"product"' in script.string:
                            script_text = script.string
                            # Find the product variants array
                            import json
                            # Extract the meta object
                            if 'var meta = ' in script_text:
                                start_idx = script_text.find('var meta = ') + len('var meta = ')
                                end_idx = script_text.find('};', start_idx) + 1
                                if end_idx > start_idx:
                                    json_str = script_text[start_idx:end_idx]
                                    try:
                                        meta_data = json.loads(json_str)
                                        if 'product' in meta_data and 'variants' in meta_data['product']:
                                            variants = meta_data['product']['variants']
                                            if variants and len(variants) > 0:
                                                # Price is in cents, convert to dollars
                                                price_cents = variants[0].get('price', 0)
                                                item_price = float(price_cents) / 100
                                                print(f"✓ Product price from JSON: ${item_price}")
                                                break
                                    except json.JSONDecodeError:
                                        pass
                except Exception as e:
                    print(f"Could not extract from JSON: {e}")
                
                # Method 2: Fallback to HTML parsing if JSON method failed
                if item_price == 0.0:
                    price_selectors = [
                        'span.price-item--sale',
                        'span.price-item--regular',
                        'span.price__sale',
                        'span.price__regular',
                    ]
                    
                    for selector in price_selectors:
                        price_el = soup.select_one(selector)
                        if price_el:
                            # Get clean text and remove currency symbols
                            price_text = price_el.get_text(strip=True).replace('USD', '').replace('$', '').strip()
                            
                            # Find all numbers in the text
                            matches = _PRICE_RE.findall(price_text)
                            if matches:
                                # Take the first valid number (should be the price)
                                for match in matches:
                                    price = float(match.replace(',', ''))
                                    # Sanity check: price should be between $1 and $50,000
                                    if 1 <= price <= 50000:
                                        item_price = price
                                        print(f"✓ Product price from HTML: ${item_price} (from {selector})")
                                        break
                                if item_price > 0:
                                    break
                
                if item_price == 0.0:
                    print("⚠ Could not find price on product page")
                    return {
                        "item_price": 0.0,
                        "shipping_fee": None,
                        "tax_amount": None,
                        "total_price": 0.0,
                        "currency": "USD",
                        "breakdown": {"error": "Could not find product price"}
                    }
                
                # Apply shipping rules
                location_lower = location.lower().strip()
                
                if item_price > 350:
                    # Free shipping for orders above $350
                    shipping_fee = 0.0
                    delivery_time = "2-3 business days"
                    print(f"✓ Free shipping (order above $350)")
                elif location_lower == "inside beirut":
                    # $4 inside Beirut
                    shipping_fee = 4.0
                    delivery_time = "2-3 business days"
                    print(f"✓ Inside Beirut: $4 shipping, 2-3 business days delivery")
                else:
                    # $7 outside Beirut
                    shipping_fee = 7.0
                    delivery_time = "5-7 business days"
                    print(f"✓ Outside Beirut: $7 shipping, 5-7 business days delivery")
                
                # No taxes
                tax_amount = None
                total_price = item_price + shipping_fee
                
                return {
                    "item_price": item_price,
                    "shipping_fee": shipping_fee,
                    "tax_amount": tax_amount,
                    "total_price": total_price,
                    "currency": "USD",
                    "breakdown": {
                        "subtotal": item_price,
                        "shipping": shipping_fee,
                        "tax": tax_amount,
                        "total": total_price,
                        "delivery_location": location,
                        "delivery_time": delivery_time
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
                    "breakdown": {"error": str(e)}
                }