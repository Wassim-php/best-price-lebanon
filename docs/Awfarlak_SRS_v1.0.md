# Software Requirements Specification for Awfarlak

Software Requirements Specification for a Price and Delivery Comparison Platform in Lebanon

Version: 1.1
Prepared by: Naous
Date: May 3, 2026

## Revision History

| Name | Date | Reason for Changes | Version |
| --- | --- | --- | --- |
| Naous | May 2, 2026 | Initial complete SRS created for senior project submission. | 1.0 |
| Naous | May 3, 2026 | Updated to match the current Awfarlak backend/frontend implementation, 12-source registry, authenticated source endpoints, trending searches, environment-based secrets, and current UI behavior. | 1.1 |

## Table of Contents

- 1 Introduction
- 1.1 Purpose and Intended Audience
- 1.2 Project Scope
- 1.3 Terms, Definitions, and Acronyms
- 1.4 References
- 2 Overall Description
- 2.1 Product Perspective
- 2.2 Product Features
- 2.3 User Classes and Characteristics
- 2.4 Operating Environment
- 2.5 Design and Implementation Constraints
- 2.6 Assumptions and Dependencies
- 3 System Features
- 3.1 Functional Requirements
- 3.2 Supported Store Sources
- 3.3 Comparison Scoring Requirements
- 4 Non-Functional Requirements
- 5 External Interface Requirements
- 5.1 User Interfaces
- 5.2 Hardware Interfaces
- 5.3 Software Interfaces
- 5.4 Communication Interfaces
- 6 Detailed Use Cases
- 7 Appendix

## 1. Introduction

### 1.1 Purpose and Intended Audience

This SRS defines the required external behavior, constraints, interfaces, data expectations, and use cases for Awfarlak.

### 1.2 Project Scope

Awfarlak is a web-based product comparison system for shoppers in Lebanon. It includes a React frontend, Django REST backend, PostgreSQL persistence, Redis/Celery infrastructure, source adapters, Google OAuth, and Gemini product-intent filtering.

### 1.3 Terms, Definitions, and Acronyms

| Term | Definition |
| --- | --- |
| Adapter | A backend component that knows how to search one external store and normalize that store's product data into the common OfferData format. |
| AI Filtering | The use of Google Gemini to select search results that match the user's actual product intent and exclude unrelated accessories, bundles, or different product variants. |
| Awfarlak | The project name and frontend brand for the Lebanese price comparison platform. |
| Bearer Token | A token sent in the HTTP Authorization header to prove that a user is authenticated. |
| Comparison Search | A saved user search containing the original query, delivery location, metadata, and one or more ranked comparison results. |
| Delivery Location | A simplified location category used for shipping estimates: inside Beirut or outside Beirut. |
| Delivered Price | The final estimated cost shown to the user, calculated as item price plus shipping fee plus tax amount when available. |
| Django REST Framework (DRF) | The backend framework used to create JSON API endpoints for the React frontend. |
| External Store | An e-commerce website outside the system, such as 961Souq, Ayoub Computers, MobileLeb, HiCart, or Ishtari. |
| JWT | JSON Web Token. The authentication mechanism used by the backend for protected API calls. |
| Offer | A normalized product result returned from a store adapter. It includes title, product URL, image URL, price, currency, and stock status. |
| PostgreSQL | The relational database used to persist users, search jobs, offers, comparison searches, and comparison results. |
| React | The frontend JavaScript framework used to build the user interface. |
| Redis | The in-memory service configured as the Celery broker for background processing. |
| Search Job | A backend record representing a search request sent to one store source. |
| Store Rating | A manually assigned quality or trust signal for each source, measured from 0.0 to 5.0 and used in the scoring formula. |
| Trending Search | A normalized comparison query that appears among the top searched queries in saved comparison history. |
| Vite | The frontend development and build tool used by the React application. |

### 1.4 References

| ID | Reference | Location or Source |
| --- | --- | --- |
| REF-01 | Backend source repository | C:\Users\naous\senior-project\best-price-lebanon |
| REF-02 | Frontend source repository | C:\Users\naous\senior-project\awfarlak-react |
| REF-03 | Backend README: project overview, architecture, planned sources, and technology stack | best-price-lebanon\readme.md |
| REF-04 | Frontend README and implementation: API client, token handling, Vite proxy, routes, and services | awfarlak-react\README.md and awfarlak-react\src |
| REF-05 | Backend Docker Compose configuration for Django, PostgreSQL, Redis, and Celery | best-price-lebanon\docker-compose.yml |
| REF-06 | Backend comparison and scoring implementation | best-price-lebanon\comparisons |
| REF-07 | Backend scraping registry and source adapters | best-price-lebanon\scraping |
| REF-08 | Frontend React pages, services, and reusable components | awfarlak-react\src |

## 2. Overall Description

### 2.1 Product Perspective

