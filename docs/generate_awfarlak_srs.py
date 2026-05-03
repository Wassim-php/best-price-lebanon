from __future__ import annotations

import html
import re
import zipfile
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = Path(r"C:\Users\naous\Downloads\SRS Template v4.docx")
OUTPUT_DOCX = ROOT / "docs" / "Awfarlak_SRS_v1.0.docx"
OUTPUT_MD = ROOT / "docs" / "Awfarlak_SRS_v1.0.md"

PROJECT_NAME = "Awfarlak"
PROJECT_SUBTITLE = "Software Requirements Specification for a Price and Delivery Comparison Platform in Lebanon"
VERSION = "1.1"
AUTHOR = "Naous"
DOC_DATE = "May 3, 2026"


TOC = [
    ("1", "Introduction"),
    ("1.1", "Purpose and Intended Audience"),
    ("1.2", "Project Scope"),
    ("1.3", "Terms, Definitions, and Acronyms"),
    ("1.4", "References"),
    ("2", "Overall Description"),
    ("2.1", "Product Perspective"),
    ("2.2", "Product Features"),
    ("2.3", "User Classes and Characteristics"),
    ("2.4", "Operating Environment"),
    ("2.5", "Design and Implementation Constraints"),
    ("2.6", "Assumptions and Dependencies"),
    ("3", "System Features"),
    ("3.1", "Functional Requirements"),
    ("3.2", "Supported Store Sources"),
    ("3.3", "Comparison Scoring Requirements"),
    ("4", "Non-Functional Requirements"),
    ("5", "External Interface Requirements"),
    ("5.1", "User Interfaces"),
    ("5.2", "Hardware Interfaces"),
    ("5.3", "Software Interfaces"),
    ("5.4", "Communication Interfaces"),
    ("6", "Detailed Use Cases"),
    ("7", "Appendix"),
]


terms = [
    ("Adapter", "A backend component that knows how to search one external store and normalize that store's product data into the common OfferData format."),
    ("AI Filtering", "The use of Google Gemini to select search results that match the user's actual product intent and exclude unrelated accessories, bundles, or different product variants."),
    ("Awfarlak", "The project name and frontend brand for the Lebanese price comparison platform."),
    ("Bearer Token", "A token sent in the HTTP Authorization header to prove that a user is authenticated."),
    ("Comparison Search", "A saved user search containing the original query, delivery location, metadata, and one or more ranked comparison results."),
    ("Delivery Location", "A simplified location category used for shipping estimates: inside Beirut or outside Beirut."),
    ("Delivered Price", "The final estimated cost shown to the user, calculated as item price plus shipping fee plus tax amount when available."),
    ("Django REST Framework (DRF)", "The backend framework used to create JSON API endpoints for the React frontend."),
    ("External Store", "An e-commerce website outside the system, such as 961Souq, Ayoub Computers, MobileLeb, HiCart, or Ishtari."),
    ("JWT", "JSON Web Token. The authentication mechanism used by the backend for protected API calls."),
    ("Offer", "A normalized product result returned from a store adapter. It includes title, product URL, image URL, price, currency, and stock status."),
    ("PostgreSQL", "The relational database used to persist users, search jobs, offers, comparison searches, and comparison results."),
    ("React", "The frontend JavaScript framework used to build the user interface."),
    ("Redis", "The in-memory service configured as the Celery broker for background processing."),
    ("Search Job", "A backend record representing a search request sent to one store source."),
    ("Store Rating", "A manually assigned quality or trust signal for each source, measured from 0.0 to 5.0 and used in the scoring formula."),
    ("Trending Search", "A normalized comparison query that appears among the top searched queries in saved comparison history."),
    ("Vite", "The frontend development and build tool used by the React application."),
]


references = [
    ("REF-01", "Backend source repository", r"C:\Users\naous\senior-project\best-price-lebanon"),
    ("REF-02", "Frontend source repository", r"C:\Users\naous\senior-project\awfarlak-react"),
    ("REF-03", "Backend README: project overview, architecture, planned sources, and technology stack", r"best-price-lebanon\readme.md"),
    ("REF-04", "Frontend README and implementation: API client, token handling, Vite proxy, routes, and services", r"awfarlak-react\README.md and awfarlak-react\src"),
    ("REF-05", "Backend Docker Compose configuration for Django, PostgreSQL, Redis, and Celery", r"best-price-lebanon\docker-compose.yml"),
    ("REF-06", "Backend comparison and scoring implementation", r"best-price-lebanon\comparisons"),
    ("REF-07", "Backend scraping registry and source adapters", r"best-price-lebanon\scraping"),
    ("REF-08", "Frontend React pages, services, and reusable components", r"awfarlak-react\src"),
]


product_features = [
    ("Account creation and sign-in", "Users can create accounts, sign in with username and password, or sign in using Google when configured."),
    ("Protected shopping dashboard", "Authenticated users access a dashboard with comparison search, recent searches, and ranking results."),
    ("Multi-store product comparison", "A single product query is searched across supported stores through source-specific adapters."),
    ("AI-assisted product matching", "The backend can filter raw store results so accessories and wrong product variants are not treated as valid cheapest matches."),
    ("Delivered price estimation", "The system calculates item price, shipping, tax, total price, delivery time, and delivery days when store data or source rules are available."),
    ("Recommendation scoring", "Results are ranked using weighted price, delivery, and trust sub-scores."),
    ("Best deal and category highlights", "The frontend highlights the best overall deal and separately identifies best price, best delivery, and best reliability."),
    ("Expandable result details", "Users can inspect item price, shipping, delivery time, and score breakdown before opening the seller page."),
    ("Search history", "Authenticated searches can be saved, listed, reopened, and cleared."),
    ("Trending searches", "The dashboard lists the three most-used normalized comparison queries without exposing search counts."),
    ("Account settings", "Users can update delivery location and password. Google accounts do not display password-change controls."),
    ("Admin visibility", "Backend staff users can view comparison history beyond their own user records through the API permissions implemented in the comparison views."),
]


user_classes = [
    ("Registered Shopper", "Primary user", "Basic web browsing skill. Uses the system to compare products, review price and delivery options, and open external seller pages."),
    ("Returning Shopper", "Primary user", "Same as registered shopper, with additional use of saved history to revisit previous searches."),
    ("Administrator / Evaluator", "Secondary user", "Moderate technical skill. Uses Django admin or staff-permitted API access to inspect records, validate behavior, and review source performance."),
    ("Developer / Maintainer", "Supporting user", "Advanced technical skill. Maintains adapters, environment variables, Docker services, scoring logic, API contracts, and frontend integration."),
]


constraints = [
    "The system depends on external e-commerce websites whose HTML, APIs, prices, availability, and anti-bot rules may change without notice.",
    "Google Gemini quota and API availability affect AI filtering; the backend returns a specific quota error when most source failures are caused by AI quota exhaustion.",
    "Deployment values such as DEBUG, DJANGO_SECRET_KEY, allowed hosts, API keys, OAuth client IDs, and database credentials must be supplied through environment variables.",
    "The user location model is intentionally simple: inside Beirut or outside Beirut. It does not yet calculate shipping by exact address, district, or GPS coordinates.",
    "The frontend sends the user's saved inside/outside Beirut location with comparison requests; if a backend request omits location, the backend default remains outside Beirut.",
    "The application does not process payments, place orders, reserve products, manage returns, or guarantee that external store prices remain unchanged after the user leaves the application.",
    "Some source adapters rely on HTTP scraping, some use API extraction, and at least one source uses browser automation. Performance and reliability will vary by store.",
    "The frontend stores access and refresh tokens in localStorage. This works for the current implementation but should be reviewed during production security hardening.",
]


assumptions = [
    "Users have an internet-connected device with a modern browser.",
    "Backend, database, Redis, and any worker processes are running when comparisons are requested.",
    "External store websites are reachable from the server environment.",
    "Prices are treated as USD unless a source explicitly returns another supported currency.",
    "Store rating values are manually maintained by the development team until a live review-data integration is introduced.",
    "Search queries are product names or product-like text. Source-specific product URLs can be used by diagnostic product-details endpoints, but the primary user workflow is product-name comparison.",
    "The user understands that final purchase decisions happen on external seller websites.",
]


