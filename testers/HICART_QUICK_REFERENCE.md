# HiCart Adapter - Quick Reference

## API Usage

### 1. Search for Products
```bash
curl -X POST http://localhost:8000/api/search/hicart \
  -H "Content-Type: application/json" \
  -d '{"query": "iphone"}'
```

**Response**:
```json
{
  "id": 123,
  "query": "iphone",
  "source": "hicart",
  "status": "DONE",
  "offers": [
    {
      "id": 1,
      "title": "Ultra-Thin iPhone Case 0.3mm",
      "url": "https://www.hicart.com/...",
      "image_url": "https://media.hicart.com/...",
      "item_price": "11.50",
      "currency": "USD",
      "in_stock": true
    }
  ]
}
```

### 2. Get Product Details with Pricing
```bash
curl -X POST http://localhost:8000/api/product-details/hicart \
  -H "Content-Type: application/json" \
  -d '{
    "product_url": "https://www.hicart.com/product-url",
    "location": "Beirut"
  }'
```

**Response**:
```json
{
  "item_price": 165.0,
  "shipping_fee": 4.0,
  "tax_amount": 0.0,
  "total_price": 169.0,
  "currency": "USD",
  "delivery_time": "5 days",
  "breakdown": {
    "title": "Product Name",
    "in_stock": true,
    "url": "...",
    "note": "HiCart has fixed $4 shipping, no taxes, and 5 days delivery for all locations"
  }
}
```

## Python Usage

### Direct Adapter Usage
```python
from scraping.adapters.websites.hicart import HiCartAdapter

adapter = HiCartAdapter()

# Search
results = adapter.search("iphone", limit=10)
for product in results:
    print(f"{product.title}: ${product.item_price}")

# Get Details
details = adapter.get_detailed_pricing(
    "https://www.hicart.com/product-url",
    location="Beirut"
)
print(f"Total: ${details['total_price']}")
```

### Via Registry
```python
from scraping.registry import ADAPTERS

hicart = ADAPTERS['hicart']
results = hicart.search("laptop")
```

## Pricing Rules

| Item | Value | Note |
|------|-------|------|
| **Shipping** | $4.00 | Fixed for all locations |
| **Taxes** | $0.00 | No taxes applied |
| **Delivery** | 5 days | Fixed delivery time |
| **Currency** | USD | All prices in US Dollars |

**Formula**: `Total = Item Price + $4.00`

## Supported Locations
All locations have the same pricing:
- Beirut
- Tripoli
- Sidon
- Zahle
- Any other location

## Testing

Run comprehensive tests:
```bash
python testers/test_hicart_comprehensive.py
```

## Troubleshooting

### Common Issues

**No products found**
- Check if HiCart website is accessible
- Verify search query is valid
- Check network connectivity

**Price extraction fails**
- Product page might have changed structure
- Check if meta tag `product:price:amount` exists
- Fallback to price-box extraction

**Timeout errors**
- Increase timeout in adapter (default: 15 seconds)
- Check network speed
- Website might be slow/down

## Implementation Notes

### Why No Selenium?
HiCart uses Magento, which renders product data server-side (no JavaScript required for product listings). This allows simple HTTP requests with BeautifulSoup, which is:
- **10x faster** than Selenium
- **Lower resource usage**
- **More reliable** (no browser dependencies)

### Price Extraction Strategy
1. **Primary**: Meta tag `<meta property="product:price:amount">`
2. **Fallback**: Parse HTML price-box with special-price → regular-price → generic price
3. **Validation**: Convert to float, ensure positive value

### Error Handling
- Returns empty list on search failure
- Returns error breakdown on detail fetch failure
- Logs all errors with context
- Never crashes the application

## Maintenance

### If HiCart Changes Structure

1. **Search results**: Update selector from `li.item.col-xs-6` in line ~53
2. **Product name**: Update `h2.product-name > a` selector in line ~58
3. **Price**: Update `span.price` selector in line ~75
4. **Product page**: Update meta/price-box selectors in lines ~145-165

### Adding New Features

To add stock checking:
```python
# In get_detailed_pricing method
stock_elem = soup.find('button', class_='tocart')
in_stock = bool(stock_elem and 'disabled' not in stock_elem.get('class', []))
```

## Related Files

- **Adapter**: `scraping/adapters/websites/hicart.py`
- **Registry**: `scraping/registry.py`
- **Tests**: `testers/test_hicart_*.py`
- **Documentation**: `testers/HICART_IMPLEMENTATION.md`

## Support

For issues or questions about the HiCart adapter:
1. Check test files for usage examples
2. Review saved HTML files in `testers/` directory
3. Check Django logs: `docker logs best-price-lebanon-web-1`
4. Verify adapter is registered: See list_adapters.py output