```text
User Browser
  |
  | HTTPS/HTTP JSON requests
  v
React + Vite Frontend
  |-- AuthService -> /api/auth/*
  |-- ProductService -> /api/comparisons/compare and /api/comparisons/trending
  |-- HistoryService -> /api/comparisons/history and saved-search details
  v
Django REST API
  |-- Authentication app: JWT, Google token verification, location, password
  |-- Comparisons app: all-source comparison, scoring, saved history
  |-- Scraping app: SearchJob, Offer, adapter registry, AI filtering
  v
Parallel Adapter Execution
  |-- 961Souq, Ayoub, Abed Tahan, MobileLeb, HiCart, OutGeeked
  |-- ZoodMall, Phonefinity, DSLR Zone, Ishtari, Beytech, Ezone LB
  v
External Store Websites/APIs + Google Gemini
  |
  v
PostgreSQL persistence + Redis/Celery infrastructure
```

### 2.2 Product Features

| Feature | Description |
| --- | --- |
| Account creation and sign-in | Users can create accounts, sign in with username and password, or sign in using Google when configured. |
| Protected shopping dashboard | Authenticated users access a dashboard with comparison search, recent searches, and ranking results. |
| Multi-store product comparison | A single product query is searched across supported stores through source-specific adapters. |
| AI-assisted product matching | The backend can filter raw store results so accessories and wrong product variants are not treated as valid cheapest matches. |
| Delivered price estimation | The system calculates item price, shipping, tax, total price, delivery time, and delivery days when store data or source rules are available. |
| Recommendation scoring | Results are ranked using weighted price, delivery, and trust sub-scores. |
| Best deal and category highlights | The frontend highlights the best overall deal and separately identifies best price, best delivery, and best reliability. |
| Expandable result details | Users can inspect item price, shipping, delivery time, and score breakdown before opening the seller page. |
| Search history | Authenticated searches can be saved, listed, reopened, and cleared. |
| Trending searches | The dashboard lists the three most-used normalized comparison queries without exposing search counts. |
| Account settings | Users can update delivery location and password. Google accounts do not display password-change controls. |
| Admin visibility | Backend staff users can view comparison history beyond their own user records through the API permissions implemented in the comparison views. |

### 2.3 User Classes and Characteristics

| User Class | Priority | Characteristics |
| --- | --- | --- |
| Registered Shopper | Primary user | Basic web browsing skill. Uses the system to compare products, review price and delivery options, and open external seller pages. |
| Returning Shopper | Primary user | Same as registered shopper, with additional use of saved history to revisit previous searches. |
| Administrator / Evaluator | Secondary user | Moderate technical skill. Uses Django admin or staff-permitted API access to inspect records, validate behavior, and review source performance. |
| Developer / Maintainer | Supporting user | Advanced technical skill. Maintains adapters, environment variables, Docker services, scoring logic, API contracts, and frontend integration. |

### 2.4 Operating Environment

- Frontend: React 19, Vite 7, Tailwind CSS 4, axios, react-router-dom, and lucide-react.
- Backend: Django 6, Django REST Framework, Simple JWT, PostgreSQL, Redis, Celery, requests, BeautifulSoup/lxml, Selenium, and Google Generative AI SDK.
- Development ports: React 5173 and Django 8000, with Vite proxying /api requests.

### 2.5 Design and Implementation Constraints

- The system depends on external e-commerce websites whose HTML, APIs, prices, availability, and anti-bot rules may change without notice.
- Google Gemini quota and API availability affect AI filtering; the backend returns a specific quota error when most source failures are caused by AI quota exhaustion.
- Deployment values such as DEBUG, DJANGO_SECRET_KEY, allowed hosts, API keys, OAuth client IDs, and database credentials must be supplied through environment variables.
- The user location model is intentionally simple: inside Beirut or outside Beirut. It does not yet calculate shipping by exact address, district, or GPS coordinates.
- The frontend sends the user's saved inside/outside Beirut location with comparison requests; if a backend request omits location, the backend default remains outside Beirut.
- The application does not process payments, place orders, reserve products, manage returns, or guarantee that external store prices remain unchanged after the user leaves the application.
- Some source adapters rely on HTTP scraping, some use API extraction, and at least one source uses browser automation. Performance and reliability will vary by store.
- The frontend stores access and refresh tokens in localStorage. This works for the current implementation but should be reviewed during production security hardening.

### 2.6 Assumptions and Dependencies

- Users have an internet-connected device with a modern browser.
- Backend, database, Redis, and any worker processes are running when comparisons are requested.
- External store websites are reachable from the server environment.
- Prices are treated as USD unless a source explicitly returns another supported currency.
- Store rating values are manually maintained by the development team until a live review-data integration is introduced.
- Search queries are product names or product-like text. Source-specific product URLs can be used by diagnostic product-details endpoints, but the primary user workflow is product-name comparison.
- The user understands that final purchase decisions happen on external seller websites.

## 3. System Features

### 3.1 Functional Requirements