functional_requirements = [
    ("FR-01", "User registration", "High", "The system shall allow a visitor to register with username, email, password, and delivery location.", "A valid registration creates a Django user, stores the location flag, and returns a usable authentication response or validation errors."),
    ("FR-02", "Email uniqueness validation", "High", "The system shall reject registration when the email address already belongs to another user.", "Duplicate email submission returns a validation error without creating a second user."),
    ("FR-03", "Password validation", "High", "The frontend and backend shall require passwords of at least eight characters and backend validators shall reject weak passwords.", "Weak password submissions display an error and no account is created or changed."),
    ("FR-04", "Password login", "High", "The system shall authenticate registered users by username and password.", "Valid credentials return user data plus JWT access and refresh tokens; invalid credentials return HTTP 401."),
    ("FR-05", "Google login", "Medium", "The system shall support Google Sign-In when Google client IDs are configured.", "A verified Google ID token creates or locates a user, assigns an unusable password for new Google-only accounts, and returns JWT tokens."),
    ("FR-06", "Logout", "High", "The system shall allow authenticated users to log out by blacklisting the refresh token and clearing frontend authentication storage.", "Logout removes tokens from localStorage and returns a success message when the refresh token is valid."),
    ("FR-07", "Protected routes", "High", "The frontend shall prevent unauthenticated visitors from accessing home, search history, account, and help pages.", "Unauthenticated navigation redirects to the login page."),
    ("FR-08", "Update delivery location", "High", "The system shall allow authenticated users to change the stored inside/outside Beirut location.", "A successful PATCH request updates auth_user.location and the frontend reflects the new selection."),
    ("FR-09", "Change password", "Medium", "The system shall allow password-authenticated users to change their password after entering the current password.", "The backend validates the old password and new password; Google-authenticated accounts do not show password-change UI."),
    ("FR-10", "Submit comparison query", "High", "The system shall allow an authenticated user to submit a product search query from the dashboard.", "A non-empty query sends POST /api/comparisons/compare and displays loading state while the backend searches."),
    ("FR-11", "Reject empty search", "High", "The frontend and backend shall reject blank product queries.", "The user sees a clear error and the backend returns HTTP 400 when query is missing."),
    ("FR-12", "Parallel source search", "High", "The backend shall search registered store adapters in parallel to reduce total comparison time.", "compare_all_sources submits one task per adapter through a ThreadPoolExecutor and records failed sources separately."),
    ("FR-13", "Source adapter normalization", "High", "Each store adapter shall normalize product data into title, URL, image URL, item price, currency, and stock status.", "Saved Offer records and comparison responses use the common normalized structure."),
    ("FR-14", "AI intent filtering", "High", "When comparing across sources, the backend shall filter store results by product intent before selecting the cheapest candidate from each source.", "Accessories and wrong variants are excluded according to the Gemini prompt rules; if filtering fails non-quota, the source returns no filtered results rather than an unsafe raw cheapest result."),
    ("FR-15", "AI quota handling", "High", "The backend shall return a clear quota response if Gemini quota exhaustion prevents most source searches.", "The compare endpoint returns HTTP 429 with AI_QUOTA_EXCEEDED metadata when quota failures dominate."),
    ("FR-16", "Cheapest candidate selection", "High", "For each source, after AI filtering, the backend shall select the cheapest matching product for detailed pricing.", "Each successful source contributes at most one candidate to the all-sources comparison."),
    ("FR-17", "Detailed delivered pricing", "High", "The backend shall calculate or extract item price, shipping fee, tax amount, total price, currency, and delivery time when supported by the adapter.", "The response includes pricing fields and a pricing breakdown when available."),
    ("FR-18", "Location-aware shipping", "Medium", "The backend shall use the provided delivery location when calculating source-specific shipping and delivery time.", "Adapters with inside/outside Beirut rules select the proper shipping fee and delivery range."),
    ("FR-19", "Graceful source failure", "High", "A failure in one store source shall not cancel the entire comparison if other sources succeed.", "The response includes successful results plus metadata listing failed sources and errors."),
    ("FR-20", "No-results response", "High", "If no supported source returns a valid product, the backend shall return a not-found response.", "The frontend displays a no-products or search-error state instead of an empty broken result grid."),
    ("FR-21", "Comparison scoring", "High", "The system shall calculate final score and sub-scores for price, delivery, and trust.", "Each result includes final score, price_score, delivery_score, and trust_score."),
    ("FR-22", "Best deal presentation", "High", "The frontend shall present the highest-scoring product as the best deal.", "The best deal card displays product image or fallback icon, title, source, stock status, total price, delivery, store rating, and score."),
    ("FR-23", "Category ranking presentation", "Medium", "The frontend shall highlight best price, best delivery, and best reliability where matching results exist.", "Top Rankings cards display category badges and can be expanded for details."),
    ("FR-24", "Open external seller", "High", "The frontend shall let users open a product on the external seller website.", "The Go to Store or View on Store link opens the product URL in a new browser context."),
    ("FR-25", "Save comparison history", "High", "The backend shall save authenticated comparison searches by default.", "ComparisonSearch and ComparisonResult records are created with metadata and result details unless save is false."),
    ("FR-26", "Recent search display", "Medium", "The dashboard shall show recent searches for quick access.", "The home page fetches history, normalizes it, and displays the latest three searches."),
    ("FR-27", "Full search history", "Medium", "The system shall provide a full history page for authenticated users.", "Users can view previous queries, timestamps, best price, and open a previous search back in the home workflow."),
    ("FR-28", "Clear history", "Medium", "The system shall let users clear their own comparison history.", "A confirmed clear action deletes the user's ComparisonSearch and ComparisonResult records and updates the UI."),
    ("FR-29", "History authorization", "High", "Users shall not access another regular user's comparison history.", "Non-staff users are limited to their own records; staff users may view or clear targeted user history."),
    ("FR-30", "Trending searches", "Medium", "The system shall list the top three most-used saved comparison queries as trending searches.", "GET /api/comparisons/trending returns at most three normalized queries, counts upper/lower case together, trims whitespace, and does not expose search counts."),
    ("FR-31", "Single-source diagnostic endpoints", "Low", "The backend shall expose authenticated source-specific search and product-details endpoints for testing adapters and detailed pricing.", "Authenticated POST /api/search/<source>, /api/product-details/<source>, and /api/search-with-details/<source> return source-scoped results or meaningful errors."),
]


source_adapters = [
    ("961souq", "961Souq", "https://961souq.com", "Selenium checkout simulation for detailed pricing; source rating 4.5; typical 4 delivery days."),
    ("ayoubcomputers", "Ayoub Computers", "https://ayoubcomputers.com", "BigCommerce Storefront GraphQL search; source rating 4.7; typical 3 delivery days."),
    ("abdeltahan", "Abed Tahan", "https://abedtahan.com", "Shopify search parsing with fixed shipping rules; source rating 4.6; typical 3 delivery days."),
    ("mobileleb", "MobileLeb", "https://mobileleb.com", "Shopify search parsing; source rating 4.3; typical 3 delivery days."),
    ("hicart", "HiCart", "https://www.hicart.com", "HTTP search parsing with fixed shipping; source rating 4.0; typical 5 delivery days."),
    ("outgeeked", "OutGeeked", "https://outgeeked.net", "Shopify search parsing; source rating 4.4; typical 4 delivery days."),
    ("zoodmall", "ZoodMall", "https://www.zoodmall.com.lb", "ZoodMall web pages with Selenium support; fixed Lebanon shipping estimate; source rating 3.0; typical 5 delivery days; anti-bot behavior may affect availability."),
    ("phonefinity", "Phonefinity", "https://phonefinity.net", "WooCommerce search parsing; source rating 4.8; typical 3 delivery days."),
    ("dslrzone", "DSLR Zone", "https://www.dslr-zone.com", "WooCommerce Store API first, HTML fallback; source rating 4.5; typical 4 delivery days."),
    ("ishtari", "Ishtari", "https://www.ishtari.com", "Mobile API and HTML fallback strategies; source rating 4.1; typical 4 delivery days."),
    ("beytech", "Beytech", "https://www.beytech.com.lb", "WooCommerce search parsing; source rating 4.5; typical 2 delivery days."),
    ("ezonelb", "Ezone LB", "https://ezonelb.com", "WooCommerce Store API with HTML fallback; source rating 4.5; typical 2 delivery days."),
]


