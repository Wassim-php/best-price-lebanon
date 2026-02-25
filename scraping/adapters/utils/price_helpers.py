"""
Price extraction and parsing helpers.
"""

import re
from typing import Optional, List


# Regex to match prices: 1234.56 or 1,234.56
PRICE_REGEX = re.compile(r"(\d+(?:,\d{3})*(?:\.\d+)?)")


def clean_price_text(text: str) -> str:
    """
    Clean price text by removing currency symbols and extra whitespace.
    
    Args:
        text: Raw price text
    
    Returns:
        Cleaned text with only numbers, commas, and decimal points
    """
    # Remove common currency symbols
    cleaned = text.replace("USD", "").replace("$", "").replace("€", "").replace("£", "")
    # Remove extra whitespace
    cleaned = cleaned.strip()
    return cleaned


def extract_price(text: str, default: float = 0.0) -> float:
    """
    Extract a price from text using regex.
    
    Args:
        text: Text containing price
        default: Default value if price not found
    
    Returns:
        Extracted price as float
    """
    cleaned = clean_price_text(text)
    match = PRICE_REGEX.search(cleaned)
    if match:
        return float(match.group(1).replace(',', ''))
    return default


def extract_all_prices(text: str) -> List[float]:
    """
    Extract all prices from text.
    
    Args:
        text: Text containing prices
    
    Returns:
        List of extracted prices
    """
    cleaned = clean_price_text(text)
    matches = PRICE_REGEX.findall(cleaned)
    return [float(match.replace(',', '')) for match in matches]


def find_price_in_elements(elements, default: float = 0.0) -> Optional[float]:
    """
    Find first valid price in a list of web elements.
    
    Args:
        elements: List of web elements to check
        default: Default value if no price found
    
    Returns:
        First found price or default
    """
    for elem in elements:
        try:
            if elem.is_displayed():
                text = elem.text.strip()
                if text and '$' in text:
                    price = extract_price(text)
                    if price > 0:
                        return price
        except Exception:
            continue
    return default


def calculate_total(
    item_price: float,
    shipping_fee: Optional[float] = None,
    tax_amount: Optional[float] = None
) -> float:
    """
    Calculate total price from components.
    
    Args:
        item_price: Base item price
        shipping_fee: Shipping cost (optional)
        tax_amount: Tax amount (optional)
    
    Returns:
        Total price
    """
    total = item_price
    if shipping_fee is not None:
        total += shipping_fee
    if tax_amount is not None:
        total += tax_amount
    return round(total, 2)


def calculate_tax(price: float, tax_rate: float) -> float:
    """
    Calculate tax amount from price and tax rate.
    
    Args:
        price: Base price
        tax_rate: Tax rate (e.g., 0.11 for 11%)
    
    Returns:
        Tax amount
    """
    return round(price * tax_rate, 2)