| ID | Name | Priority | Requirement | Acceptance Criteria |
| --- | --- | --- | --- | --- |
| FR-01 | User registration | High | The system shall allow a visitor to register with username, email, password, and delivery location. | A valid registration creates a Django user, stores the location flag, and returns a usable authentication response or validation errors. |
| FR-02 | Email uniqueness validation | High | The system shall reject registration when the email address already belongs to another user. | Duplicate email submission returns a validation error without creating a second user. |
| FR-03 | Password validation | High | The frontend and backend shall require passwords of at least eight characters and backend validators shall reject weak passwords. | Weak password submissions display an error and no account is created or changed. |
| FR-04 | Password login | High | The system shall authenticate registered users by username and password. | Valid credentials return user data plus JWT access and refresh tokens; invalid credentials return HTTP 401. |
| FR-05 | Google login | Medium | The system shall support Google Sign-In when Google client IDs are configured. | A verified Google ID token creates or locates a user, assigns an unusable password for new Google-only accounts, and returns JWT tokens. |
| FR-06 | Logout | High | The system shall allow authenticated users to log out by blacklisting the refresh token and clearing frontend authentication storage. | Logout removes tokens from localStorage and returns a success message when the refresh token is valid. |
| FR-07 | Protected routes | High | The frontend shall prevent unauthenticated visitors from accessing home, search history, account, and help pages. | Unauthenticated navigation redirects to the login page. |
| FR-08 | Update delivery location | High | The system shall allow authenticated users to change the stored inside/outside Beirut location. | A successful PATCH request updates auth_user.location and the frontend reflects the new selection. |
| FR-09 | Change password | Medium | The system shall allow password-authenticated users to change their password after entering the current password. | The backend validates the old password and new password; Google-authenticated accounts do not show password-change UI. |
| FR-10 | Submit comparison query | High | The system shall allow an authenticated user to submit a product search query from the dashboard. | A non-empty query sends POST /api/comparisons/compare and displays loading state while the backend searches. |
| FR-11 | Reject empty search | High | The frontend and backend shall reject blank product queries. | The user sees a clear error and the backend returns HTTP 400 when query is missing. |
| FR-12 | Parallel source search | High | The backend shall search registered store adapters in parallel to reduce total comparison time. | compare_all_sources submits one task per adapter through a ThreadPoolExecutor and records failed sources separately. |
| FR-13 | Source adapter normalization | High | Each store adapter shall normalize product data into title, URL, image URL, item price, currency, and stock status. | Saved Offer records and comparison responses use the common normalized structure. |
| FR-14 | AI intent filtering | High | When comparing across sources, the backend shall filter store results by product intent before selecting the cheapest candidate from each source. | Accessories and wrong variants are excluded according to the Gemini prompt rules; if filtering fails non-quota, the source returns no filtered results rather than an unsafe raw cheapest result. |
| FR-15 | AI quota handling | High | The backend shall return a clear quota response if Gemini quota exhaustion prevents most source searches. | The compare endpoint returns HTTP 429 with AI_QUOTA_EXCEEDED metadata when quota failures dominate. |
| FR-16 | Cheapest candidate selection | High | For each source, after AI filtering, the backend shall select the cheapest matching product for detailed pricing. | Each successful source contributes at most one candidate to the all-sources comparison. |
| FR-17 | Detailed delivered pricing | High | The backend shall calculate or extract item price, shipping fee, tax amount, total price, currency, and delivery time when supported by the adapter. | The response includes pricing fields and a pricing breakdown when available. |
| FR-18 | Location-aware shipping | Medium | The backend shall use the provided delivery location when calculating source-specific shipping and delivery time. | Adapters with inside/outside Beirut rules select the proper shipping fee and delivery range. |
| FR-19 | Graceful source failure | High | A failure in one store source shall not cancel the entire comparison if other sources succeed. | The response includes successful results plus metadata listing failed sources and errors. |
| FR-20 | No-results response | High | If no supported source returns a valid product, the backend shall return a not-found response. | The frontend displays a no-products or search-error state instead of an empty broken result grid. |
| FR-21 | Comparison scoring | High | The system shall calculate final score and sub-scores for price, delivery, and trust. | Each result includes final score, price_score, delivery_score, and trust_score. |
| FR-22 | Best deal presentation | High | The frontend shall present the highest-scoring product as the best deal. | The best deal card displays product image or fallback icon, title, source, stock status, total price, delivery, store rating, and score. |
| FR-23 | Category ranking presentation | Medium | The frontend shall highlight best price, best delivery, and best reliability where matching results exist. | Top Rankings cards display category badges and can be expanded for details. |
| FR-24 | Open external seller | High | The frontend shall let users open a product on the external seller website. | The Go to Store or View on Store link opens the product URL in a new browser context. |
| FR-25 | Save comparison history | High | The backend shall save authenticated comparison searches by default. | ComparisonSearch and ComparisonResult records are created with metadata and result details unless save is false. |
| FR-26 | Recent search display | Medium | The dashboard shall show recent searches for quick access. | The home page fetches history, normalizes it, and displays the latest three searches. |
| FR-27 | Full search history | Medium | The system shall provide a full history page for authenticated users. | Users can view previous queries, timestamps, best price, and open a previous search back in the home workflow. |
| FR-28 | Clear history | Medium | The system shall let users clear their own comparison history. | A confirmed clear action deletes the user's ComparisonSearch and ComparisonResult records and updates the UI. |
| FR-29 | History authorization | High | Users shall not access another regular user's comparison history. | Non-staff users are limited to their own records; staff users may view or clear targeted user history. |
| FR-30 | Trending searches | Medium | The system shall list the top three most-used saved comparison queries as trending searches. | GET /api/comparisons/trending returns at most three normalized queries, counts upper/lower case together, trims whitespace, and does not expose search counts. |
| FR-31 | Single-source diagnostic endpoints | Low | The backend shall expose authenticated source-specific search and product-details endpoints for testing adapters and detailed pricing. | Authenticated POST /api/search/<source>, /api/product-details/<source>, and /api/search-with-details/<source> return source-scoped results or meaningful errors. |