pricing_rules = [
    ("961Souq", "Parsed from checkout", "Parsed from checkout when present", "Parsed dynamically; defaults such as 3-5 business days when free shipping is detected."),
    ("Ayoub Computers", "Free shipping", "11 percent of item price", "2-6 business days."),
    ("Abed Tahan", "Free over $350; otherwise $4 inside Beirut or $7 outside Beirut", "None", "2-3 business days inside Beirut or free-shipping orders; 5-7 business days outside Beirut."),
    ("MobileLeb", "$3 inside Beirut; $5 outside Beirut", "None", "1-2 business days inside Beirut; 3-5 business days outside Beirut."),
    ("HiCart", "$4 flat", "0", "3-7 business days."),
    ("OutGeeked", "$3 flat", "0", "2-5 business days inside Beirut; 5-7 business days outside Beirut."),
    ("ZoodMall", "$4.75 flat Lebanon delivery estimate", "0", "2-7 business days."),
    ("Phonefinity", "$5 flat", "0", "1 business day inside Beirut; 2-4 business days outside Beirut."),
    ("DSLR Zone", "Free at or above $350; $5 below $350", "0", "1-2 business days."),
    ("Ishtari", "$3 inside Beirut; $5 outside Beirut", "0", "2-4 business days inside Beirut; 3-6 business days outside Beirut."),
    ("Beytech", "$5 flat", "0", "2-3 business days."),
    ("Ezone LB", "Free inside Beirut; $3 outside Beirut", "0", "1 business day inside Beirut; 2-3 business days outside Beirut."),
]


nfrs = [
    ("NFR-F-01", "Functional correctness", "High", "A comparison result shall not knowingly rank an unrelated accessory as the best product for a main-device query.", "AI filtering rules and no-unsafe-fallback behavior are in place."),
    ("NFR-F-02", "Input validation", "High", "API endpoints shall reject missing required fields and malformed user input with clear HTTP errors.", "Missing query and product_url paths return HTTP 400."),
    ("NFR-U-01", "Usability", "High", "The primary comparison workflow shall require no more than one query input and one submit action after login.", "Home search bar accepts query and displays results without leaving the page."),
    ("NFR-U-02", "Responsive layout", "High", "The frontend shall support desktop and mobile navigation.", "Sidebar collapses on desktop and becomes a mobile overlay menu below the desktop breakpoint."),
    ("NFR-U-03", "Feedback", "High", "Long-running searches shall display visible progress feedback.", "The frontend rotates loading messages while the comparison request is pending."),
    ("NFR-R-01", "Partial failure tolerance", "High", "The system shall return successful store results even when some sources fail.", "Failed source metadata is returned without discarding successful results."),
    ("NFR-R-02", "Error transparency", "Medium", "The frontend shall display meaningful search, authentication, history, and account update errors.", "Service-layer errors are converted into user-facing messages."),
    ("NFR-P-01", "Comparison performance", "High", "The backend shall attempt source searches concurrently rather than sequentially.", "The comparison view uses ThreadPoolExecutor with configured worker count and per-source timeout handling."),
    ("NFR-P-02", "User waiting expectation", "Medium", "The user interface shall set realistic expectations for comparison duration.", "The loading panel states that searches can take up to 60 seconds depending on store response time."),
    ("NFR-S-01", "Authentication security", "High", "Protected API endpoints shall require JWT authentication.", "Comparison and account endpoints use IsAuthenticated permissions."),
    ("NFR-S-02", "Token lifetime control", "High", "JWT access tokens shall be short-lived and refresh tokens shall rotate and be blacklisted after logout/rotation.", "Configured access lifetime is 30 minutes and refresh lifetime is 7 days with rotation and blacklist enabled."),
    ("NFR-S-03", "Production secret handling", "High", "Production deployments shall use environment variables for secret keys, API keys, OAuth client IDs, database credentials, and allowed hosts.", "No production deployment may rely on development fallback values."),
    ("NFR-M-01", "Maintainability", "High", "Adding a new store shall require implementing a new adapter and registering it in the adapter registry.", "The BaseAdapter and ADAPTERS registry define the integration boundary."),
    ("NFR-M-02", "Testability", "Medium", "Scoring and comparison model behavior shall be covered by automated tests.", "Existing tests validate delivery parsing, rating calculation, model creation, and ordering."),
    ("NFR-C-01", "Compatibility", "Medium", "The frontend shall run in modern browsers supported by React and Vite.", "The application is built with React 19, Vite, Tailwind, axios, and react-router."),
    ("NFR-D-01", "Data retention control", "Medium", "Users shall be able to remove their comparison history.", "Clear history endpoint deletes stored comparison searches and results for the target authorized user."),
    ("NFR-L-01", "Legal and ethical scraping", "High", "The system shall only collect publicly visible product listing and pricing information required for comparison.", "The application does not store payment information, customer data from stores, or private seller records."),
]


ui_interfaces = [
    ("Login page", "/login", "Username/password login, Google Sign-In button when configured, error messages, password visibility toggle, and auth-state synchronization after login."),
    ("Register page", "/register", "Username, email, password, confirm password, inside/outside Beirut selector, conditional address field, terms checkbox, validation messages."),
    ("Home dashboard", "/home", "Search bar, loading state, result cards, best deal card, top ranking cards, other options, top-three trending searches, recent searches, and clear recent history action."),
    ("Search history page", "/search-history", "Full saved search list, timestamp display, best price summary, open-in-home behavior, clear history action."),
    ("My account page", "/account", "Account identity summary, delivery location update controls, password change form for password accounts."),
    ("About and help page", "/about-help", "Plain-language explanation of comparison flow and FAQ."),
    ("Sidebar navigation", "All protected pages", "Responsive navigation links for Home, Search History, My Account, About and Help, and Sign Out."),
]


api_endpoints = [
    ("POST", "/api/auth/register", "Public", "Create account with username, email, password, and location; returns user and JWT tokens."),
    ("POST", "/api/auth/login", "Public", "Authenticate username/password; returns user and JWT tokens."),
    ("POST", "/api/auth/google", "Public", "Verify Google ID token; create or fetch user; return JWT tokens."),
    ("POST", "/api/auth/logout", "Authenticated", "Blacklist refresh token and end session."),
    ("PATCH", "/api/auth/location", "Authenticated", "Update inside/outside Beirut location flag."),
    ("POST", "/api/auth/password", "Authenticated", "Change password after old-password validation."),
    ("POST", "/api/comparisons/compare", "Authenticated", "Search all adapters, compute delivered pricing and scores, optionally save history."),
    ("GET", "/api/comparisons/history", "Authenticated", "List comparison history for the user; staff may view all."),
    ("GET", "/api/comparisons/trending", "Authenticated", "Return the top three normalized saved comparison queries without search counts."),
    ("DELETE", "/api/comparisons/history/clear", "Authenticated", "Delete comparison history for the user; staff may target a user_id."),
    ("GET", "/api/comparisons/<search_id>", "Authenticated", "Return saved comparison search and detailed results."),
    ("DELETE", "/api/comparisons/<search_id>", "Authenticated", "Delete one saved comparison search after authorization check."),
    ("POST", "/api/search/<source_key>", "Authenticated diagnostic/internal", "Run source-specific search, with optional AI filtering and cheapest-only flags."),
    ("POST", "/api/product-details/<source_key>", "Authenticated diagnostic/internal", "Get detailed pricing for a specific product URL from one source."),
    ("POST", "/api/search-with-details/<source_key>", "Authenticated diagnostic/internal", "Search one source, select the cheapest AI-filtered result, and get detailed pricing."),
]


