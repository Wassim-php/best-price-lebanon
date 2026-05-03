# Setup Guide

This guide is for the Awfarlak Django backend.

## Requirements

- Docker and Docker Compose, recommended
- Or Python with the packages in `requirements.txt`
- PostgreSQL
- Redis, used by the Celery worker service

## Environment

The backend reads these environment variables:

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

`GOOGLE_OAUTH_CLIENT_ID` is needed for Google login. `GEMINI_API_KEY` is needed for AI filtering.

## Docker Setup

Build and start services:

```bash
docker-compose up --build
```

Run migrations:

```bash
docker-compose exec web python manage.py migrate
```

Create an admin user:

```bash
docker-compose exec web python manage.py createsuperuser
```

The API runs at:

```text
http://localhost:8000
```

PostgreSQL is exposed on host port `5433`.

## Local Setup Without Docker

Install dependencies:

```bash
pip install -r requirements.txt
```

Run migrations:

```bash
python manage.py migrate
```

Start Django:

```bash
python manage.py runserver
```

Run the Celery worker when running the full local stack:

```bash
celery -A best_price_lebanon worker --loglevel=info
```

The comparison endpoint performs parallel website searches inside the API request using `ThreadPoolExecutor`.

## Project Structure

```text
best-price-lebanon/
  api/                  Single-source search/detail endpoints
  authentication/       JWT auth, Google login, location, password change
  best_price_lebanon/   Django settings, root URLs, Celery app
  comparisons/          Multi-website compare, scoring, history, trending
  scraping/             Adapter registry, scraper services, scraper models
  testers/              Local scraper test helpers
  docs/                 Additional generated/project docs
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

## Quick API Smoke Test

First login:

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"your_user\",\"password\":\"your_password\"}"
```

Then call a protected endpoint with the returned access token:

```bash
curl -X POST http://localhost:8000/api/comparisons/compare \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d "{\"query\":\"iphone 15\",\"location\":\"inside beirut\",\"save\":true}"
```

## Development Commands

View web logs:

```bash
docker-compose logs -f web
```

View worker logs:

```bash
docker-compose logs -f celery
```

Stop services:

```bash
docker-compose down
```

Rebuild after dependency or Dockerfile changes:

```bash
docker-compose up --build
```

Open Django shell:

```bash
docker-compose exec web python manage.py shell
```

Run compile checks:

```bash
python -m py_compile api/views.py comparisons/views.py scraping/services.py
```