### 3.2 Supported Store Sources

| Adapter Key | Store | Base Source | Implementation Notes |
| --- | --- | --- | --- |
| 961souq | 961Souq | https://961souq.com | Selenium checkout simulation for detailed pricing; source rating 4.5; typical 4 delivery days. |
| ayoubcomputers | Ayoub Computers | https://ayoubcomputers.com | BigCommerce Storefront GraphQL search; source rating 4.7; typical 3 delivery days. |
| abdeltahan | Abed Tahan | https://abedtahan.com | Shopify search parsing with fixed shipping rules; source rating 4.6; typical 3 delivery days. |
| mobileleb | MobileLeb | https://mobileleb.com | Shopify search parsing; source rating 4.3; typical 3 delivery days. |
| hicart | HiCart | https://www.hicart.com | HTTP search parsing with fixed shipping; source rating 4.0; typical 5 delivery days. |
| outgeeked | OutGeeked | https://outgeeked.net | Shopify search parsing; source rating 4.4; typical 4 delivery days. |
| zoodmall | ZoodMall | https://www.zoodmall.com.lb | ZoodMall web pages with Selenium support; fixed Lebanon shipping estimate; source rating 3.0; typical 5 delivery days; anti-bot behavior may affect availability. |
| phonefinity | Phonefinity | https://phonefinity.net | WooCommerce search parsing; source rating 4.8; typical 3 delivery days. |
| dslrzone | DSLR Zone | https://www.dslr-zone.com | WooCommerce Store API first, HTML fallback; source rating 4.5; typical 4 delivery days. |
| ishtari | Ishtari | https://www.ishtari.com | Mobile API and HTML fallback strategies; source rating 4.1; typical 4 delivery days. |
| beytech | Beytech | https://www.beytech.com.lb | WooCommerce search parsing; source rating 4.5; typical 2 delivery days. |
| ezonelb | Ezone LB | https://ezonelb.com | WooCommerce Store API with HTML fallback; source rating 4.5; typical 2 delivery days. |

| Store | Shipping Rule | Tax Rule | Delivery Time Rule |
| --- | --- | --- | --- |
| 961Souq | Parsed from checkout | Parsed from checkout when present | Parsed dynamically; defaults such as 3-5 business days when free shipping is detected. |
| Ayoub Computers | Free shipping | 11 percent of item price | 2-6 business days. |
| Abed Tahan | Free over $350; otherwise $4 inside Beirut or $7 outside Beirut | None | 2-3 business days inside Beirut or free-shipping orders; 5-7 business days outside Beirut. |
| MobileLeb | $3 inside Beirut; $5 outside Beirut | None | 1-2 business days inside Beirut; 3-5 business days outside Beirut. |
| HiCart | $4 flat | 0 | 3-7 business days. |
| OutGeeked | $3 flat | 0 | 2-5 business days inside Beirut; 5-7 business days outside Beirut. |
| ZoodMall | $4.75 flat Lebanon delivery estimate | 0 | 2-7 business days. |
| Phonefinity | $5 flat | 0 | 1 business day inside Beirut; 2-4 business days outside Beirut. |
| DSLR Zone | Free at or above $350; $5 below $350 | 0 | 1-2 business days. |
| Ishtari | $3 inside Beirut; $5 outside Beirut | 0 | 2-4 business days inside Beirut; 3-6 business days outside Beirut. |
| Beytech | $5 flat | 0 | 2-3 business days. |
| Ezone LB | Free inside Beirut; $3 outside Beirut | 0 | 1 business day inside Beirut; 2-3 business days outside Beirut. |

### 3.3 Comparison Scoring Requirements

| Component | Formula | Meaning |
| --- | --- | --- |
| Price score | (minimum delivered price / result delivered price) * 10 | The cheapest result receives 10.0. |
| Delivery score | max(0, 10 - delivery_days / 1.4) | Shorter delivery times score higher. |
| Trust score | store_rating * 2 | Converts 5-point store rating to 10-point scale. |
| Final score | 0.50 * price + 0.20 * delivery + 0.30 * trust | Balanced recommendation score. |

## 4. Non-Functional Requirements