data_dictionary = [
    ("auth_user.location", "boolean", "Custom migration column on Django auth_user", "True means inside Beirut; False means outside Beirut."),
    ("SearchJob.query", "string", "scraping.SearchJob", "Original single-source search query."),
    ("SearchJob.source", "string", "scraping.SearchJob", "Adapter key used for the single-source job."),
    ("SearchJob.status", "string", "scraping.SearchJob", "PENDING, RUNNING, DONE, or FAILED status indicator."),
    ("Offer.title", "string", "scraping.Offer", "Normalized product title."),
    ("Offer.url", "URL", "scraping.Offer", "External seller product URL."),
    ("Offer.image_url", "URL nullable", "scraping.Offer", "External image URL when available."),
    ("Offer.item_price", "decimal", "scraping.Offer", "Base item price before delivered-price adjustments."),
    ("Offer.currency", "string", "scraping.Offer", "Currency code, default USD."),
    ("Offer.in_stock", "boolean nullable", "scraping.Offer", "Stock signal when available."),
    ("ComparisonSearch.user", "foreign key", "comparisons.ComparisonSearch", "Owner of the saved comparison."),
    ("ComparisonSearch.query", "string", "comparisons.ComparisonSearch", "Original all-source comparison query."),
    ("ComparisonSearch.location", "string", "comparisons.ComparisonSearch", "Delivery location used for the comparison."),
    ("ComparisonSearch.min_price", "decimal nullable", "comparisons.ComparisonSearch", "Lowest total price among successful results."),
    ("ComparisonSearch.sites_checked", "integer", "comparisons.ComparisonSearch", "Number of registered adapters checked."),
    ("ComparisonSearch.sites_succeeded", "integer", "comparisons.ComparisonSearch", "Number of adapters returning successful results."),
    ("TrendingSearch.query", "derived string", "comparisons.get_trending_searches", "Trimmed lowercase query derived from ComparisonSearch.query for case-insensitive trending counts."),
    ("ComparisonResult.source", "string", "comparisons.ComparisonResult", "Adapter/store key for the result."),
    ("ComparisonResult.product_title", "string", "comparisons.ComparisonResult", "Saved product title."),
    ("ComparisonResult.product_url", "URL", "comparisons.ComparisonResult", "External product URL."),
    ("ComparisonResult.item_price", "decimal", "comparisons.ComparisonResult", "Base item price."),
    ("ComparisonResult.shipping_fee", "decimal nullable", "comparisons.ComparisonResult", "Shipping cost when known."),
    ("ComparisonResult.tax_amount", "decimal nullable", "comparisons.ComparisonResult", "Tax amount when known."),
    ("ComparisonResult.total_price", "decimal", "comparisons.ComparisonResult", "Delivered price used for ranking."),
    ("ComparisonResult.delivery_days", "integer nullable", "comparisons.ComparisonResult", "Parsed numeric delivery estimate."),
    ("ComparisonResult.store_rating", "decimal nullable", "comparisons.ComparisonResult", "Store trust signal from adapter metadata."),
    ("ComparisonResult.score", "decimal", "comparisons.ComparisonResult", "Final weighted score out of 10."),
    ("ComparisonResult.pricing_breakdown", "JSON nullable", "comparisons.ComparisonResult", "Raw detailed pricing payload for auditability."),
]


use_cases = [
    {
        "id": "UC-01",
        "name": "Create Account",
        "actors": "Visitor",
        "preconditions": "The visitor is not authenticated and can access the register page.",
        "trigger": "The visitor submits the registration form.",
        "main": [
            "Visitor enters username, email, password, password confirmation, location, and accepts terms.",
            "Frontend validates required fields, email format, password strength, confirmation match, and terms acceptance.",
            "Frontend sends username, email, password, and location to POST /api/auth/register.",
            "Backend validates email uniqueness and password policy.",
            "Backend creates a Django user, writes the location flag, and returns authentication data.",
            "Frontend navigates the user to the login page after registration.",
        ],
        "alternates": [
            "If validation fails, the frontend displays field-level errors.",
            "If email is already registered, the backend returns a validation error and the account is not created.",
        ],
        "post": "A new user exists with a stored delivery location.",
        "requirements": "FR-01, FR-02, FR-03",
    },
    {
        "id": "UC-02",
        "name": "Sign In with Password",
        "actors": "Registered Shopper",
        "preconditions": "The shopper has an existing username/password account.",
        "trigger": "The shopper submits the login form.",
        "main": [
            "Shopper enters username and password.",
            "Frontend sends credentials to POST /api/auth/login.",
            "Backend authenticates against Django auth.",
            "Backend returns user details and JWT tokens.",
            "Frontend stores tokens and user data in localStorage.",
            "Frontend navigates to /home.",
        ],
        "alternates": [
            "If credentials are invalid, the backend returns HTTP 401 and the frontend displays an error.",
            "If token storage is cleared later, protected routes redirect back to /login.",
        ],
        "post": "The shopper has an authenticated browser session.",
        "requirements": "FR-04, FR-07, NFR-S-01",
    },
    {
        "id": "UC-03",
        "name": "Sign In with Google",
        "actors": "Visitor or Registered Shopper",
        "preconditions": "Google client ID is configured in the frontend and backend.",
        "trigger": "The user selects Google Sign-In.",
        "main": [
            "Frontend loads the Google Identity script.",
            "Google returns an ID token credential.",
            "Frontend sends the ID token to POST /api/auth/google.",
            "Backend verifies the token audience and verified email status.",
            "Backend finds an existing user by email or creates a new Google-only user.",
            "Backend returns JWT tokens and frontend navigates to /home.",
        ],
        "alternates": [
            "If Google is not configured, the frontend displays setup guidance.",
            "If the email is not verified or token is invalid, the backend rejects the login.",
        ],
        "post": "The user is authenticated with provider metadata set to google.",
        "requirements": "FR-05, FR-07",
    },
    {
        "id": "UC-04",
        "name": "Compare Product Across Stores",
        "actors": "Authenticated Shopper",
        "preconditions": "The shopper is signed in and backend services are available.",
        "trigger": "The shopper submits a product query from the home page.",
        "main": [
            "Frontend verifies the query is not blank.",
            "Frontend sends POST /api/comparisons/compare with the query and the user's normalized saved delivery location.",
            "Backend starts parallel searches across all registered adapters.",
            "Each adapter returns normalized raw offers.",
            "Backend applies AI filtering and selects the cheapest matching candidate for each source.",
            "Backend gets detailed pricing, delivery, and source rating metadata.",
            "Backend calculates scores, sorts results, saves history, and returns the response.",
            "Frontend renders best deal, category rankings, other options, metadata, and external store links.",
        ],
        "alternates": [
            "If one or more sources fail, their errors are listed in metadata and successful results still display.",
            "If no source succeeds, the backend returns HTTP 404 and the frontend displays an error/no-result state.",
            "If Gemini quota is exceeded for most sources, the backend returns HTTP 429 with AI_QUOTA_EXCEEDED.",
        ],
        "post": "The shopper sees ranked delivered-price recommendations and a saved comparison history record exists unless saving is disabled.",
        "requirements": "FR-10 through FR-25, NFR-R-01, NFR-P-01",
    },
    {
        "id": "UC-05",
        "name": "Use Trending Searches",
        "actors": "Authenticated Shopper",
        "preconditions": "The shopper is signed in and at least one comparison search may exist in system history.",
        "trigger": "The shopper opens the home dashboard or selects a trending search item.",
        "main": [
            "Frontend requests GET /api/comparisons/trending with a limit of 3.",
            "Backend normalizes saved query text by trimming whitespace and lowering case.",
            "Backend counts matching normalized queries, orders by count and most recent search time, and returns at most three query values.",
            "Frontend displays the returned queries without showing search counts.",
            "Shopper selects a trending query and the frontend runs a new comparison for that query.",
        ],
        "alternates": [
            "If there are no saved searches, the frontend displays an empty trending-searches message.",
            "If the request fails, the dashboard continues to work without trending suggestions.",
        ],
        "post": "The shopper can quickly launch a comparison based on common searches.",
        "requirements": "FR-30",
    },
    {
        "id": "UC-06",
        "name": "Inspect and Open a Result",
        "actors": "Authenticated Shopper",
        "preconditions": "A comparison response is displayed.",
        "trigger": "The shopper expands a result or clicks the store link.",
        "main": [
            "Shopper selects View Details on a result card.",
            "Frontend reveals item price, shipping, delivery time, and score breakdown.",
            "Shopper selects Go to Store or View on Store.",
            "Browser opens the external product URL.",
        ],
        "alternates": [
            "If no image URL exists, the frontend displays a product icon fallback.",
            "If stock is unknown, the UI avoids claiming availability.",
        ],
        "post": "The shopper can continue evaluation on the seller website.",
        "requirements": "FR-22, FR-23, FR-24",
    },
    {
        "id": "UC-07",
        "name": "View and Reopen Search History",
        "actors": "Authenticated Shopper",
        "preconditions": "The shopper has performed at least one saved comparison.",
        "trigger": "The shopper opens Search History or selects a recent search.",
        "main": [
            "Frontend requests GET /api/comparisons/history.",
            "Backend returns authorized saved searches.",
            "Frontend displays query, timestamp, and best price summary.",
            "Shopper selects one saved search.",
            "Frontend requests GET /api/comparisons/<search_id> and maps saved results back into the comparison display.",
        ],
        "alternates": [
            "If history is empty, the frontend displays an empty state.",
            "If the user is not authorized for a search ID, the backend returns HTTP 403.",
        ],
        "post": "The shopper can review previous results without re-scraping external stores.",
        "requirements": "FR-26, FR-27, FR-29",
    },
    {
        "id": "UC-08",
        "name": "Clear Search History",
        "actors": "Authenticated Shopper",
        "preconditions": "The shopper has saved comparison history.",
        "trigger": "The shopper chooses Clear History and confirms.",
        "main": [
            "Frontend shows a confirmation prompt.",
            "After confirmation, frontend calls DELETE /api/comparisons/history/clear.",
            "Backend authorizes the target user.",
            "Backend deletes the user's comparison searches and results.",
            "Frontend removes history from the current view.",
        ],
        "alternates": [
            "If the shopper cancels, no request is sent.",
            "If a non-staff user targets another user_id, backend returns HTTP 403.",
        ],
        "post": "The user's saved comparison history is removed.",
        "requirements": "FR-28, FR-29, NFR-D-01",
    },
    {
        "id": "UC-09",
        "name": "Update Account Location",
        "actors": "Authenticated Shopper",
        "preconditions": "The shopper is on the My Account page.",
        "trigger": "The shopper selects inside Beirut or outside Beirut.",
        "main": [
            "Frontend optimistically updates the location selection.",
            "Frontend calls PATCH /api/auth/location.",
            "Backend updates auth_user.location.",
            "Frontend persists the updated user object and displays success.",
        ],
        "alternates": [
            "If the API call fails, the frontend restores the previous location and displays an error.",
        ],
        "post": "Future requests can use the shopper's preferred delivery location.",
        "requirements": "FR-08, FR-18",
    },
    {
        "id": "UC-10",
        "name": "Change Password",
        "actors": "Authenticated password-account shopper",
        "preconditions": "The shopper is not signed in through Google-only authentication.",
        "trigger": "The shopper submits current password, new password, and confirmation.",
        "main": [
            "Frontend validates required fields, minimum length, confirmation match, and difference from old password.",
            "Frontend calls POST /api/auth/password.",
            "Backend validates old password and password policy.",
            "Backend saves the new password and returns success.",
            "Frontend clears the form and displays success.",
        ],
        "alternates": [
            "If old password is wrong, backend returns an error.",
            "If the account is Google-authenticated, the password form is hidden.",
        ],
        "post": "The user's password credential is updated.",
        "requirements": "FR-09, NFR-S-01",
    },
    {
        "id": "UC-11",
        "name": "Use Source Diagnostic Endpoint",
        "actors": "Developer / Maintainer",
        "preconditions": "Backend is running, the maintainer is authenticated, and a source key is known.",
        "trigger": "Developer sends a source-specific diagnostic API request.",
        "main": [
            "Developer posts a query to /api/search/<source_key> or /api/search-with-details/<source_key> with a valid JWT bearer token.",
            "Backend validates source key and query.",
            "Backend runs the matching adapter and returns normalized output.",
            "Developer uses results to verify or debug adapter behavior.",
        ],
        "alternates": [
            "Missing or invalid authentication returns an authentication error.",
            "Unknown source keys return HTTP 404.",
            "Adapters without detailed pricing return a not-implemented or fallback pricing response.",
        ],
        "post": "The maintainer has source-specific evidence for debugging or demonstration.",
        "requirements": "FR-31",
    },
]


