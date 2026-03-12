# Comparisons App

This Django app handles multi-site product comparisons with intelligent scoring and user history tracking.

## Features

- **Parallel Execution**: Queries all 7 stores simultaneously using ThreadPoolExecutor
- **Intelligent Scoring**: Rates products based on price (50%), delivery time (20%), and store trust (30%)
- **User History**: Saves all searches for authenticated users
- **Comprehensive Data**: Stores full pricing breakdown including shipping and taxes

## API Endpoints

### 1. Compare All Sources
**POST** `/api/comparisons/compare`

Compare product prices across all available sources.

**Request Body:**
```json
{
  "query": "iPhone 15",
  "location": "outside beirut",  // optional, default: "outside beirut"
  "save": true                    // optional, default: true
}
```

**Response:**
```json
{
  "query": "iPhone 15",
  "location": "outside beirut",
  "search_id": 123,
  "results": [
    {
      "product": {
        "title": "Apple iPhone 15 128GB",
        "url": "https://...",
        "image_url": "https://...",
        "in_stock": true
      },
      "pricing": {
        "item_price": 950.0,
        "shipping_fee": 4.0,
        "tax_amount": 0.0,
        "total_price": 954.0,
        "currency": "USD",
        "delivery_time": "3 days"
      },
      "source": "mobileleb",
      "store_rating": 4.3,
      "delivery_days": 3,
      "score": 9.2,
      "score_breakdown": {
        "price_score": 10.0,
        "delivery_score": 8.6,
        "trust_score": 8.6
      }
    }
  ],
  "metadata": {
    "min_price": 950.0,
    "sites_checked": 7,
    "sites_succeeded": 6,
    "sites_failed": 1,
    "failed_sources": [
      {
        "source": "zoodmall",
        "error": "Timeout"
      }
    ]
  }
}
```

### 2. Get Comparison History
**GET** `/api/comparisons/history?limit=20`

Get search history for authenticated user.

**Response:**
```json
{
  "count": 5,
  "searches": [
    {
      "id": 123,
      "query": "iPhone 15",
      "location": "outside beirut",
      "min_price": 950.0,
      "sites_checked": 7,
      "sites_succeeded": 6,
      "result_count": 6,
      "top_result": {
        "source": "mobileleb",
        "product_title": "Apple iPhone 15 128GB",
        "total_price": 954.0,
        "score": 9.2
      },
      "username": "john_doe",
      "created_at": "2026-03-03T10:30:00Z"
    }
  ]
}
```

### 3. Get Comparison Details
**GET** `/api/comparisons/<search_id>`

Get full details of a specific comparison search.

**Response:**
Same structure as the compare endpoint, but retrieved from database.

## Database Models

### ComparisonSearch
Stores the main search query and metadata.

Fields:
- `user`: ForeignKey to User (nullable for anonymous)
- `query`: Search string
- `location`: Delivery location
- `min_price`: Minimum price found
- `sites_checked`: Total sites queried
- `sites_succeeded`: Successful responses

### ComparisonResult
Stores individual product results.

Fields:
- `search`: ForeignKey to ComparisonSearch
- `source`: Store identifier
- `product_title`, `product_url`, `image_url`, `in_stock`
- `item_price`, `shipping_fee`, `tax_amount`, `total_price`, `currency`
- `delivery_time`, `delivery_days`
- `store_rating`: Store rating (0-5)
- `score`: Overall score (0-10)
- `price_score`, `delivery_score`, `trust_score`: Component scores
- `pricing_breakdown`: JSON field with full details

## Scoring Algorithm

The scoring system uses weighted components:

```python
# Weights
price_weight = 50%
delivery_weight = 20%
trust_weight = 30%

# Price Score (0-10)
price_score = (min_price / product_price) * 10

# Delivery Score (0-10)
# Drops to 0 at 14 days
delivery_score = max(0, 10 - (delivery_days / 1.4))

# Trust Score (0-10)
# Store rating converted from 5-star to 10-point scale
trust_score = store_rating * 2

# Final Score
final_score = (0.5 * price_score) + (0.2 * delivery_score) + (0.3 * trust_score)
```

## Store Ratings

Current store ratings (can be adjusted in adapter files):
- AbedTahan: 4.5 ⭐ (3 days delivery)
- OutGeeked: 4.4 ⭐ (4 days delivery)
- MobileLeb: 4.3 ⭐ (3 days delivery)
- AyoubComputers: 4.2 ⭐ (3 days delivery)
- HiCart: 4.1 ⭐ (5 days delivery)
- 961Souq: 4.0 ⭐ (4 days delivery)
- ZoodMall: 3.8 ⭐ (5 days delivery)

## Setup Instructions

1. **Run migrations** (via Docker):
```bash
docker-compose exec web python manage.py makemigrations comparisons
docker-compose exec web python manage.py migrate
```

2. **Create superuser** (optional, for admin access):
```bash
docker-compose exec web python manage.py createsuperuser
```

3. **Test the endpoint**:
```bash
curl -X POST http://localhost:8000/api/comparisons/compare \
  -H "Content-Type: application/json" \
  -d '{"query": "iPhone 15", "location": "outside beirut"}'
```

## Performance

- **Parallel Execution**: All 7 stores queried simultaneously
- **Typical Response Time**: 10-15 seconds (limited by slowest store)
- **Timeout**: 30 seconds per store (prevents hanging)
- **Graceful Degradation**: Returns partial results if some stores fail

## Admin Interface

The comparisons app is registered in Django admin:
- View all comparison searches
- Filter by user, date, location
- Inspect detailed results and scores
- Manual data management

Access at: `http://localhost:8000/admin/comparisons/`
