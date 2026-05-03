# Implementation Summary

This document summarizes the current Awfarlak backend implementation.

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

These endpoints now require authentication. They are mostly useful for testing or direct API access. The frontend normally uses the comparison endpoint instead.

### `scraping`

Contains:

- `SearchJob` and `Offer` models
- `run_search()` service
- AI filtering integration
- scraper adapter base classes
- registered website adapters

Current registered adapters:

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

- Searches all registered adapters in parallel with `ThreadPoolExecutor`
- Uses AI filtering and cheapest-product selection per source
- Fetches detailed pricing when available
- Calculates final price, delivery days, store trust, and score
- Saves comparison searches and results to the database by default

Trending searches return the top 3 most-searched comparison queries. Counting ignores uppercase/lowercase differences and surrounding whitespace. Search counts are intentionally not returned to the frontend.

## Current Architecture

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

## Celery Status

Celery is configured:

- `best_price_lebanon/celery.py`
- Redis broker in settings
- `celery` service in `docker-compose.yml`

However, the active comparison flow does not currently enqueue Celery tasks. Comparisons run inside the HTTP request and use `ThreadPoolExecutor` for per-source concurrency.

This is acceptable for the current project/demo scope. A production-scale version should move long-running comparisons to Celery tasks and expose job-status polling endpoints.

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

## Recent Updates

- Added `ezonelb` adapter.
- Fixed Beytech range pricing to use the lower price in ranges.
- Cleaned 961souq same-day delivery text from `1-1 business days` to `1 business day`.
- Added trending searches endpoint.
- Made single-source API endpoints authenticated.
- Updated backend README and documentation to match current implementation.

## Known Limitations

- Comparisons can take a while because scraping happens during the request.
- Heavy simultaneous traffic may exhaust web worker/thread capacity.
- Some ecommerce websites may change layout or block scraping.
- Gemini quota issues can affect AI filtering.
- Celery is configured but not part of the active comparison execution path yet.