traceability = [
    ("Register/Login/Auth", "FR-01 to FR-07", "UC-01, UC-02, UC-03", "authentication serializers/views, authService, LoginSection, RegisterSection"),
    ("Account management", "FR-08, FR-09", "UC-09, UC-10", "authentication views, MyAccount, authService"),
    ("Comparison search", "FR-10 to FR-21", "UC-04", "comparisons.views, scraping.services, ai_filter, adapters, scoring"),
    ("Result display", "FR-22 to FR-24", "UC-06", "Home component, productService"),
    ("History and trending", "FR-25 to FR-30", "UC-05, UC-07, UC-08", "ComparisonSearch/Result models, comparison views, historyService, ProductService, Home, SearchHistory"),
    ("Diagnostics", "FR-31", "UC-11", "api.views, api.urls"),
]


architecture_diagram = """User Browser
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
PostgreSQL persistence + Redis/Celery infrastructure"""


sequence_diagram = """Authenticated Shopper
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
  -> Shopper: display best deal, rankings, details, and seller links"""


def esc(text: object) -> str:
    return html.escape(str(text), quote=True)


def run(text: str, *, bold: bool = False, italic: bool = False, size: int | None = None, font: str | None = None) -> str:
    props = []
    if bold:
        props.append("<w:b/>")
    if italic:
        props.append("<w:i/>")
    if size:
        props.append(f'<w:sz w:val="{size}"/><w:szCs w:val="{size}"/>')
    if font:
        props.append(f'<w:rFonts w:ascii="{esc(font)}" w:hAnsi="{esc(font)}" w:cs="{esc(font)}"/>')
    prop_xml = f"<w:rPr>{''.join(props)}</w:rPr>" if props else ""

    parts = str(text).split("\n")
    inner = []
    for i, part in enumerate(parts):
        if i:
            inner.append("<w:br/>")
        preserve = ' xml:space="preserve"' if part.startswith(" ") or part.endswith(" ") else ""
        inner.append(f"<w:t{preserve}>{esc(part)}</w:t>")
    return f"<w:r>{prop_xml}{''.join(inner)}</w:r>"


def paragraph(
    text: str = "",
    *,
    style: str | None = None,
    align: str | None = None,
    bold: bool = False,
    italic: bool = False,
    size: int | None = None,
    font: str | None = None,
    before: int | None = None,
    after: int | None = 120,
) -> str:
    ppr = []
    if style:
        ppr.append(f'<w:pStyle w:val="{style}"/>')
    if align:
        ppr.append(f'<w:jc w:val="{align}"/>')
    spacing = []
    if before is not None:
        spacing.append(f'w:before="{before}"')
    if after is not None:
        spacing.append(f'w:after="{after}"')
    if spacing:
        ppr.append(f"<w:spacing {' '.join(spacing)}/>")
    ppr_xml = f"<w:pPr>{''.join(ppr)}</w:pPr>" if ppr else ""
    return f"<w:p>{ppr_xml}{run(text, bold=bold, italic=italic, size=size, font=font)}</w:p>"


def page_break() -> str:
    return '<w:p><w:r><w:br w:type="page"/></w:r></w:p>'


def heading(number: str, title: str, level: int = 1) -> str:
    style = f"Heading{level}"
    return paragraph(f"{number} {title}", style=style, bold=True, after=180)


def bullet(text: str) -> str:
    return paragraph(f"- {text}", style="ListParagraph", after=80)


def code_block(text: str) -> str:
    blocks = []
    for line in text.splitlines():
        ppr = (
            '<w:pPr><w:pStyle w:val="NoSpacing"/>'
            '<w:shd w:val="clear" w:color="auto" w:fill="F2F2F2"/>'
            '<w:ind w:left="360"/>'
            '<w:spacing w:after="0"/></w:pPr>'
        )
        blocks.append(f"<w:p>{ppr}{run(line or ' ', font='Courier New', size=18)}</w:p>")
    return "".join(blocks)


def toc_field_with_result() -> str:
    # Word can update this field after pagination, while the fallback result
    # keeps the document readable immediately after generation.
    parts = [
        '<w:p><w:r><w:fldChar w:fldCharType="begin"/></w:r>'
        '<w:r><w:instrText xml:space="preserve"> TOC \\o "1-3" \\h \\z \\u </w:instrText></w:r>'
        '<w:r><w:fldChar w:fldCharType="separate"/></w:r></w:p>'
    ]
    for number, title in TOC:
        indent = "    " if number.count(".") else ""
        parts.append(paragraph(f"{indent}{number} {title}", after=20))
    parts.append('<w:p><w:r><w:fldChar w:fldCharType="end"/></w:r></w:p>')
    return "".join(parts)