| ID | Category | Priority | Requirement | Evidence or Acceptance Criteria |
| --- | --- | --- | --- | --- |
| NFR-F-01 | Functional correctness | High | A comparison result shall not knowingly rank an unrelated accessory as the best product for a main-device query. | AI filtering rules and no-unsafe-fallback behavior are in place. |
| NFR-F-02 | Input validation | High | API endpoints shall reject missing required fields and malformed user input with clear HTTP errors. | Missing query and product_url paths return HTTP 400. |
| NFR-U-01 | Usability | High | The primary comparison workflow shall require no more than one query input and one submit action after login. | Home search bar accepts query and displays results without leaving the page. |
| NFR-U-02 | Responsive layout | High | The frontend shall support desktop and mobile navigation. | Sidebar collapses on desktop and becomes a mobile overlay menu below the desktop breakpoint. |
| NFR-U-03 | Feedback | High | Long-running searches shall display visible progress feedback. | The frontend rotates loading messages while the comparison request is pending. |
| NFR-R-01 | Partial failure tolerance | High | The system shall return successful store results even when some sources fail. | Failed source metadata is returned without discarding successful results. |
| NFR-R-02 | Error transparency | Medium | The frontend shall display meaningful search, authentication, history, and account update errors. | Service-layer errors are converted into user-facing messages. |
| NFR-P-01 | Comparison performance | High | The backend shall attempt source searches concurrently rather than sequentially. | The comparison view uses ThreadPoolExecutor with configured worker count and per-source timeout handling. |
| NFR-P-02 | User waiting expectation | Medium | The user interface shall set realistic expectations for comparison duration. | The loading panel states that searches can take up to 60 seconds depending on store response time. |
| NFR-S-01 | Authentication security | High | Protected API endpoints shall require JWT authentication. | Comparison and account endpoints use IsAuthenticated permissions. |
| NFR-S-02 | Token lifetime control | High | JWT access tokens shall be short-lived and refresh tokens shall rotate and be blacklisted after logout/rotation. | Configured access lifetime is 30 minutes and refresh lifetime is 7 days with rotation and blacklist enabled. |
| NFR-S-03 | Production secret handling | High | Production deployments shall use environment variables for secret keys, API keys, OAuth client IDs, database credentials, and allowed hosts. | No production deployment may rely on development fallback values. |
| NFR-M-01 | Maintainability | High | Adding a new store shall require implementing a new adapter and registering it in the adapter registry. | The BaseAdapter and ADAPTERS registry define the integration boundary. |
| NFR-M-02 | Testability | Medium | Scoring and comparison model behavior shall be covered by automated tests. | Existing tests validate delivery parsing, rating calculation, model creation, and ordering. |
| NFR-C-01 | Compatibility | Medium | The frontend shall run in modern browsers supported by React and Vite. | The application is built with React 19, Vite, Tailwind, axios, and react-router. |
| NFR-D-01 | Data retention control | Medium | Users shall be able to remove their comparison history. | Clear history endpoint deletes stored comparison searches and results for the target authorized user. |
| NFR-L-01 | Legal and ethical scraping | High | The system shall only collect publicly visible product listing and pricing information required for comparison. | The application does not store payment information, customer data from stores, or private seller records. |

## 5. External Interface Requirements

### 5.1 User Interfaces

| Interface | Route | Main Requirements |
| --- | --- | --- |
| Login page | /login | Username/password login, Google Sign-In button when configured, error messages, password visibility toggle, and auth-state synchronization after login. |
| Register page | /register | Username, email, password, confirm password, inside/outside Beirut selector, conditional address field, terms checkbox, validation messages. |
| Home dashboard | /home | Search bar, loading state, result cards, best deal card, top ranking cards, other options, top-three trending searches, recent searches, and clear recent history action. |
| Search history page | /search-history | Full saved search list, timestamp display, best price summary, open-in-home behavior, clear history action. |
| My account page | /account | Account identity summary, delivery location update controls, password change form for password accounts. |
| About and help page | /about-help | Plain-language explanation of comparison flow and FAQ. |
| Sidebar navigation | All protected pages | Responsive navigation links for Home, Search History, My Account, About and Help, and Sign Out. |

### 5.2 Hardware Interfaces

The system has no dedicated hardware interface. It requires standard user devices and sufficient backend server resources.

### 5.3 Software Interfaces

The system interfaces with React, Django REST Framework, PostgreSQL, Redis, Celery, Google OAuth, Google Gemini, and external store websites.

### 5.4 Communication Interfaces

| Method | Endpoint | Access | Purpose |
| --- | --- | --- | --- |
| POST | /api/auth/register | Public | Create account with username, email, password, and location; returns user and JWT tokens. |
| POST | /api/auth/login | Public | Authenticate username/password; returns user and JWT tokens. |
| POST | /api/auth/google | Public | Verify Google ID token; create or fetch user; return JWT tokens. |
| POST | /api/auth/logout | Authenticated | Blacklist refresh token and end session. |
| PATCH | /api/auth/location | Authenticated | Update inside/outside Beirut location flag. |
| POST | /api/auth/password | Authenticated | Change password after old-password validation. |
| POST | /api/comparisons/compare | Authenticated | Search all adapters, compute delivered pricing and scores, optionally save history. |
| GET | /api/comparisons/history | Authenticated | List comparison history for the user; staff may view all. |
| GET | /api/comparisons/trending | Authenticated | Return the top three normalized saved comparison queries without search counts. |
| DELETE | /api/comparisons/history/clear | Authenticated | Delete comparison history for the user; staff may target a user_id. |
| GET | /api/comparisons/<search_id> | Authenticated | Return saved comparison search and detailed results. |
| DELETE | /api/comparisons/<search_id> | Authenticated | Delete one saved comparison search after authorization check. |
| POST | /api/search/<source_key> | Authenticated diagnostic/internal | Run source-specific search, with optional AI filtering and cheapest-only flags. |
| POST | /api/product-details/<source_key> | Authenticated diagnostic/internal | Get detailed pricing for a specific product URL from one source. |
| POST | /api/search-with-details/<source_key> | Authenticated diagnostic/internal | Search one source, select the cheapest AI-filtered result, and get detailed pricing. |

