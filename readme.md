# 📦 Price & Delivery Comparison Platform (Lebanon)

> **Senior Project – Work in Progress**  
> This README represents the *initial version* of the project documentation and will be continuously updated throughout development.

---

## 📌 Project Overview

This project is a web-based application designed to help users find the **best price and delivery time** for products available in Lebanon or shipped to Lebanon.

Users can enter a product name, and the system will:
- Search for the product across multiple Lebanese and international e-commerce websites
- Calculate the **final delivered price** (product price + shipping + estimated taxes/customs)
- Estimate delivery time ranges
- Rank results based on **best price** and **fastest delivery**

The platform combines **web scraping**, **asynchronous backend processing**, and **agentic AI** to provide accurate and transparent comparisons.

---

## 🎯 Project Goals

- Reduce the time and effort required to compare online product prices in Lebanon
- Provide transparency around hidden costs (shipping, customs, taxes)
- Compare delivery times across different sellers and platforms
- Demonstrate scalable scraping architecture and intelligent AI-assisted data extraction

---

## 🧠 Key Features (Planned)

- Product query normalization and confirmation
- Parallel scraping of multiple e-commerce websites
- Delivered-price calculation engine
- Delivery-time estimation and comparison
- Ranking system (price + delivery)
- Progress tracking for scraping jobs
- Admin interface for managing sources and monitoring scrapers

---

## 🌍 Data Sources

### 🇱🇧 Lebanon-based websites
- Ishtari
- 961Souq✅
- Abed Tahan✅
- MobileLeb✅
- HiCart ✅
- Ayoub ✅
- Makhsoom TBR
- Maasrani Electronics TBR
- OutGeeked ✅
- Phonefinity ✅

### 🌐 International websites (shipping to Lebanon)
- SHEIN
- ZoodMall ⚠️ (Adapter implemented - Cloudflare protection requires proxy service for production)

> Note: The system is designed to scale beyond these sources.

---

## 🏗️ High-Level Architecture

```
User Request
     ↓
Django REST API
     ↓
Scrape Job Created
     ↓
Celery Workers (Parallel Scraping)
     ↓
AI-Assisted Normalization & Validation
     ↓
Pricing + Delivery Calculation
     ↓
Ranking Engine
     ↓
Results Returned to User
```

---

## 🛠️ Tech Stack

### Backend
- Django
- Django REST Framework
- PostgreSQL

### Background Processing
- Celery
- Redis

### Web Scraping
- Playwright (JavaScript-heavy sites)
- BeautifulSoup / lxml (static pages)

### AI Integration
- Large Language Model (LLM) API for:
  - product normalization
  - delivery-time extraction
  - fallback parsing and validation

### Frontend
- React or Next.js (planned)

### DevOps / Deployment
- Docker
- Cloud hosting (TBD)

---

## ⚠️ Current Status

- Project planning and architecture design
- Source selection finalized
- Backend setup in progress

---

## 🚧 Limitations (Current & Expected)

- Shipping and customs costs are **estimates**, not guarantees
- Website structure changes may affect scraping reliability
- Anti-bot protections may limit scraping frequency

These limitations will be addressed and documented as the project evolves.

---

## 👥 Team

- **Michel Naouss**  
- **Wassim Nasrallah**

### Supervisor
- **Dr. Charbel Fakhri**

---

## 📅 Roadmap (High-Level)

- Phase 1: Backend setup & core models
- Phase 2: Single-site scraping prototype
- Phase 3: Multi-site parallel scraping
- Phase 4: AI integration
- Phase 5: Ranking & optimization
- Phase 6: Frontend & final evaluation

---

## 📝 Notes

This README is an **initial draft** and will be updated as features are implemented, architecture evolves, and evaluation results are gathered.

---

📌 *Last updated: Initial project setup phase*