def table(rows: list[list[object]], widths: list[int] | None = None) -> str:
    if not rows:
        return ""
    col_count = len(rows[0])
    if widths is None:
        widths = [int(9000 / col_count)] * col_count
    tbl = [
        "<w:tbl>",
        "<w:tblPr>",
        '<w:tblStyle w:val="TableGrid"/>',
        '<w:tblW w:w="0" w:type="auto"/>',
        '<w:tblBorders>'
        '<w:top w:val="single" w:sz="4" w:space="0" w:color="BFBFBF"/>'
        '<w:left w:val="single" w:sz="4" w:space="0" w:color="BFBFBF"/>'
        '<w:bottom w:val="single" w:sz="4" w:space="0" w:color="BFBFBF"/>'
        '<w:right w:val="single" w:sz="4" w:space="0" w:color="BFBFBF"/>'
        '<w:insideH w:val="single" w:sz="4" w:space="0" w:color="BFBFBF"/>'
        '<w:insideV w:val="single" w:sz="4" w:space="0" w:color="BFBFBF"/>'
        '</w:tblBorders>',
        "</w:tblPr>",
        "<w:tblGrid>",
    ]
    for width in widths:
        tbl.append(f'<w:gridCol w:w="{width}"/>')
    tbl.append("</w:tblGrid>")

    for row_i, row in enumerate(rows):
        tbl.append("<w:tr>")
        for col_i, cell in enumerate(row):
            header = row_i == 0
            shading = '<w:shd w:val="clear" w:color="auto" w:fill="D9EAF7"/>' if header else ""
            width = widths[col_i] if col_i < len(widths) else widths[-1]
            tbl.append(f'<w:tc><w:tcPr><w:tcW w:w="{width}" w:type="dxa"/>{shading}</w:tcPr>')
            cell_text = str(cell)
            for para in cell_text.split("\n"):
                tbl.append(paragraph(para, bold=header, after=60))
            tbl.append("</w:tc>")
        tbl.append("</w:tr>")
    tbl.append("</w:tbl>")
    tbl.append(paragraph("", after=120))
    return "".join(tbl)


