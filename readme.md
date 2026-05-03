# Awfarlak Backend

Awfarlak is a Django REST backend for comparing product prices, delivery fees, and delivery times across 12 ecommerce websites.

The backend powers:

- User registration, login, Google login, logout, password change, and delivery-location settings
- Single-source product search
- Product detail pricing with delivery fees
- Multi-website comparison across registered adapters
- Search history and trending comparison queries
- AI-assisted filtering for matching the requested product more accurately

## Tech Stack

- Python
- Django 6
- Django REST Framework
- Simple JWT authentication
- PostgreSQL
- Redis and Celery
- BeautifulSoup, lxml, requests, Selenium, cloudscraper
- Google Gemini API for AI filtering
- Google OAuth token verification

## Project Structure

```text
best-price-lebanon/
  api/                  Single-source search/detail API endpoints
  authentication/       JWT auth, Google login, user location, password changes
  best_price_lebanon/   Django project settings and root URLs
  comparisons/          Multi-website comparison, scoring, history, trending searches
  scraping/             Scraper adapters, registry, services, search models
  testers/              Local/manual scraper testing helpers
  docs/                 Additional scraper documentation and notes
```

## Integrated Websites

The backend uses 12 website adapters registered in `scraping/registry.py`:

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

## Environment Variables

Create a `.env` file or provide these variables through Docker/environment configuration:

```env
POSTGRES_NAME=lebanon_prices
POSTGRES_USER=hello
POSTGRES_PASSWORD=hello
POSTGRES_HOST=db
GEMINI_API_KEY=your_gemini_api_key
GOOGLE_OAUTH_CLIENT_ID=your_google_oauth_client_id
ISHTARI_API_TOKEN=optional_ishtari_api_token
FRONTEND_URLS=http://localhost:5173,http://127.0.0.1:5173
```

`GOOGLE_OAUTH_CLIENT_ID` is required for Google login. `GEMINI_API_KEY` is required when AI filtering is enabled.

## Running With Docker

```bash
docker-compose up --build
```

The Django API runs on:

```text
http://localhost:8000
```

PostgreSQL is exposed locally on port `5433` and Redis is available inside the Docker network.

Run migrations:

```bash
docker-compose exec web python manage.py migrate
```

Create an admin user:

```bash
docker-compose exec web python manage.py createsuperuser
```

## Running Locally Without Docker

Install dependencies:

```bash
pip install -r requirements.txt
```

Run migrations:

```bash
python manage.py migrate
```

Start the development server:

```bash
python manage.py runserver
```

Run the Celery worker when running the full Docker-equivalent local stack:

```bash
celery -A best_price_lebanon worker --loglevel=info
```

## Authentication API

Base path:

```text
/api/auth/
```

Endpoints:

| Method | Path | Description |
| --- | --- | --- |
| `POST` | `/api/auth/register` | Create a new user and return JWT tokens |
| `POST` | `/api/auth/login` | Login with username/password |
| `POST` | `/api/auth/google` | Login/register with a Google ID token |
| `POST` | `/api/auth/logout` | Blacklist a refresh token |
| `PATCH` | `/api/auth/location` | Update delivery location |
| `POST` | `/api/auth/password` | Change password |

Auth responses include:

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

`location: true` means inside Beirut. `location: false` means outside Beirut.

Protected endpoints use:

```http
Authorization: Bearer <access_token>
```

## Single-Source Search API

Base path:

```text
/api/
```

These endpoints require JWT authentication and are mainly used for direct backend testing. The frontend uses the comparison endpoint.

### Search a Source

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

### Search and Get Details

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

## Comparison API

Base path:

```text
/api/comparisons/
```

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

Behavior:

- Searches all 12 registered websites in parallel
- Uses AI filtering and cheapest-product selection per source
- Fetches detailed pricing when supported by the adapter
- Calculates final price, delivery days, and score
- Saves the comparison to history by default

### Get Comparison History

```http
GET /api/comparisons/history?limit=20
```

Regular users see their own history. Staff users can see all searches.

### Get Trending Searches

```http
GET /api/comparisons/trending
```

Returns the top 3 most searched comparison queries. Counting is case-insensitive and ignores surrounding whitespace, so `iphone 15`, `IPHONE 15`, and ` iphone 15 ` are counted together.

Example response:

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

The response does not include how many times each query was searched.

### Clear Comparison History

```http
DELETE /api/comparisons/history/clear
```

Regular users clear their own history. Staff users may target another user by providing `user_id`.

### Get or Delete One Comparison

```http
GET /api/comparisons/<search_id>
DELETE /api/comparisons/<search_id>
```

## Scoring

Comparison results are scored from 0 to 10 using:

- Price score: 50%
- Delivery score: 20%
- Store trust score: 30%

The scoring helpers live in `comparisons/scoring.py`.

## Delivery Location

Most pricing endpoints accept:

- `"inside beirut"`
- `"outside beirut"`

Different adapters use this value to calculate delivery fees and delivery-time estimates. Account settings store the same concept as a boolean:

- `true`: inside Beirut
- `false`: outside Beirut

## Notes and Limitations

- Website layouts can change, which may break individual scraper selectors.
- Some websites use anti-bot protection and may require special handling.
- Shipping and delivery estimates are based on available website data or adapter rules.
- AI filtering depends on Gemini quota and availability.

## Team

- Michel Naouss
- Wassim Nasrallah

Supervisor: Dr. Charbel Fakhri
