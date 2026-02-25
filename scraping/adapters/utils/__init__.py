"""
Utility functions for website adapters.
"""

from .selenium_helpers import (
    create_chrome_driver,
    safe_click,
    wait_for_element,
    find_element_with_fallbacks,
    get_page_text,
)
from .price_helpers import (
    extract_price,
    extract_all_prices,
    PRICE_REGEX,
    clean_price_text,
    calculate_tax,
)
from .request_helpers import (
    get_default_headers,
    get_graphql_headers,
)
from .url_helpers import (
    normalize_image_url,
    build_product_url,
    build_search_url,
)
from .extraction_helpers import (
    extract_stock_status,
    extract_image_url,
    extract_price_from_json_ld,
    extract_delivery_location_display,
    create_pricing_result,
)

__all__ = [
    # Selenium helpers
    'create_chrome_driver',
    'safe_click',
    'wait_for_element',
    'find_element_with_fallbacks',
    'get_page_text',
    # Price helpers
    'extract_price',
    'extract_all_prices',
    'PRICE_REGEX',
    'clean_price_text',
    'calculate_tax',
    # Request helpers
    'get_default_headers',
    'get_graphql_headers',
    # URL helpers
    'normalize_image_url',
    'build_product_url',
    'build_search_url',
    # Extraction helpers
    'extract_stock_status',
    'extract_image_url',
    'extract_price_from_json_ld',
    'extract_delivery_location_display',
    'create_pricing_result',
]