def build_document_xml() -> str:
    body: list[str] = []

    # Title page
    body.append(paragraph("Software Requirements Specification", style="Title", align="center", bold=True, size=44, after=300))
    body.append(paragraph("for", align="center", italic=True, size=24, after=120))
    body.append(paragraph(PROJECT_NAME, align="center", bold=True, size=40, after=220))
    body.append(paragraph(PROJECT_SUBTITLE, align="center", size=24, after=500))
    body.append(paragraph(f"Version {VERSION}", align="center", bold=True, size=24, after=160))
    body.append(paragraph(f"Prepared by {AUTHOR}", align="center", size=24, after=160))
    body.append(paragraph(DOC_DATE, align="center", size=24, after=420))
    body.append(paragraph("Senior Project Submission", align="center", italic=True, size=22, after=120))
    body.append(paragraph("Prepared from the implemented Django backend and React frontend repositories.", align="center", size=20, after=120))
    body.append(page_break())

    body.append(paragraph("Revision History", style="Heading1", bold=True))
    body.append(table([
        ["Name", "Date", "Reason for Changes", "Version"],
        [AUTHOR, "May 2, 2026", "Initial complete SRS created for senior project submission.", "1.0"],
        [AUTHOR, DOC_DATE, "Updated to match the current Awfarlak backend/frontend implementation, 12-source registry, authenticated source endpoints, trending searches, environment-based secrets, and current UI behavior.", VERSION],
    ], [2200, 1800, 4200, 1200]))

    body.append(paragraph("Table of Contents", style="Heading1", bold=True))
    body.append(toc_field_with_result())
    body.append(page_break())

    body.append(heading("1.", "Introduction", 1))
    body.append(heading("1.1", "Purpose and Intended Audience", 2))
    body.append(paragraph(
        f"This Software Requirements Specification defines the required external behavior, major constraints, interfaces, data expectations, and use cases for {PROJECT_NAME}. "
        "The document is intended for the project evaluator, instructor, development team, testers, and future maintainers. It explains what the system shall do from the user's perspective while also giving enough technical detail to verify that the React frontend and Django backend satisfy the senior project goals."
    ))
    body.append(paragraph(
        "The SRS is written for a mixed audience. Non-technical readers can understand the product scope and user workflows, while technical readers can trace requirements to API endpoints, data models, source adapters, and scoring logic."
    ))

    body.append(heading("1.2", "Project Scope", 2))
    body.append(paragraph(
        f"{PROJECT_NAME} is a web-based product comparison system for shoppers in Lebanon. The system lets authenticated users search once for a product and compare estimated delivered prices, delivery times, and trust-related signals across the supported store sources registered in the backend. "
        "The project includes a React/Vite frontend, a Django REST backend, PostgreSQL persistence, Redis/Celery infrastructure, store-specific scraping adapters, Google OAuth login support, and Google Gemini product-intent filtering."
    ))
    body.append(paragraph(
        "The system will compare product offers, estimate delivered cost, rank results, and save comparison history. It will not process payments, purchase products, reserve inventory, provide live seller customer support, guarantee seller availability after redirection, or replace the final checkout process on external stores."
    ))

    body.append(heading("1.3", "Terms, Definitions, and Acronyms", 2))
    body.append(table([["Term", "Definition"], *terms], [2200, 6800]))

    body.append(heading("1.4", "References", 2))
    body.append(table([["ID", "Reference", "Location or Source"], *references], [1200, 4500, 3300]))

    body.append(heading("2.", "Overall Description", 1))
    body.append(heading("2.1", "Product Perspective", 2))
    body.append(paragraph(
        f"{PROJECT_NAME} is a stand-alone comparison platform that interfaces with external store websites and APIs. The product's frontend runs in the user's browser, while the backend coordinates authentication, comparison execution, source adapters, AI filtering, scoring, and persistence. "
        "The product does not own or modify store inventory. It acts as a shopping assistant that gathers public product information, normalizes it, and presents ranked recommendations."
    ))
    body.append(paragraph("High-level architecture:"))
    body.append(code_block(architecture_diagram))

    body.append(heading("2.2", "Product Features", 2))
    body.append(table([["Feature", "Description"], *product_features], [2800, 6200]))

    body.append(heading("2.3", "User Classes and Characteristics", 2))
    body.append(table([["User Class", "Priority", "Characteristics"], *user_classes], [2600, 1600, 4800]))

    body.append(heading("2.4", "Operating Environment", 2))
    env_items = [
        "Frontend: React 19, Vite 7, Tailwind CSS 4, axios, react-router-dom, and lucide-react running in a modern desktop or mobile browser.",
        "Backend: Django 6, Django REST Framework, Simple JWT, django-cors-headers, PostgreSQL, Redis, Celery, requests, BeautifulSoup/lxml, Selenium, webdriver-manager, cloudscraper, and Google Generative AI SDK.",
        "Development ports: React dev server on 5173 and Django API on 8000, with Vite proxying /api requests to the backend.",
        "Docker services: web, db, redis, and celery defined in docker-compose.yml; PostgreSQL exposed as host port 5433 to avoid common local conflicts.",
        "Network: backend requires outbound HTTPS access to external store websites, Google OAuth token verification, and Gemini API when AI filtering is enabled.",
    ]
    for item in env_items:
        body.append(bullet(item))

    body.append(heading("2.5", "Design and Implementation Constraints", 2))
    for item in constraints:
        body.append(bullet(item))

    body.append(heading("2.6", "Assumptions and Dependencies", 2))
    for item in assumptions:
        body.append(bullet(item))

    body.append(heading("3.", "System Features", 1))
    body.append(paragraph(
        "This section describes the system's functional requirements from the client's and user's perspective. Requirement priorities are High, Medium, or Low. High-priority requirements are essential for the senior project demonstration."
    ))
    body.append(heading("3.1", "Functional Requirements", 2))
    body.append(table(
        [["ID", "Name", "Priority", "Requirement", "Acceptance Criteria"], *functional_requirements],
        [850, 1900, 900, 3500, 2850],
    ))

    body.append(heading("3.2", "Supported Store Sources", 2))
    body.append(paragraph(
        "The backend uses a registry of adapters. Each adapter implements search behavior and, when possible, detailed pricing behavior for one external store. The following sources are registered in the current backend implementation."
    ))
    body.append(table([["Adapter Key", "Store", "Base Source", "Implementation Notes"], *source_adapters], [1500, 1700, 2600, 4200]))
    body.append(paragraph("Current delivered-pricing rules and assumptions:"))
    body.append(table([["Store", "Shipping Rule", "Tax Rule", "Delivery Time Rule"], *pricing_rules], [1800, 3000, 1800, 3400]))

    body.append(heading("3.3", "Comparison Scoring Requirements", 2))
    body.append(paragraph(
        "The system shall calculate an overall score out of 10 for each successful result. The implemented formula weights price at 50 percent, delivery at 20 percent, and store trust at 30 percent."
    ))
    body.append(table([
        ["Component", "Formula", "Meaning"],
        ["Price score", "(minimum delivered price / result delivered price) * 10", "The cheapest result receives 10.0; more expensive results receive lower scores."],
        ["Delivery score", "max(0, 10 - delivery_days / 1.4)", "Shorter delivery times score higher; long delivery times trend toward 0."],
        ["Trust score", "store_rating * 2", "Converts adapter store rating from a 5-point scale to a 10-point scale."],
        ["Final score", "0.50 * price + 0.20 * delivery + 0.30 * trust", "Balanced recommendation score displayed to users."],
    ], [2000, 3500, 3500]))

    body.append(heading("4.", "Non-Functional Requirements", 1))
    body.append(paragraph("The project uses the FURPS+ style grouping: functionality, usability, reliability, performance, supportability/maintainability, security, compatibility, data, and legal/ethical constraints."))
    body.append(table([["ID", "Category", "Priority", "Requirement", "Evidence or Acceptance Criteria"], *nfrs], [1200, 1500, 900, 3600, 2800]))

    body.append(heading("5.", "External Interface Requirements", 1))
    body.append(heading("5.1", "User Interfaces", 2))
    body.append(table([["Interface", "Route", "Main Requirements"], *ui_interfaces], [2100, 1900, 5000]))

    body.append(heading("5.2", "Hardware Interfaces", 2))
    body.append(paragraph(
        "The system has no dedicated hardware interface. Users interact through standard desktop or mobile devices. The backend may require server resources sufficient for concurrent HTTP requests and browser automation; Selenium-based adapters may require a Chrome/Chromium runtime in the deployment environment."
    ))

    body.append(heading("5.3", "Software Interfaces", 2))
    body.append(table([
        ["Software System", "Interface Type", "Purpose"],
        ["React frontend", "HTTP JSON", "Consumes backend APIs for authentication, comparison, history, and account settings."],
        ["Django REST backend", "REST API", "Provides application logic, validation, persistence, scoring, and source integration."],
        ["PostgreSQL", "Database connection", "Stores users, tokens, scraping jobs, offers, comparison searches, and comparison results."],
        ["Redis", "Broker URL", "Configured as Celery broker for background-task infrastructure."],
        ["Celery", "Worker process", "Configured for asynchronous/background work support. Current all-source comparison uses thread-based parallelism in the request path."],
        ["Google OAuth", "ID token verification", "Verifies Google Sign-In credentials from the frontend."],
        ["Google Gemini", "Generative AI API", "Filters products by semantic match to query intent."],
        ["External stores", "HTTPS pages/APIs", "Provide public product, price, stock, shipping, and delivery data."],
    ], [2400, 2200, 4400]))

    body.append(heading("5.4", "Communication Interfaces", 2))
    comms = [
        "Frontend-to-backend communication uses JSON over HTTP during development and shall use HTTPS in production.",
        "Authenticated API calls use the Authorization: Bearer <access token> header.",
        "The frontend stores authToken, refreshToken, and user in localStorage and attaches the access token through an axios request interceptor.",
        "The backend allows configured frontend origins through CORS and CSRF trusted origin settings.",
        "External scraping and API calls use HTTPS and source-specific headers/user agents.",
        "Backend error responses use JSON bodies with error or message fields when possible.",
    ]
    for item in comms:
        body.append(bullet(item))
    body.append(paragraph("Primary API contract:"))
    body.append(table([["Method", "Endpoint", "Access", "Purpose"], *api_endpoints], [900, 2600, 1500, 5000]))

    body.append(heading("6.", "Detailed Use Cases", 1))
    for case in use_cases:
        body.append(heading(case["id"], case["name"], 2))
        rows = [
            ["Field", "Description"],
            ["Actors", case["actors"]],
            ["Preconditions", case["preconditions"]],
            ["Trigger", case["trigger"]],
            ["Main Success Scenario", "\n".join(f"{i + 1}. {step}" for i, step in enumerate(case["main"]))],
            ["Alternate / Exception Flows", "\n".join(f"- {step}" for step in case["alternates"])],
            ["Postconditions", case["post"]],
            ["Related Requirements", case["requirements"]],
        ]
        body.append(table(rows, [2300, 6700]))

    body.append(heading("7.", "Appendix", 1))
    body.append(heading("A.1", "Primary Comparison Sequence", 2))
    body.append(code_block(sequence_diagram))

    body.append(heading("A.2", "Data Dictionary", 2))
    body.append(table([["Data Element", "Type", "Model or Store", "Description"], *data_dictionary], [2300, 1500, 2400, 3800]))

    body.append(heading("A.3", "Requirement Traceability Matrix", 2))
    body.append(table([["Feature Area", "Requirements", "Use Cases", "Implementation Evidence"], *traceability], [2200, 1800, 2000, 4000]))

    body.append(heading("A.4", "Key Backend Response Shape", 2))
    body.append(paragraph("The all-source comparison endpoint returns the following conceptual structure. Actual arrays and values vary by query and source availability."))
    body.append(code_block("""{
  "query": "iPhone 15",
  "location": "outside beirut",
  "results": [
    {
      "product": {
        "title": "Product title",
        "url": "https://seller.example/product",
        "image_url": "https://seller.example/image.jpg",
        "in_stock": true
      },
      "pricing": {
        "item_price": 950.00,
        "shipping_fee": 5.00,
        "tax_amount": 0.00,
        "total_price": 955.00,
        "currency": "USD",
        "delivery_time": "3-5 business days"
      },
      "source": "mobileleb",
      "store_rating": 4.3,
      "delivery_days": 4,
      "score": 8.9,
      "score_breakdown": {
        "price_score": 10.0,
        "delivery_score": 7.1,
        "trust_score": 8.6
      }
    }
  ],
  "metadata": {
    "min_price": 955.00,
    "sites_checked": 12,
    "sites_succeeded": 7,
    "sites_failed": 4,
    "failed_sources": []
  },
  "search_id": 123
}"""))

    body.append(heading("A.5", "Known Limitations and Production Readiness Notes", 2))
    production_notes = [
        "Before production, provide real environment variables for Django secret key, Gemini, Google OAuth, database credentials, allowed hosts, frontend URLs, and any source API tokens.",
        "Set DEBUG to false, configure ALLOWED_HOSTS, serve behind HTTPS, and review CORS origins.",
        "Review localStorage token storage and consider hardened token handling for a production threat model.",
        "Add scheduled adapter health checks because external store markup can change.",
        "The frontend sends the user's saved delivery location with compare-all requests; backend clients that omit it still receive the outside Beirut default.",
        "Add pagination or retention policy for very large histories if the user base grows.",
        "Consider moving all long-running comparisons to Celery tasks if deployment timeouts become an issue.",
    ]
    for item in production_notes:
        body.append(bullet(item))

    sect_pr = (
        '<w:sectPr>'
        '<w:pgSz w:w="12240" w:h="15840"/>'
        '<w:pgMar w:top="1440" w:right="1080" w:bottom="1440" w:left="1080" w:header="720" w:footer="720" w:gutter="0"/>'
        '<w:cols w:space="720"/>'
        '<w:docGrid w:linePitch="360"/>'
        '</w:sectPr>'
    )
    xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:wpc="http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas" '
        'xmlns:cx="http://schemas.microsoft.com/office/drawing/2014/chartex" '
        'xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" '
        'xmlns:o="urn:schemas-microsoft-com:office:office" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
        'xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math" '
        'xmlns:v="urn:schemas-microsoft-com:vml" '
        'xmlns:wp14="http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing" '
        'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" '
        'xmlns:w10="urn:schemas-microsoft-com:office:word" '
        'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
        'xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml" '
        'xmlns:wpg="http://schemas.microsoft.com/office/word/2010/wordprocessingGroup" '
        'xmlns:wpi="http://schemas.microsoft.com/office/word/2010/wordprocessingInk" '
        'xmlns:wne="http://schemas.microsoft.com/office/word/2006/wordml" '
        'xmlns:wps="http://schemas.microsoft.com/office/word/2010/wordprocessingShape" '
        'mc:Ignorable="w14 wp14">'
        f"<w:body>{''.join(body)}{sect_pr}</w:body>"
        "</w:document>"
    )
    return xml


def update_settings_xml(settings_xml: bytes) -> bytes:
    text = settings_xml.decode("utf-8")
    if "<w:updateFields" not in text:
        text = text.replace("</w:settings>", '<w:updateFields w:val="true"/></w:settings>')
    return text.encode("utf-8")


def core_props_xml() -> bytes:
    today_iso = date.today().isoformat()
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
    xmlns:dc="http://purl.org/dc/elements/1.1/"
    xmlns:dcterms="http://purl.org/dc/terms/"
    xmlns:dcmitype="http://purl.org/dc/dcmitype/"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <dc:title>{esc(PROJECT_NAME)} Software Requirements Specification</dc:title>
  <dc:subject>Senior Project SRS</dc:subject>
  <dc:creator>{esc(AUTHOR)}</dc:creator>
  <cp:keywords>SRS; senior project; price comparison; Lebanon; Django; React</cp:keywords>
  <dc:description>{esc(PROJECT_SUBTITLE)}</dc:description>
  <cp:lastModifiedBy>{esc(AUTHOR)}</cp:lastModifiedBy>
  <dcterms:created xsi:type="dcterms:W3CDTF">{today_iso}T00:00:00Z</dcterms:created>
  <dcterms:modified xsi:type="dcterms:W3CDTF">{today_iso}T00:00:00Z</dcterms:modified>
