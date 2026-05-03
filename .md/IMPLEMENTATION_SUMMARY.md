# Implementation Summary

This document summarizes the Awfarlak backend implementation prepared for submission.

## Implemented Apps

### `authentication`

Provides account and JWT functionality:

- Register
- Username/password login
- Google ID-token login
- Logout with refresh-token blacklist
- Delivery location setting
- Password change

Account delivery location is stored as a boolean:

- `true`: inside Beirut
- `false`: outside Beirut

### `api`

Provides direct single-source scraper endpoints:

- `POST /api/search/<source_key>`
- `POST /api/product-details/<source_key>`
- `POST /api/search-with-details/<source_key>`

These endpoints require authentication. They are mainly useful for direct backend testing and API inspection. The frontend uses the comparison endpoint.

### `scraping`

Contains:

- `SearchJob` and `Offer` models
- `run_search()` service
- AI filtering integration
- scraper adapter base classes
- 12 registered website adapters

Registered website adapters from `scraping/registry.py`:

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

### `comparisons`

Provides the main product comparison flow:

- `POST /api/comparisons/compare`
- `GET /api/comparisons/history`
- `GET /api/comparisons/trending`
- `DELETE /api/comparisons/history/clear`
- `GET /api/comparisons/<search_id>`
- `DELETE /api/comparisons/<search_id>`

The comparison endpoint:

- Searches all 12 registered website adapters in parallel with `ThreadPoolExecutor`
- Uses AI filtering and cheapest-product selection per source
- Fetches detailed pricing when available
- Calculates final price, delivery days, store trust, and score
- Saves comparison searches and results to the database by default

Trending searches return the top 3 most-searched comparison queries. Counting ignores uppercase/lowercase differences and surrounding whitespace. Search counts are intentionally not returned to the frontend.

## Architecture

```text
Frontend
  -> Django REST API
    -> JWT authentication
    -> compare_all_sources
      -> ThreadPoolExecutor
        -> run_search per adapter
          -> adapter.search()
          -> optional Gemini AI filtering
          -> detailed pricing
      -> scoring
      -> database save
    -> response
```

## Background Worker Status

Celery infrastructure is included in the project:

- `best_price_lebanon/celery.py`
- Redis broker in settings
- `celery` service in `docker-compose.yml`

The comparison endpoint runs website searches inside the HTTP request and uses `ThreadPoolExecutor` for per-website concurrency.

## Security and Access Control

- Auth endpoints use JWT tokens from Simple JWT.
- Protected endpoints require `Authorization: Bearer <access_token>`.
- Comparison history is scoped to the authenticated user.
- Staff users have broader history visibility and can clear targeted user history.
- Direct single-source search/detail endpoints require authentication.

## Scoring

Comparison results are scored from 0 to 10:

- Price score: 50%
- Delivery score: 20%
- Store trust score: 30%

The scoring logic lives in `comparisons/scoring.py`.

## Implemented Highlights

- 12 website adapters are registered through `scraping/registry.py`.
- Multi-website comparisons run in parallel with `ThreadPoolExecutor`.
- AI filtering helps remove unrelated products before cheapest-product selection.
- Detailed pricing includes item price, shipping fee, total price, currency, and delivery time when supported by the adapter.
- Beytech range prices use the lower listed price.
- 961souq same-day delivery is displayed as `1 business day`.
- Trending searches return the top 3 normalized queries without exposing search counts.
- Single-source API endpoints require authentication.

## Operational Considerations

- Comparisons can take a while because website searches happen during the request.
- Heavy simultaneous traffic may exhaust web worker/thread capacity.
- Some websites may change layout or block scraping.
- Gemini quota issues can affect AI filtering.
- Celery infrastructure is included, while the comparison endpoint uses request-time parallel execution.
