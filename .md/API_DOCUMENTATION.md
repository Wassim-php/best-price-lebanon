# API Documentation

Base backend URL during local development:

```text
http://localhost:8000
```

Most endpoints require:

```http
Authorization: Bearer <access_token>
```

## Authentication

Base path:

```text
/api/auth/
```

### Register

```http
POST /api/auth/register
```

Body:

```json
{
  "username": "michel",
  "email": "michel@example.com",
  "password": "StrongPass1!",
  "location": true
}
```

`location: true` means inside Beirut. `location: false` means outside Beirut.

### Login

```http
POST /api/auth/login
```

Body:

```json
{
  "username": "michel",
  "password": "StrongPass1!"
}
```

### Google Login

```http
POST /api/auth/google
```

Body:

```json
{
  "id_token": "google_id_token"
}
```

### Auth Response

Register, login, and Google login return:

```json
{
  "user": {
    "id": 1,
    "username": "michel",
    "email": "michel@example.com",
    "location": true
  },
  "tokens": {
    "access": "...",
    "refresh": "..."
  }
}
```

### Logout

```http
POST /api/auth/logout
```

Body:

```json
{
  "refresh": "refresh_token"
}
```

### Update Location

```http
PATCH /api/auth/location
```

Body:

```json
{
  "location": false
}
```

### Change Password

```http
POST /api/auth/password
```

Body:

```json
{
  "old_password": "OldPass1!",
  "new_password": "NewPass1!"
}
```

## Single-Source Search

These endpoints are authenticated. They are mainly for direct testing and internal/API usage; the frontend uses the comparison endpoint.

Base path:

```text
/api/
```

Available `source_key` values from the 12 registered website adapters:

- `961souq`
- `ayoubcomputers`
- `abdeltahan`
- `mobileleb`
- `hicart`
- `outgeeked`
- `zoodmall`
- `phonefinity`
- `dslrzone`
- `ishtari`
- `beytech`
- `ezonelb`

### Search by Source

```http
POST /api/search/<source_key>
```

Body:

```json
{
  "query": "iphone 15",
  "use_ai_filter": true,
  "cheapest_only": false
}
```

Example:

```bash
curl -X POST http://localhost:8000/api/search/mobileleb \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d "{\"query\":\"iphone 15\",\"use_ai_filter\":true,\"cheapest_only\":false}"
```

### Get Product Details

```http
POST /api/product-details/<source_key>
```

Body:

```json
{
  "product_url": "https://example.com/product",
  "location": "inside beirut"
}
```

### Search with Details

```http
POST /api/search-with-details/<source_key>
```

Body:

```json
{
  "query": "iphone 15",
  "location": "outside beirut"
}
```

This searches a single source with AI filtering and cheapest-product selection, then fetches detailed pricing when the adapter supports it.

## Comparisons

Base path:

```text
/api/comparisons/
```

All comparison endpoints require authentication.

### Compare Across All Sources

```http
POST /api/comparisons/compare
```

Body:

```json
{
  "query": "iphone 15",
  "location": "inside beirut",
  "save": true
}
```

Response shape:

```json
{
  "query": "iphone 15",
  "location": "inside beirut",
  "search_id": 123,
  "results": [
    {
      "product": {
        "title": "Product title",
        "url": "https://example.com/product",
        "image_url": "https://example.com/image.jpg",
        "in_stock": true
      },
      "pricing": {
        "item_price": 950.0,
        "shipping_fee": 0.0,
        "tax_amount": 0.0,
        "total_price": 950.0,
        "currency": "USD",
        "delivery_time": "1 business day"
      },
      "source": "mobileleb",
      "store_rating": 4.3,
      "delivery_days": 1,
      "score": 9.2,
      "score_breakdown": {
        "price_score": 10.0,
        "delivery_score": 9.3,
        "trust_score": 8.6
      }
    }
  ],
  "metadata": {
    "min_price": 950.0,
    "sites_checked": 12,
    "sites_succeeded": 8,
    "sites_failed": 4,
    "failed_sources": []
  }
}
```

### Get History

```http
GET /api/comparisons/history?limit=20
```

Regular users receive their own history. Staff users can view all history.

### Trending Searches

```http
GET /api/comparisons/trending
```

Returns the top 3 searched comparison queries.

Behavior:

- Case-insensitive counting
- Surrounding whitespace ignored
- Search counts are not returned

Example:

```json
{
  "searches": [
    {
      "query": "iphone 15",
      "latest_searched_at": "2026-05-03T12:00:00Z"
    }
  ]
}
```

### Clear History

```http
DELETE /api/comparisons/history/clear
```

Optional staff-only targeting:

```json
{
  "user_id": 5
}
```

### Get Comparison Details

```http
GET /api/comparisons/<search_id>
```

### Delete One Comparison

```http
DELETE /api/comparisons/<search_id>
```

## Common Error Responses

### Missing Authentication

```json
{
  "detail": "Authentication credentials were not provided."
}
```

### Invalid Token

```json
{
  "detail": "Given token not valid for any token type"
}
```

### Unknown Source

```json
{
  "error": "Unknown source"
}
```

### Missing Query

```json
{
  "error": "query is required"
}
```

### No Products Found

```json
{
  "error": "No products found matching your query",
  "query": "example",
  "source": "mobileleb"
}
```

### AI Quota Exceeded

```json
{
  "error": "AI_QUOTA_EXCEEDED",
  "message": "Gemini API quota exceeded. The AI filtering service is temporarily unavailable. Please try again in a few minutes."
}
```