</cp:coreProperties>'''.encode("utf-8")


def write_docx() -> None:
    if not TEMPLATE.exists():
        raise FileNotFoundError(f"Template not found: {TEMPLATE}")

    document_xml = build_document_xml().encode("utf-8")
    with zipfile.ZipFile(TEMPLATE, "r") as zin, zipfile.ZipFile(OUTPUT_DOCX, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "word/document.xml":
                data = document_xml
            elif item.filename == "word/settings.xml":
                data = update_settings_xml(data)
            elif item.filename == "docProps/core.xml":
                data = core_props_xml()
            zout.writestr(item, data)


def markdown_table(rows: list[list[object]]) -> str:
    if not rows:
        return ""
    escaped = [[str(cell).replace("\n", "<br>") for cell in row] for row in rows]
    header = "| " + " | ".join(escaped[0]) + " |"
    sep = "| " + " | ".join("---" for _ in escaped[0]) + " |"
    body = ["| " + " | ".join(row) + " |" for row in escaped[1:]]
    return "\n".join([header, sep, *body])


def write_markdown() -> None:
    lines: list[str] = [
        f"# Software Requirements Specification for {PROJECT_NAME}",
        "",
        PROJECT_SUBTITLE,
        "",
        f"Version: {VERSION}",
        f"Prepared by: {AUTHOR}",
        f"Date: {DOC_DATE}",
        "",
        "## Revision History",
        "",
        markdown_table([
            ["Name", "Date", "Reason for Changes", "Version"],
            [AUTHOR, "May 2, 2026", "Initial complete SRS created for senior project submission.", "1.0"],
            [AUTHOR, DOC_DATE, "Updated to match the current Awfarlak backend/frontend implementation, 12-source registry, authenticated source endpoints, trending searches, environment-based secrets, and current UI behavior.", VERSION],
        ]),
        "",
        "## Table of Contents",
        "",
    ]
    lines.extend(f"- {number} {title}" for number, title in TOC)
    lines.extend([
        "",
        "## 1. Introduction",
        "",
        "### 1.1 Purpose and Intended Audience",
        "",
        f"This SRS defines the required external behavior, constraints, interfaces, data expectations, and use cases for {PROJECT_NAME}.",
        "",
        "### 1.2 Project Scope",
        "",
        f"{PROJECT_NAME} is a web-based product comparison system for shoppers in Lebanon. It includes a React frontend, Django REST backend, PostgreSQL persistence, Redis/Celery infrastructure, source adapters, Google OAuth, and Gemini product-intent filtering.",
        "",
        "### 1.3 Terms, Definitions, and Acronyms",
        "",
        markdown_table([["Term", "Definition"], *terms]),
        "",
        "### 1.4 References",
        "",
        markdown_table([["ID", "Reference", "Location or Source"], *references]),
        "",
        "## 2. Overall Description",
        "",
        "### 2.1 Product Perspective",
        "",
        "```text",
        architecture_diagram,
        "```",
        "",
        "### 2.2 Product Features",
        "",
        markdown_table([["Feature", "Description"], *product_features]),
        "",
        "### 2.3 User Classes and Characteristics",
        "",
        markdown_table([["User Class", "Priority", "Characteristics"], *user_classes]),
        "",
        "### 2.4 Operating Environment",
        "",
    ])
    lines.extend(f"- {item}" for item in [
        "Frontend: React 19, Vite 7, Tailwind CSS 4, axios, react-router-dom, and lucide-react.",
        "Backend: Django 6, Django REST Framework, Simple JWT, PostgreSQL, Redis, Celery, requests, BeautifulSoup/lxml, Selenium, and Google Generative AI SDK.",
        "Development ports: React 5173 and Django 8000, with Vite proxying /api requests.",
    ])
    lines.extend(["", "### 2.5 Design and Implementation Constraints", ""])
    lines.extend(f"- {item}" for item in constraints)
    lines.extend(["", "### 2.6 Assumptions and Dependencies", ""])
    lines.extend(f"- {item}" for item in assumptions)
    lines.extend([
        "",
        "## 3. System Features",
        "",
        "### 3.1 Functional Requirements",
        "",
        markdown_table([["ID", "Name", "Priority", "Requirement", "Acceptance Criteria"], *functional_requirements]),
        "",
        "### 3.2 Supported Store Sources",
        "",
        markdown_table([["Adapter Key", "Store", "Base Source", "Implementation Notes"], *source_adapters]),
        "",
        markdown_table([["Store", "Shipping Rule", "Tax Rule", "Delivery Time Rule"], *pricing_rules]),
        "",
        "### 3.3 Comparison Scoring Requirements",
        "",
        markdown_table([
            ["Component", "Formula", "Meaning"],
            ["Price score", "(minimum delivered price / result delivered price) * 10", "The cheapest result receives 10.0."],
            ["Delivery score", "max(0, 10 - delivery_days / 1.4)", "Shorter delivery times score higher."],
            ["Trust score", "store_rating * 2", "Converts 5-point store rating to 10-point scale."],
            ["Final score", "0.50 * price + 0.20 * delivery + 0.30 * trust", "Balanced recommendation score."],
        ]),
        "",
        "## 4. Non-Functional Requirements",
        "",
        markdown_table([["ID", "Category", "Priority", "Requirement", "Evidence or Acceptance Criteria"], *nfrs]),
        "",
        "## 5. External Interface Requirements",
        "",
        "### 5.1 User Interfaces",
        "",
        markdown_table([["Interface", "Route", "Main Requirements"], *ui_interfaces]),
        "",
        "### 5.2 Hardware Interfaces",
        "",
        "The system has no dedicated hardware interface. It requires standard user devices and sufficient backend server resources.",
        "",
        "### 5.3 Software Interfaces",
        "",
        "The system interfaces with React, Django REST Framework, PostgreSQL, Redis, Celery, Google OAuth, Google Gemini, and external store websites.",
        "",
        "### 5.4 Communication Interfaces",
        "",
        markdown_table([["Method", "Endpoint", "Access", "Purpose"], *api_endpoints]),
        "",
        "## 6. Detailed Use Cases",
        "",
    ])
    for case in use_cases:
        lines.extend([
            f"### {case['id']} {case['name']}",
            "",
            markdown_table([
                ["Field", "Description"],
                ["Actors", case["actors"]],
                ["Preconditions", case["preconditions"]],
                ["Trigger", case["trigger"]],
                ["Main Success Scenario", "<br>".join(f"{i + 1}. {step}" for i, step in enumerate(case["main"]))],
                ["Alternate / Exception Flows", "<br>".join(f"- {step}" for step in case["alternates"])],
                ["Postconditions", case["post"]],
                ["Related Requirements", case["requirements"]],
            ]),
            "",
        ])
    lines.extend([
        "## 7. Appendix",
        "",
        "### A.1 Primary Comparison Sequence",
        "",
        "```text",
        sequence_diagram,
        "```",
        "",
        "### A.2 Data Dictionary",
        "",
        markdown_table([["Data Element", "Type", "Model or Store", "Description"], *data_dictionary]),
        "",
        "### A.3 Requirement Traceability Matrix",
        "",
        markdown_table([["Feature Area", "Requirements", "Use Cases", "Implementation Evidence"], *traceability]),
    ])
    OUTPUT_MD.write_text("\n".join(lines), encoding="utf-8")


def verify_docx_text() -> tuple[int, int]:
    with zipfile.ZipFile(OUTPUT_DOCX, "r") as z:
        xml = z.read("word/document.xml").decode("utf-8")
    text = re.sub(r"<[^>]+>", " ", xml)
    text = html.unescape(re.sub(r"\s+", " ", text)).strip()
    return len(text), len(re.findall(r"\bFR-\d{2}\b", text))


if __name__ == "__main__":
    write_docx()
    write_markdown()
    char_count, fr_count = verify_docx_text()
    print(f"Created: {OUTPUT_DOCX}")
    print(f"Created: {OUTPUT_MD}")
    print(f"Extracted document text characters: {char_count}")
    print(f"Functional requirement references found: {fr_count}")
