# Best Price Lebanon - API Documentation

## Endpoints

### 1. Search by Source
**Endpoint:** `POST /api/search/<source_key>`

Search for products from a specific source.

**Parameters:**
- `source_key`: Source name (ayoubcomputers, 961souq)
- `query` (required): Search query string
- `use_ai_filter` (optional): Boolean, default False
- `cheapest_only` (optional): Boolean, default False

**Example:**
```bash
curl -X POST http://localhost:8000/api/search/ayoubcomputers \
  -H "Content-Type: application/json" \
  -d '{"query": "headphones", "use_ai_filter": true, "cheapest_only": false}'
```

---

### 2. Get Product Details
**Endpoint:** `POST /api/product-details/<source_key>`

Get detailed pricing for a specific product including shipping and taxes.

**Parameters:**
- `source_key`: Source name (ayoubcomputers, 961souq)
- `product_url` (required): Full URL to the product page
- `location` (optional): "inside beirut" or "outside beirut" (default: "outside beirut")

**Example:**
```bash
curl -X POST http://localhost:8000/api/product-details/ayoubcomputers \
  -H "Content-Type: application/json" \
  -d '{"product_url": "https://ayoubcomputers.com/hoco-wireless-and-wired-headphones-w33/", "location": "outside beirut"}'
```

**Response:**
```json
{
  "item_price": 14.0,
  "shipping_fee": 0.0,
  "tax_amount": 1.54,
  "total_price": 15.54,
  "currency": "USD",
  "delivery_time": "2-6 business days",
  "breakdown": {
    "Item Price": "$14.00",
    "Shipping": "FREE",
    "Tax (11%)": "$1.54",
    "Total": "$15.54",
    "Delivery Time": "2-6 business days",
    "Note": "Ayoub Computers offers free delivery with 11% tax on all orders"
  }
}
```

---

### 3. Search with Complete Details (NEW!)
**Endpoint:** `POST /api/search-with-details/<source_key>`

**This is the main endpoint you want to use!**

Combines AI-filtered search with detailed pricing to provide a complete product recommendation. 
This endpoint:
1. Searches with AI filter enabled
2. Returns only the cheapest matching product
3. Automatically fetches complete pricing details including shipping, taxes, and delivery time

**Parameters:**
- `source_key`: Source name (ayoubcomputers, 961souq)
- `query` (required): Search query string
- `location` (optional): "inside beirut" or "outside beirut" (default: "outside beirut")

**Example:**
```bash
curl -X POST http://localhost:8000/api/search-with-details/ayoubcomputers \
  -H "Content-Type": application/json" \
  -d '{"query": "wireless headphones", "location": "outside beirut"}'
```

**Response:**
```json
{
  "product": {
    "title": "Hoco Wireless and Wired Headphones | W33",
    "url": "https://ayoubcomputers.com/hoco-wireless-and-wired-headphones-w33/",
    "image_url": "https://cdn11.bigcommerce.com/s-sp9oc95xrw/images/stencil/300w/products/54728/134897/HocoWirelessandWiredHeadphonesW331__50121.1764589449.jpg",
    "in_stock": true
  },
  "pricing": {
    "item_price": 14.0,
    "shipping_fee": 0.0,
    "tax_amount": 1.54,
    "total_price": 15.54,
    "currency": "USD",
    "delivery_time": "2-6 business days",
    "breakdown": {
      "Item Price": "$14.00",
      "Shipping": "FREE",
      "Tax (11%)": "$1.54",
      "Total": "$15.54",
      "Delivery Time": "2-6 business days",
      "Note": "Ayoub Computers offers free delivery with 11% tax on all orders"
    }
  },
  "source": "ayoubcomputers",
  "query": "wireless headphones"
}
```

---

## Available Sources

### ayoubcomputers
- **Fixed pricing rules:**
  - Delivery: Always FREE
  - Taxes: Always 11%
  - Delivery time: Always 2-6 business days
  - Total = item_price * 1.11

### 961souq
- **Dynamic pricing:**
  - Shipping varies by location and product
  - Uses Selenium to simulate checkout for accurate pricing
  - Delivery time varies

---

## Usage Examples

### Python Example (using requests):
```python
import requests

# Search with complete details
response = requests.post(
    "http://localhost:8000/api/search-with-details/ayoubcomputers",
    json={
        "query": "iPhone 15",
        "location": "outside beirut"
    }
)

result = response.json()
print(f"Product: {result['product']['title']}")
print(f"Total Price: ${result['pricing']['total_price']:.2f}")
print(f"Delivery: {result['pricing']['delivery_time']}")
```

### JavaScript Example (using fetch):
```javascript
fetch('http://localhost:8000/api/search-with-details/ayoubcomputers', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    query: 'wireless mouse',
    location: 'inside beirut'
  })
})
.then(res => res.json())
.then(data => {
  console.log('Product:', data.product.title);
  console.log('Total:', data.pricing.total_price);
  console.log('Delivery:', data.pricing.delivery_time);
});
```

---

## Error Responses

### 404 - Unknown Source
```json
{
  "error": "Unknown source"
}
```

### 404 - No Products Found
```json
{
  "error": "No products found matching your query",
  "query": "unicorn laptop",
  "source": "ayoubcomputers"
}
```

### 400 - Missing Query
```json
{
  "error": "query is required"
}
```

### 500 - Server Error
```json
{
  "error": "Error message here"
}
```
