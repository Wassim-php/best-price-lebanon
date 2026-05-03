"""
Scoring utilities for product comparison
"""
import math
import re
from typing import Optional


def parse_delivery_days(delivery_time: Optional[str], default: int = 7) -> int:
    """
    Parse delivery time string and extract numeric days.
    
    Examples:
        "3 days" -> 3
        "3-5 days" -> 4 (average)
        "5 business days" -> 5
        "1 week" -> 7
        None -> default (7)
    
    Args:
        delivery_time: String containing delivery time information
        default: Default value if parsing fails
        
    Returns:
        Number of delivery days as integer
    """
    if not delivery_time:
        return default
    
    delivery_time = delivery_time.lower().strip()
    
    # Normalize common delivery formats into a single numeric day value.
    week_match = re.search(r'(\d+)\s*weeks?', delivery_time)
    if week_match:
        return int(week_match.group(1)) * 7
    
    # Check for range like "3-5 days"
    range_match = re.search(r'(\d+)\s*-\s*(\d+)', delivery_time)
    if range_match:
        min_days = int(range_match.group(1))
        max_days = int(range_match.group(2))
        return math.ceil((min_days + max_days) / 2)  # Return average, rounded up
    
    # Check for single number like "3 days" or "5"
    single_match = re.search(r'(\d+)', delivery_time)
    if single_match:
        return int(single_match.group(1))
    
    return default


def calculate_product_rating(
    price: float, 
    min_price: float, 
    delivery_days: int, 
    store_stars: float
) -> dict:
    """
    Calculates an overall score out of 10 for an e-commerce product.
    
    Args:
        price: Total price of the product
        min_price: Minimum price found across all products
        delivery_days: Estimated delivery time in days
        store_stars: Store rating out of 5.0
        
    Returns:
        Dictionary containing:
            - final_score: Overall rating out of 10
            - price_score: Price component score out of 10
            - delivery_score: Delivery component score out of 10
            - trust_score: Trust component score out of 10
    """
    # Weights reflect the project ranking formula: price matters most.
    w_price = 0.50
    w_delivery = 0.20
    w_trust = 0.30

    # Safety checks prevent invalid or missing prices from ranking highly.
    if price <= 0:
        return {
            'final_score': 0.0,
            'price_score': 0.0,
            'delivery_score': 0.0,
            'trust_score': 0.0
        }
    
    if min_price <= 0:
        min_price = price
    
    # Price score: Better (lower) price = higher score
    score_price = (min_price / price) * 10
    
    # Delivery score: Drops to 0 if delivery takes 14 days or more
    score_delivery = max(0.0, 10 - (delivery_days / 1.4))
    
    # Trust score: Store rating (0-5) converted to 0-10 scale
    score_trust = store_stars * 2

    # Final weighted score, rounded for display and storage.
    final_score = (w_price * score_price) + (w_delivery * score_delivery) + (w_trust * score_trust)
    
    # Return rounded to 1 decimal place (e.g., 8.7)
    return {
        'final_score': round(final_score, 1),
        'price_score': round(score_price, 1),
        'delivery_score': round(score_delivery, 1),
        'trust_score': round(score_trust, 1)
    }
