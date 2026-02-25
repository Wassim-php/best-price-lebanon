"""
Common extraction patterns for product data.
"""

import json
from typing import Optional, List, Dict, Any
from bs4 import BeautifulSoup, Tag


def extract_stock_status(
    card: Tag,
    out_of_stock_selectors: Optional[List[str]] = None,
    out_of_stock_keywords: Optional[List[str]] = None
) -> bool:
    """
    Determine if a product is in stock.
    
    Args:
        card: BeautifulSoup element containing product card
        out_of_stock_selectors: CSS selectors for out-of-stock badges
        out_of_stock_keywords: Keywords that indicate out of stock
    
    Returns:
        True if in stock, False otherwise
    """
    if out_of_stock_selectors is None:
        out_of_stock_selectors = [
            ".sold-out-badge",
            ".soldout_product_badge",
            "[class*='out-of-stock']",
            "[class*='sold-out']"
        ]
    
    if out_of_stock_keywords is None:
        out_of_stock_keywords = ["sold out", "out of stock", "unavailable"]
    
    # Check for out-of-stock badges
    for selector in out_of_stock_selectors:
        badge = card.select_one(selector)
        if badge:
            # If badge exists and is NOT hidden, product is out of stock
            classes = badge.get("class", [])
            if "hidden" not in classes:
                return False
    
    # Check for out-of-stock keywords in text
    card_text = card.get_text().lower()
    for keyword in out_of_stock_keywords:
        if keyword in card_text:
            return False
    
    return True


def extract_image_url(
    card: Tag,
    selectors: Optional[List[str]] = None,
    data_attributes: Optional[List[str]] = None
) -> Optional[str]:
    """
    Extract image URL from a product card with multiple fallback strategies.
    
    Args:
        card: BeautifulSoup element containing product card
        selectors: CSS selectors to try for finding image
        data_attributes: Data attributes to check (e.g., 'data-src', 'data-optionimages')
    
    Returns:
        Image URL or None if not found
    """
    if selectors is None:
        selectors = [
            ".card__media img",
            ".tt-img img",
            "img.search-result-image",
            "img",
        ]
    
    if data_attributes is None:
        data_attributes = ["data-src", "src", "srcset", "data-optionimages"]
    
    # Try to find image element
    img_el = None
    for selector in selectors:
        img_el = card.select_one(selector)
        if img_el:
            break
    
    if not img_el:
        return None
    
    # Try different data attributes
    for attr in data_attributes:
        value = img_el.get(attr)
        if value:
            # Special handling for JSON data (e.g., data-optionimages)
            if attr == "data-optionimages":
                try:
                    images_dict = json.loads(value)
                    if images_dict:
                        first_image = next(iter(images_dict.values()))
                        return first_image
                except (json.JSONDecodeError, StopIteration):
                    pass
            else:
                # Regular attribute - take first value from srcset or comma-separated list
                if isinstance(value, str):
                    value = value.split(",")[0].split(" ")[0]
                    return value
    
    return None


def extract_price_from_json_ld(soup: BeautifulSoup) -> Optional[float]:
    """
    Extract price from JSON-LD structured data.
    
    Args:
        soup: BeautifulSoup parsed HTML
    
    Returns:
        Price as float, or None if not found
    """
    script_tags = soup.find_all('script', type='application/ld+json')
    for script in script_tags:
        try:
            data = json.loads(script.string)
            if isinstance(data, dict) and data.get('@type') == 'Product':
                offers = data.get('offers', {})
                if isinstance(offers, dict):
                    price = offers.get('price')
                    if price:
                        return float(price)
        except (json.JSONDecodeError, ValueError, TypeError):
            continue
    return None


def extract_delivery_location_display(location: str) -> str:
    """
    Convert location parameter to display-friendly format.
    
    Args:
        location: Location string (e.g., "inside beirut", "outside beirut")
    
    Returns:
        Formatted location string
    """
    location_lower = location.lower().strip()
    
    if 'inside' in location_lower:
        return "Beirut (inside Beirut)"
    elif 'outside' in location_lower:
        return "Koura (outside Beirut)"
    else:
        return location.title()


def create_pricing_result(
    item_price: float = 0.0,
    shipping_fee: Optional[float] = None,
    tax_amount: Optional[float] = None,
    total_price: Optional[float] = None,
    currency: str = "USD",
    delivery_time: Optional[str] = None,
    breakdown: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a standardized pricing result dictionary.
    
    Args:
        item_price: Base product price
        shipping_fee: Shipping cost
        tax_amount: Tax amount
        total_price: Total price (calculated if None)
        currency: Currency code
        delivery_time: Estimated delivery time
        breakdown: Additional breakdown details
        error: Error message if any
    
    Returns:
        Standardized pricing dictionary
    """
    # Calculate total if not provided
    if total_price is None:
        total_price = item_price
        if shipping_fee is not None:
            total_price += shipping_fee
        if tax_amount is not None:
            total_price += tax_amount
    
    # Build breakdown if not provided
    if breakdown is None:
        breakdown = {}
    
    if error:
        breakdown["error"] = error
    
    return {
        "item_price": item_price,
        "shipping_fee": shipping_fee,
        "tax_amount": tax_amount,
        "total_price": total_price,
        "currency": currency,
        "delivery_time": delivery_time,
        "breakdown": breakdown
    }
