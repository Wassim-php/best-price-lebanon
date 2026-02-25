# Adapter Utils

This folder contains reusable utility functions to reduce code duplication across website adapters.

## Structure

```
utils/
├── __init__.py                 # Main exports
├── selenium_helpers.py         # Selenium/WebDriver utilities
├── price_helpers.py            # Price extraction and calculation
├── request_helpers.py          # HTTP request helpers
├── url_helpers.py              # URL manipulation
└── extraction_helpers.py       # Common extraction patterns
```

## Modules

### 1. `selenium_helpers.py`
Selenium WebDriver setup and common operations.

**Functions:**
- `create_chrome_driver(headless=True, timeout=30, user_agent=None)` - Create configured Chrome driver
- `safe_click(driver, element, use_js=True)` - Safely click with JS fallback
- `wait_for_element(driver, selector, by=By.CSS_SELECTOR, timeout=10, clickable=False)` - Wait for element
- `find_element_with_fallbacks(driver, selectors, by=By.CSS_SELECTOR)` - Try multiple selectors
- `scroll_to_bottom(driver, sleep_time=2)` - Scroll to bottom
- `get_page_text(driver)` - Get all page text

**Example:**
```python
from ..utils import create_chrome_driver, safe_click, wait_for_element

driver = create_chrome_driver(headless=True)
button = wait_for_element(driver, '.add-to-cart', clickable=True)
safe_click(driver, button)
```

### 2. `price_helpers.py`
Price extraction and calculations.

**Functions:**
- `PRICE_REGEX` - Compiled regex for price matching
- `clean_price_text(text)` - Remove currency symbols
- `extract_price(text, default=0.0)` - Extract single price
- `extract_all_prices(text)` - Extract all prices from text
- `find_price_in_elements(elements, default=0.0)` - Find price in web elements
- `calculate_total(item_price, shipping_fee=None, tax_amount=None)` - Calculate total
- `calculate_tax(price, tax_rate)` - Calculate tax amount

**Example:**
```python
from ..utils import extract_price, calculate_total, calculate_tax

price = extract_price("$1,234.56")  # Returns 1234.56
tax = calculate_tax(price, 0.11)     # 11% tax
total = calculate_total(price, shipping_fee=5.0, tax_amount=tax)
```

### 3. `request_helpers.py`
HTTP request configuration.

**Functions:**
- `get_default_headers(user_agent=None, accept_language="en-US,en;q=0.9", extra_headers=None)` - Standard headers
- `get_graphql_headers(token, user_agent=None, accept_language="en-US,en;q=0.9")` - GraphQL headers with auth

**Example:**
```python
from ..utils import get_default_headers

headers = get_default_headers()
r = requests.get(url, headers=headers)
```

### 4. `url_helpers.py`
URL manipulation and building.

**Functions:**
- `normalize_image_url(url, base_url="https:")` - Handle protocol-relative URLs
- `build_product_url(href, base_url)` - Build absolute URL from relative
- `build_search_url(base_url, query, page=None, search_path="/search", ...)` - Build search URL

**Example:**
```python
from ..utils import normalize_image_url, build_search_url

img_url = normalize_image_url("//cdn.example.com/img.jpg")  # Returns "https://cdn.example.com/img.jpg"
search_url = build_search_url("https://example.com", "laptop", page=2)
```

### 5. `extraction_helpers.py`
Common extraction patterns for product data.

**Functions:**
- `extract_stock_status(card, out_of_stock_selectors=None, out_of_stock_keywords=None)` - Check if in stock
- `extract_image_url(card, selectors=None, data_attributes=None)` - Extract image with fallbacks
- `extract_price_from_json_ld(soup)` - Get price from JSON-LD
- `extract_delivery_location_display(location)` - Format location string
- `create_pricing_result(item_price, shipping_fee, tax_amount, ...)` - Create standardized pricing dict

**Example:**
```python
from ..utils import extract_stock_status, extract_image_url, create_pricing_result

in_stock = extract_stock_status(product_card)
image_url = extract_image_url(product_card)

result = create_pricing_result(
    item_price=100.0,
    shipping_fee=5.0,
    tax_amount=11.0,
    delivery_time="2-5 days"
)
```

## Benefits

### Before (Repetitive Code)
```python
import re
from urllib.parse import quote_plus, urljoin
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

_PRICE_RE = re.compile(r"(\d+(?:,\d{3})*(?:\.\d+)?)")

chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
# ... 10+ lines of repeated setup ...

raw_price = price_el.get_text()
raw_price = raw_price.replace("USD", "").replace("$", "")
m = _PRICE_RE.search(raw_price)
if m:
    item_price = float(m.group(1).replace(',', ''))
```

### After (Clean & Reusable)
```python
from ..utils import create_chrome_driver, extract_price

driver = create_chrome_driver(headless=True)
item_price = extract_price(price_el.get_text())
```

## Migration Guide

### Step 1: Import Utils
```python
from ..utils import (
    create_chrome_driver,
    extract_price,
    get_default_headers,
    build_search_url,
    safe_click,
    wait_for_element,
    create_pricing_result,
)
```

### Step 2: Replace Repetitive Code

**Selenium setup:**
```python
# Before
chrome_options = Options()
chrome_options.add_argument('--headless')
# ... many lines ...
driver = webdriver.Chrome(service=service, options=chrome_options)

# After
driver = create_chrome_driver(headless=True)
```

**Price extraction:**
```python
# Before
raw_price = elem.text.replace("USD", "").replace("$", "")
m = _PRICE_RE.search(raw_price)
item_price = float(m.group(1).replace(',', '')) if m else 0.0

# After
item_price = extract_price(elem.text)
```

**Search URL:**
```python
# Before
search_url = f"{self.base_url}/search?q={quote_plus(query)}"
if page > 1:
    search_url += f"&page={page}"

# After
search_url = build_search_url(self.base_url, query, page)
```

## Adding New Utilities

When you find repetitive patterns:

1. Add the function to the appropriate helper module
2. Export it in `__init__.py`
3. Add documentation and examples
4. Update this README

## Dynamic Features

The utils are designed to be flexible:

- **Configurable selectors**: Pass custom selectors as parameters
- **Fallback strategies**: Multiple selectors tried in order
- **Optional parameters**: Sensible defaults with override options
- **Error handling**: Safe operations with graceful degradation
- **Type hints**: Better IDE support and code clarity

## Example: Full Adapter Refactor

See `REFACTORING_EXAMPLE.py` for a complete example of refactoring an adapter using these utils.