## 6. Detailed Use Cases

### UC-01 Create Account

| Field | Description |
| --- | --- |
| Actors | Visitor |
| Preconditions | The visitor is not authenticated and can access the register page. |
| Trigger | The visitor submits the registration form. |
| Main Success Scenario | 1. Visitor enters username, email, password, password confirmation, location, and accepts terms.<br>2. Frontend validates required fields, email format, password strength, confirmation match, and terms acceptance.<br>3. Frontend sends username, email, password, and location to POST /api/auth/register.<br>4. Backend validates email uniqueness and password policy.<br>5. Backend creates a Django user, writes the location flag, and returns authentication data.<br>6. Frontend navigates the user to the login page after registration. |
| Alternate / Exception Flows | - If validation fails, the frontend displays field-level errors.<br>- If email is already registered, the backend returns a validation error and the account is not created. |
| Postconditions | A new user exists with a stored delivery location. |
| Related Requirements | FR-01, FR-02, FR-03 |

### UC-02 Sign In with Password

| Field | Description |
| --- | --- |
| Actors | Registered Shopper |
| Preconditions | The shopper has an existing username/password account. |
| Trigger | The shopper submits the login form. |
| Main Success Scenario | 1. Shopper enters username and password.<br>2. Frontend sends credentials to POST /api/auth/login.<br>3. Backend authenticates against Django auth.<br>4. Backend returns user details and JWT tokens.<br>5. Frontend stores tokens and user data in localStorage.<br>6. Frontend navigates to /home. |
| Alternate / Exception Flows | - If credentials are invalid, the backend returns HTTP 401 and the frontend displays an error.<br>- If token storage is cleared later, protected routes redirect back to /login. |
| Postconditions | The shopper has an authenticated browser session. |
| Related Requirements | FR-04, FR-07, NFR-S-01 |

### UC-03 Sign In with Google

| Field | Description |
| --- | --- |
| Actors | Visitor or Registered Shopper |
| Preconditions | Google client ID is configured in the frontend and backend. |
| Trigger | The user selects Google Sign-In. |
| Main Success Scenario | 1. Frontend loads the Google Identity script.<br>2. Google returns an ID token credential.<br>3. Frontend sends the ID token to POST /api/auth/google.<br>4. Backend verifies the token audience and verified email status.<br>5. Backend finds an existing user by email or creates a new Google-only user.<br>6. Backend returns JWT tokens and frontend navigates to /home. |
| Alternate / Exception Flows | - If Google is not configured, the frontend displays setup guidance.<br>- If the email is not verified or token is invalid, the backend rejects the login. |
| Postconditions | The user is authenticated with provider metadata set to google. |
| Related Requirements | FR-05, FR-07 |

### UC-04 Compare Product Across Stores

| Field | Description |
| --- | --- |
| Actors | Authenticated Shopper |
| Preconditions | The shopper is signed in and backend services are available. |
| Trigger | The shopper submits a product query from the home page. |
| Main Success Scenario | 1. Frontend verifies the query is not blank.<br>2. Frontend sends POST /api/comparisons/compare with the query and the user's normalized saved delivery location.<br>3. Backend starts parallel searches across all registered adapters.<br>4. Each adapter returns normalized raw offers.<br>5. Backend applies AI filtering and selects the cheapest matching candidate for each source.<br>6. Backend gets detailed pricing, delivery, and source rating metadata.<br>7. Backend calculates scores, sorts results, saves history, and returns the response.<br>8. Frontend renders best deal, category rankings, other options, metadata, and external store links. |
| Alternate / Exception Flows | - If one or more sources fail, their errors are listed in metadata and successful results still display.<br>- If no source succeeds, the backend returns HTTP 404 and the frontend displays an error/no-result state.<br>- If Gemini quota is exceeded for most sources, the backend returns HTTP 429 with AI_QUOTA_EXCEEDED. |
| Postconditions | The shopper sees ranked delivered-price recommendations and a saved comparison history record exists unless saving is disabled. |
| Related Requirements | FR-10 through FR-25, NFR-R-01, NFR-P-01 |

### UC-05 Use Trending Searches

