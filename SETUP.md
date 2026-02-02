# Setup and Run Guide

## 🚀 Quick Start with Docker

### 1. Build and start all services
```bash
docker-compose up --build
```

### 2. Run migrations (in a new terminal)
```bash
docker-compose exec web python manage.py makemigrations
docker-compose exec web python manage.py migrate
```

### 3. Create a superuser (optional)
```bash
docker-compose exec web python manage.py createsuperuser
```

## 📡 API Endpoints

### Search Endpoint
**POST** `http://localhost:8000/api/search/{source_key}`

**Example:**
```bash
curl -X POST http://localhost:8000/api/search/961souq \
  -H "Content-Type: application/json" \
  -d "{\"query\":\"hp victus\"}"
```

**Response:**
```json
{
  "job_id": 1,
  "status": "DONE",
  "source": "961souq",
  "offers": [
    {
      "title": "HP Victus Gaming Laptop",
      "item_price": "1299.00",
      "currency": "USD",
      "url": "https://961souq.com/...",
      "image_url": "https://..."
    }
  ]
}
```

## 🏗️ Project Structure

```
best-price-lebanon/
├── scraping/               # Scraping app
│   ├── adapters/          # Website adapters
│   │   ├── base.py       # Base adapter interface
│   │   └── souq961.py    # 961Souq implementation
│   ├── models.py         # SearchJob & Offer models
│   ├── services.py       # Business logic
│   └── registry.py       # Adapter registry
├── api/                   # REST API
│   ├── views.py          # API endpoints
│   └── urls.py           # API routes
└── best_price_lebanon/    # Django project
    ├── settings.py
    └── urls.py
```

## ➕ Adding New Sources

1. Create adapter in `scraping/adapters/newsource.py`:
```python
from .base import BaseAdapter, OfferData

class NewSourceAdapter(BaseAdapter):
    source_name = "newsource"
    base_url = "https://newsource.com"
    
    def search(self, query: str, limit: int = 10):
        # Implementation here
        pass
```

2. Register in `scraping/registry.py`:
```python
from scraping.adapters.newsource import NewSourceAdapter

ADAPTERS = {
    "961souq": Souq961Adapter(),
    "newsource": NewSourceAdapter(),  # Add here
}
```

3. Test:
```bash
curl -X POST http://localhost:8000/api/search/newsource \
  -H "Content-Type: application/json" \
  -d "{\"query\":\"laptop\"}"
```

## 🛠️ Development Commands

### View logs
```bash
docker-compose logs -f web
```

### Stop services
```bash
docker-compose down
```

### Rebuild after changes
```bash
docker-compose up --build
```

### Access Django shell
```bash
docker-compose exec web python manage.py shell
```

## 🎯 Next Steps

1. Add more adapters (ishtari, CompuGhini, etc.)
2. Implement price comparison logic
3. Add caching with Redis
4. Create frontend UI
5. Add authentication