| Field | Description |
| --- | --- |
| Actors | Authenticated Shopper |
| Preconditions | The shopper is signed in and at least one comparison search may exist in system history. |
| Trigger | The shopper opens the home dashboard or selects a trending search item. |
| Main Success Scenario | 1. Frontend requests GET /api/comparisons/trending with a limit of 3.<br>2. Backend normalizes saved query text by trimming whitespace and lowering case.<br>3. Backend counts matching normalized queries, orders by count and most recent search time, and returns at most three query values.<br>4. Frontend displays the returned queries without showing search counts.<br>5. Shopper selects a trending query and the frontend runs a new comparison for that query. |
| Alternate / Exception Flows | - If there are no saved searches, the frontend displays an empty trending-searches message.<br>- If the request fails, the dashboard continues to work without trending suggestions. |
| Postconditions | The shopper can quickly launch a comparison based on common searches. |
| Related Requirements | FR-30 |

### UC-06 Inspect and Open a Result

| Field | Description |
| --- | --- |
| Actors | Authenticated Shopper |
| Preconditions | A comparison response is displayed. |
| Trigger | The shopper expands a result or clicks the store link. |
| Main Success Scenario | 1. Shopper selects View Details on a result card.<br>2. Frontend reveals item price, shipping, delivery time, and score breakdown.<br>3. Shopper selects Go to Store or View on Store.<br>4. Browser opens the external product URL. |
| Alternate / Exception Flows | - If no image URL exists, the frontend displays a product icon fallback.<br>- If stock is unknown, the UI avoids claiming availability. |
| Postconditions | The shopper can continue evaluation on the seller website. |
| Related Requirements | FR-22, FR-23, FR-24 |

### UC-07 View and Reopen Search History

| Field | Description |
| --- | --- |
| Actors | Authenticated Shopper |
| Preconditions | The shopper has performed at least one saved comparison. |
| Trigger | The shopper opens Search History or selects a recent search. |
| Main Success Scenario | 1. Frontend requests GET /api/comparisons/history.<br>2. Backend returns authorized saved searches.<br>3. Frontend displays query, timestamp, and best price summary.<br>4. Shopper selects one saved search.<br>5. Frontend requests GET /api/comparisons/<search_id> and maps saved results back into the comparison display. |
| Alternate / Exception Flows | - If history is empty, the frontend displays an empty state.<br>- If the user is not authorized for a search ID, the backend returns HTTP 403. |
| Postconditions | The shopper can review previous results without re-scraping external stores. |
| Related Requirements | FR-26, FR-27, FR-29 |

### UC-08 Clear Search History

| Field | Description |
| --- | --- |
| Actors | Authenticated Shopper |
| Preconditions | The shopper has saved comparison history. |
| Trigger | The shopper chooses Clear History and confirms. |
| Main Success Scenario | 1. Frontend shows a confirmation prompt.<br>2. After confirmation, frontend calls DELETE /api/comparisons/history/clear.<br>3. Backend authorizes the target user.<br>4. Backend deletes the user's comparison searches and results.<br>5. Frontend removes history from the current view. |
| Alternate / Exception Flows | - If the shopper cancels, no request is sent.<br>- If a non-staff user targets another user_id, backend returns HTTP 403. |
| Postconditions | The user's saved comparison history is removed. |
| Related Requirements | FR-28, FR-29, NFR-D-01 |

### UC-09 Update Account Location

| Field | Description |
| --- | --- |
| Actors | Authenticated Shopper |
| Preconditions | The shopper is on the My Account page. |
| Trigger | The shopper selects inside Beirut or outside Beirut. |
| Main Success Scenario | 1. Frontend optimistically updates the location selection.<br>2. Frontend calls PATCH /api/auth/location.<br>3. Backend updates auth_user.location.<br>4. Frontend persists the updated user object and displays success. |
| Alternate / Exception Flows | - If the API call fails, the frontend restores the previous location and displays an error. |
| Postconditions | Future requests can use the shopper's preferred delivery location. |
| Related Requirements | FR-08, FR-18 |

### UC-10 Change Password

| Field | Description |
| --- | --- |
| Actors | Authenticated password-account shopper |
| Preconditions | The shopper is not signed in through Google-only authentication. |
| Trigger | The shopper submits current password, new password, and confirmation. |
| Main Success Scenario | 1. Frontend validates required fields, minimum length, confirmation match, and difference from old password.<br>2. Frontend calls POST /api/auth/password.<br>3. Backend validates old password and password policy.<br>4. Backend saves the new password and returns success.<br>5. Frontend clears the form and displays success. |
| Alternate / Exception Flows | - If old password is wrong, backend returns an error.<br>- If the account is Google-authenticated, the password form is hidden. |
| Postconditions | The user's password credential is updated. |
| Related Requirements | FR-09, NFR-S-01 |

### UC-11 Use Source Diagnostic Endpoint

| Field | Description |
| --- | --- |
| Actors | Developer / Maintainer |
| Preconditions | Backend is running, the maintainer is authenticated, and a source key is known. |
| Trigger | Developer sends a source-specific diagnostic API request. |
| Main Success Scenario | 1. Developer posts a query to /api/search/<source_key> or /api/search-with-details/<source_key> with a valid JWT bearer token.<br>2. Backend validates source key and query.<br>3. Backend runs the matching adapter and returns normalized output.<br>4. Developer uses results to verify or debug adapter behavior. |
| Alternate / Exception Flows | - Missing or invalid authentication returns an authentication error.<br>- Unknown source keys return HTTP 404.<br>- Adapters without detailed pricing return a not-implemented or fallback pricing response. |
| Postconditions | The maintainer has source-specific evidence for debugging or demonstration. |
| Related Requirements | FR-31 |

## 7. Appendix

### A.1 Primary Comparison Sequence

```text
Authenticated Shopper
  -> React Home: submit query
  -> Django /api/comparisons/compare: POST { query, optional location }
  -> Adapter Registry: list registered sources
  -> ThreadPoolExecutor: run one task per source
  -> Store Adapter: search source
  -> Gemini Filter: select products matching query intent
  -> Store Adapter: calculate detailed delivered pricing
  -> Scoring Utility: compute price, delivery, trust, final score
  -> PostgreSQL: save ComparisonSearch and ComparisonResult records
  -> React Home: return sorted results and metadata
  -> Shopper: display best deal, rankings, details, and seller links
```

### A.2 Data Dictionary

| Data Element | Type | Model or Store | Description |
| --- | --- | --- | --- |
| auth_user.location | boolean | Custom migration column on Django auth_user | True means inside Beirut; False means outside Beirut. |
| SearchJob.query | string | scraping.SearchJob | Original single-source search query. |
| SearchJob.source | string | scraping.SearchJob | Adapter key used for the single-source job. |
| SearchJob.status | string | scraping.SearchJob | PENDING, RUNNING, DONE, or FAILED status indicator. |
| Offer.title | string | scraping.Offer | Normalized product title. |
| Offer.url | URL | scraping.Offer | External seller product URL. |
| Offer.image_url | URL nullable | scraping.Offer | External image URL when available. |
| Offer.item_price | decimal | scraping.Offer | Base item price before delivered-price adjustments. |
| Offer.currency | string | scraping.Offer | Currency code, default USD. |
| Offer.in_stock | boolean nullable | scraping.Offer | Stock signal when available. |
| ComparisonSearch.user | foreign key | comparisons.ComparisonSearch | Owner of the saved comparison. |
| ComparisonSearch.query | string | comparisons.ComparisonSearch | Original all-source comparison query. |
| ComparisonSearch.location | string | comparisons.ComparisonSearch | Delivery location used for the comparison. |
| ComparisonSearch.min_price | decimal nullable | comparisons.ComparisonSearch | Lowest total price among successful results. |
| ComparisonSearch.sites_checked | integer | comparisons.ComparisonSearch | Number of registered adapters checked. |
| ComparisonSearch.sites_succeeded | integer | comparisons.ComparisonSearch | Number of adapters returning successful results. |
| TrendingSearch.query | derived string | comparisons.get_trending_searches | Trimmed lowercase query derived from ComparisonSearch.query for case-insensitive trending counts. |
| ComparisonResult.source | string | comparisons.ComparisonResult | Adapter/store key for the result. |
| ComparisonResult.product_title | string | comparisons.ComparisonResult | Saved product title. |
| ComparisonResult.product_url | URL | comparisons.ComparisonResult | External product URL. |
| ComparisonResult.item_price | decimal | comparisons.ComparisonResult | Base item price. |
| ComparisonResult.shipping_fee | decimal nullable | comparisons.ComparisonResult | Shipping cost when known. |
| ComparisonResult.tax_amount | decimal nullable | comparisons.ComparisonResult | Tax amount when known. |
| ComparisonResult.total_price | decimal | comparisons.ComparisonResult | Delivered price used for ranking. |
| ComparisonResult.delivery_days | integer nullable | comparisons.ComparisonResult | Parsed numeric delivery estimate. |
| ComparisonResult.store_rating | decimal nullable | comparisons.ComparisonResult | Store trust signal from adapter metadata. |
| ComparisonResult.score | decimal | comparisons.ComparisonResult | Final weighted score out of 10. |
| ComparisonResult.pricing_breakdown | JSON nullable | comparisons.ComparisonResult | Raw detailed pricing payload for auditability. |

### A.3 Requirement Traceability Matrix

| Feature Area | Requirements | Use Cases | Implementation Evidence |
| --- | --- | --- | --- |
| Register/Login/Auth | FR-01 to FR-07 | UC-01, UC-02, UC-03 | authentication serializers/views, authService, LoginSection, RegisterSection |
| Account management | FR-08, FR-09 | UC-09, UC-10 | authentication views, MyAccount, authService |
| Comparison search | FR-10 to FR-21 | UC-04 | comparisons.views, scraping.services, ai_filter, adapters, scoring |
| Result display | FR-22 to FR-24 | UC-06 | Home component, productService |
| History and trending | FR-25 to FR-30 | UC-05, UC-07, UC-08 | ComparisonSearch/Result models, comparison views, historyService, ProductService, Home, SearchHistory |
| Diagnostics | FR-31 | UC-11 | api.views, api.urls |