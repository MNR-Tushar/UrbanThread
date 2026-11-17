# 🧵 Urban Thread — E-Commerce REST API & AI Assistant Backend

A production-ready, feature-rich Django REST Framework backend powering the **Urban Thread** fashion and apparel storefront. Built with Django 6.0, Python 3.12, Celery async task processing, Redis caching & message broker, Google Gemini AI customer chatbot, SSLCommerz payment gateway, Cloudinary image storage, and Docker multi-container deployment.

---

## 🌐 Live Services & Documentation

| Service / Resource | Local URL | Production URL |
| :----------------- | :-------- | :------------- |
| **Live Storefront (Frontend)** | `http://localhost:5173/` | [urbanthreadshop.vercel.app](https://urbanthreadshop.vercel.app/) |
| **API Base URL** | `http://127.0.0.1:8000/` | `https://urbanthread-6nok.onrender.com/` |
| **Swagger UI (Spectacular)** | `http://127.0.0.1:8000/api/docs/` | `https://urbanthread-6nok.onrender.com/api/docs/` |
| **OpenAPI Schema (JSON)** | `http://127.0.0.1:8000/api/schema/` | `https://urbanthread-6nok.onrender.com/api/schema/` |
| **ReDoc UI** | `http://127.0.0.1:8000/api/schema/redoc/` | `https://urbanthread-6nok.onrender.com/api/schema/redoc/` |
| **Django Admin Panel** | `http://127.0.0.1:8000/admin/` | `https://urbanthread-6nok.onrender.com/admin/` |
| **Celery Flower Dashboard** | `http://127.0.0.1:5555/` *(Docker)* | Internal / Protected |

---

## 📋 Table of Contents

- [🧵 Urban Thread — E-Commerce REST API & AI Assistant Backend](#-urban-thread--e-commerce-rest-api--ai-assistant-backend)
  - [🌐 Live Services \& Documentation](#-live-services--documentation)
  - [📋 Table of Contents](#-table-of-contents)
  - [🛠 Tech Stack](#-tech-stack)
  - [📁 Project Structure](#-project-structure)
  - [✨ Features](#-features)
    - [1. User Authentication \& Profile Security](#1-user-authentication--profile-security)
    - [2. Products, Catalog \& Media](#2-products-catalog--media)
    - [3. Inventory \& Stock Tracking](#3-inventory--stock-tracking)
    - [4. Shopping Cart \& Coupons](#4-shopping-cart--coupons)
    - [5. Orders, Delivery \& Returns](#5-orders-delivery--returns)
    - [6. Payments (SSLCommerz + COD)](#6-payments-sslcommerz--cod)
    - [7. Customer Reviews \& Wishlist](#7-customer-reviews--wishlist)
    - [8. AI Support Chatbot (Gemini / OpenAI)](#8-ai-support-chatbot-gemini--openai)
    - [9. Asynchronous \& Scheduled Tasks (Celery + Beat)](#9-asynchronous--scheduled-tasks-celery--beat)
  - [🏗 System Architecture](#-system-architecture)
  - [⚙️ Getting Started \& Setup](#️-getting-started--setup)
    - [Option A: Local Development (Windows / macOS / Linux)](#option-a-local-development-windows--macos--linux)
    - [Option B: Docker Compose (Multi-Container Setup)](#option-b-docker-compose-multi-container-setup)
  - [🔑 Environment Variables](#-environment-variables)
  - [⚡ Celery Background Workers \& Beat Scheduler](#-celery-background-workers--beat-scheduler)
  - [📡 Complete API Endpoints](#-complete-api-endpoints)
    - [Accounts (`/accounts/`)](#accounts-accounts)
    - [Products, Banners \& Settings (`/products/`)](#products-banners--settings-products)
    - [Inventory Management (`/inventory/inventorys/`)](#inventory-management-inventoryinventorys)
    - [Shopping Cart (`/cart/`)](#shopping-cart-cart)
    - [Coupons (`/coupons/`)](#coupons-coupons)
    - [Orders, Tracking \& Returns (`/orders/`)](#orders-tracking--returns-orders)
    - [Payments (`/payments/`)](#payments-payments)
    - [Reviews (`/reviews/`)](#reviews-reviews)
    - [AI Chatbot (`/chatbot/`)](#ai-chatbot-chatbot)
  - [🤖 AI Chatbot Details](#-ai-chatbot-details)
  - [💳 Payment Gateway Integration](#-payment-gateway-integration)
  - [📧 Transactional Emails (Brevo / SendGrid)](#-transactional-emails-brevo--sendgrid)
  - [🛡 Django Admin \& Staff Features](#-django-admin--staff-features)
  - [🔄 Testing \& CI/CD](#-testing--cicd)
  - [📝 License](#-license)

---

## 🛠 Tech Stack

| Component | Technology | Version / Details |
| --------- | ---------- | ----------------- |
| **Framework** | Django + Django REST Framework | Django 6.0.1, DRF 3.16.1 |
| **Runtime** | Python | 3.12+ (tested on Python 3.12 / 3.13) |
| **Authentication** | JWT (`djangorestframework-simplejwt`) + Google OAuth | Access & refresh rotation, token blacklist, `google-auth` token verification |
| **Database** | PostgreSQL (Docker/Prod) or SQLite (Local Dev) | `psycopg2-binary`, configured with `dj-database-url` |
| **Caching** | Redis / LocMemCache | `django-redis` with Redis 7; falls back gracefully to `LocMemCache` |
| **Task Queue** | Celery + Celery Beat + Flower | `celery 5.6.3`, `django-celery-beat`, `flower 2.0.1` |
| **Cloud Storage** | Cloudinary / WhiteNoise | `cloudinary 1.47.0` for user uploads, `whitenoise 6.12.0` for static files |
| **AI Assistant** | Google Gemini API (native REST) / OpenAI | Fallback across `gemini-3.8-flash`, `gemini-2.5-flash`, `gemini-1.5-flash` |
| **Payment Gateway** | SSLCommerz + Cash on Delivery (COD) | Sandbox & live modes, IPN webhooks, refund endpoints |
| **Email & SMS** | Brevo API / SendGrid API / Console / SMS Webhook | Transactional OTP, welcome messages, order notifications |
| **Invoicing** | ReportLab | PDF invoice generation (`/orders/{id}/invoice/`) |
| **API Documentation** | drf-spectacular (OpenAPI 3) + drf-yasg | Swagger UI and ReDoc generators |
| **Containerization** | Docker & Docker Compose | Multi-stage Dockerfile, PostgreSQL, Redis, Celery, Beat, Flower |
| **CI/CD** | GitHub Actions | Flake8 linting, `manage.py check`, migration test, GHCR Docker build |

---

## 📁 Project Structure

```
urbanthread/
├── .github/
│   └── workflows/          # GitHub Actions CI/CD workflows
├── accounts/               # Custom user, profile, address, Google OAuth, OTP verification
├── cart/                   # Shopping cart, cart items, guest cart support
├── chatbot/                # AI assistant view, Gemini/OpenAI caller, store knowledge base
├── coupons/                # Discount coupons, percentage discounts, auto-expiry tasks
├── inventory/              # Variant stock management (product × color × size)
├── management/             # Custom management commands (e.g. migrate_media_to_cloudinary)
├── media/                  # Local media upload folder (used when Cloudinary is not active)
├── orders/                 # Order placement, tracking history, return requests, PDF invoices
├── payments/               # SSLCommerz gateway integration, IPN callbacks, refunds
├── products/               # Products, categories, brands, colors, sizes, images, banners, store settings
├── reviews/                # Product ratings and verified reviews
├── staticfiles/            # Collected static files
├── urbanthread/            # Settings, URLs, WSGI, ASGI, Celery app definition, custom storage
├── .dockerignore
├── .env                    # Environment configuration (ignored in git)
├── .env.example            # Sample environment variables
├── .gitignore
├── docker-compose.yml      # Multi-container orchestration (web, db, redis, celery, beat, flower)
├── Dockerfile              # Multi-stage production container build
├── manage.py
├── populate_test_data.py   # Seed script for test products & demo accounts
└── requirements.txt        # Pinned Python dependencies
```

---

## ✨ Features

### 1. User Authentication & Profile Security
- **JWT Authentication:** Access token (60-day) and Refresh token (10-day) with automatic rotation and token blacklisting upon logout.
- **Google One-Tap / OAuth Sign-in:** Validates Google ID tokens via backend Google Auth API and automatically registers/signs in users.
- **Email & Phone OTP:** Registration verification, resend cooldowns, and OTP expiration (15 minutes).
- **Password Reset & Change:** Secure OTP-based reset flows without requiring insecure reset links.
- **Rate Throttling:** Strict throttling on login (5/min), register (5/hr), OTP requests, and chatbot interactions.

### 2. Products, Catalog & Media
- Full catalog hierarchy: Categories, Brands, Products, Colors, Sizes, and Multiple Product Images.
- Dynamic Store Settings & Banners API for homepage banners and delivery charge thresholds.
- Filtering, keyword search (`?search=`), sorting (`?ordering=-created_at`), and Limit/Offset pagination.
- Automatic image uploads to **Cloudinary** (when configured) or local filesystem.

### 3. Inventory & Stock Tracking
- Granular stock tracking per variant: `(Product, Color, Size)`.
- Real-time availability check endpoint (`/inventory/inventorys/check_availability/`).
- Auto-decrement on order placement and auto-restock on order cancellation.

### 4. Shopping Cart & Coupons
- Authenticated customer cart with Redis-backed caching for high throughput.
- Guest cart support using unique `X-Guest-Cart` request header.
- Percentage-based coupon discounts with validation and automated expiry.

### 5. Orders, Delivery & Returns
- Complete order checkout with address snapshot, zone-based delivery calculation, and coupon discount.
- Order tracking status pipeline: `pending` → `processing` → `shipped` → `delivered` / `cancelled`.
- **Return & Refund Requests:** Customers can request returns for delivered orders; staff can review, approve, and track status.
- **PDF Invoice Generation:** Downloadable invoice generated dynamically using ReportLab (`/orders/{id}/invoice/`).

### 6. Payments (SSLCommerz + COD)
- **SSLCommerz Online Payment:** Initiation URL, browser callbacks (`success`, `fail`, `cancel`), and automated IPN webhook verification.
- **Cash on Delivery (COD):** Instant checkout placement with `unpaid` status.
- Admin refund management endpoint and detailed payment audit logs.

### 7. Customer Reviews & Wishlist
- 1–5 star ratings, text reviews, and product-specific review listings.
- User Wishlist API (`/products/wishlist/`) to save favorite items.

### 8. AI Support Chatbot (Gemini / OpenAI)
- Interactive customer assistant endpoint (`POST /chatbot/`).
- Powered by **Google Gemini API** (`gemini-3.8-flash` primary, auto-fallback to `gemini-2.5-flash` and `gemini-1.5-flash`), or OpenAI.
- Injects real-time catalog data (products, prices, stock, delivery charges, store return policies).
- Bilingual support: effortlessly communicates in both English and Bengali (Bangla & Romanized Bangla).

### 9. Asynchronous & Scheduled Tasks (Celery + Beat)
- **Async Execution:** Asynchronous verification emails, invoice dispatches, and stock sync without blocking web threads.
- **Periodic Scheduler:**
  - Hourly coupon expiration check (`expire_coupons`).
  - Order auto-cancellation for stale unpaid orders (`auto_cancel_orders`).
  - Daily low-stock inventory alerts for store admins (`send_low_stock_alerts`).
  - Daily abandoned cart reminder emails (`send_abandoned_cart_reminders`).

---

## 🏗 System Architecture

```
                               ┌─────────────────────────────┐
                               │   React Frontend (Vite)     │
                               │   http://localhost:5173     │
                               └──────────────┬──────────────┘
                                              │ HTTP / JSON
                                              ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                Django REST Backend                                     │
│                                http://127.0.0.1:8000                                   │
│                                                                                        │
│   ┌────────────────────┐   ┌───────────────────────┐   ┌───────────────────────────┐   │
│   │ REST Endpoints     │   │ AI Chatbot Service    │   │ SSLCommerz Payment Module │   │
│   │ (DRF ViewSets)     │   │ (Gemini 3.8 / OpenAI) │   │ (Gateway & IPN Handlers)  │   │
│   └─────────┬──────────┘   └───────────┬───────────┘   └─────────────┬─────────────┘   │
└─────────────┼──────────────────────────┼─────────────────────────────┼─────────────────┘
              │                          │                             │
              ▼                          ▼                             ▼
   ┌────────────────────┐     ┌───────────────────────┐     ┌───────────────────────┐
   │ PostgreSQL / SQLite│     │ Google Generative AI  │     │ SSLCommerz Gateway    │
   │ (Application DB)   │     │ (REST API Endpoint)   │     │ (Sandbox / Live API)  │
   └────────────────────┘     └───────────────────────┘     └───────────────────────┘
              │
              ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                Background Task Engine                                  │
│                                                                                        │
│   ┌────────────────────┐   ┌───────────────────────┐   ┌───────────────────────────┐   │
│   │ Redis (Broker &    │──▶│ Celery Worker         │──▶│ Celery Beat Scheduler     │   │
│   │ Django Cache)      │   │ (Async Emails & Tasks)│   │ (Cron / Periodic Jobs)    │   │
│   └────────────────────┘   └───────────────────────┘   └─────────────┬─────────────┘   │
│                                                                      │                 │
│                                                                      ▼                 │
│                                                            ┌───────────────────┐       │
│                                                            │ Flower Dashboard  │       │
│                                                            │ Port 5555         │       │
│                                                            └───────────────────┘       │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## ⚙️ Getting Started & Setup

### Option A: Local Development (Windows / macOS / Linux)

**Prerequisites:** Python 3.10+ (Python 3.12 recommended), Git. Redis is optional for local development (Django will automatically fall back to memory broker & LocMemCache).

#### 1. Navigate to the backend directory
```powershell
# From the repository root:
cd urbanthread
```

#### 2. Create and activate a virtual environment
```powershell
# Windows PowerShell:
..\venv\Scripts\Activate.ps1
# Or create a local one:
python -m venv venv
.\venv\Scripts\Activate.ps1

# macOS / Linux:
python3 -m venv venv
source venv/bin/activate
```

#### 3. Install dependencies
```bash
pip install -r requirements.txt
```

#### 4. Configure environment variables
Create a `.env` file in the `urbanthread/` directory (see [.env.example](.env.example)):
```env
SECRET_KEY=your-secure-secret-key-change-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DB_ENGINE=django.db.backends.sqlite3
REDIS_URL=locmem
FRONTEND_URL=http://localhost:5173
```

#### 5. Run migrations and initialize data
```powershell
python manage.py migrate
python manage.py createsuperuser
```

*(Optional)* Seed sample products and brands for local testing:
```powershell
python populate_test_data.py
```
> ⚠️ **Warning:** `populate_test_data.py` creates demo test accounts with default passwords. Use only in local development!

#### 6. Start the development server
```powershell
python manage.py runserver 127.0.0.1:8000
```
Visit `http://127.0.0.1:8000/api/docs/` to inspect the Swagger UI documentation.

---

### Option B: Docker Compose (Multi-Container Setup)

**Prerequisites:** Docker and Docker Compose installed.

```bash
# 1. Navigate to backend directory
cd urbanthread

# 2. Prepare .env file
cp .env.example .env
# Ensure DB_HOST=db and REDIS_URL=redis://redis:6379/0 are set

# 3. Build and launch all containers
docker compose up --build
```

**Services started by `docker-compose.yml`:**
| Service | Image | Internal Port | Host Port | Purpose |
| ------- | ----- | ------------- | --------- | ------- |
| `web` | Custom (Dockerfile) | 8000 | `8000` | Django DRF application (Gunicorn) |
| `db` | `postgres:16-alpine` | 5432 | Internal | PostgreSQL database |
| `redis` | `redis:7-alpine` | 6379 | `6379` | Celery broker & Django cache |
| `celery` | Custom (Dockerfile) | - | - | Background task worker |
| `celery_beat` | Custom (Dockerfile) | - | - | Periodic task scheduler |
| `flower` | Custom (Dockerfile) | 5555 | `5555` | Celery real-time monitor |

To run migrations or create a superuser inside Docker:
```bash
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
```

---

## 🔑 Environment Variables

The application reads configuration from the environment or `.env` using `python-decouple`.

| Variable | Default Value | Required | Purpose / Notes |
| -------- | ------------- | :------: | --------------- |
| `SECRET_KEY` | *(django-insecure fallback)* | **Yes (Prod)** | Django cryptographic signature key |
| `DEBUG` | `True` | No | Set to `False` in production |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | No | Comma-separated list of hostnames |
| `DATABASE_URL` | *Empty* | No | PostgreSQL connection URL (e.g. Supabase / Render) |
| `DB_ENGINE` | `django.db.backends.sqlite3` | No | `django.db.backends.postgresql` for Postgres |
| `DB_NAME` | `urbanthread` | No | PostgreSQL database name |
| `DB_USER` | `postgres` | No | PostgreSQL username |
| `DB_PASSWORD` | *Empty* | No | PostgreSQL password |
| `DB_HOST` | `localhost` | No | Host address (`db` inside Docker) |
| `DB_PORT` | `5432` | No | Database port |
| `REDIS_URL` | `locmem` | No | `redis://localhost:6379/0` (or `locmem` for memory cache) |
| `CELERY_BROKER_URL` | Same as `REDIS_URL` | No | Celery broker override (`memory://` if no Redis) |
| `CELERY_RESULT_BACKEND` | Same as `REDIS_URL` | No | Celery results storage |
| `FRONTEND_URL` | `http://localhost:5173` | No | Frontend origin (production: `https://urbanthreadshop.vercel.app`) |
| `BACKEND_PUBLIC_URL` | *Empty* | No | Public HTTPS URL (required for SSLCommerz callbacks) |
| `GOOGLE_CLIENT_ID` | *Empty* | No | Google OAuth 2.0 Web Client ID |
| `GEMINI_API_KEY` | *Empty* | No | Google AI Studio Gemini API key (for customer chatbot) |
| `GEMINI_CHAT_MODEL` | `gemini-3.8-flash` | No | Gemini model name |
| `OPENAI_API_KEY` | *Empty* | No | OpenAI API key (if `CHATBOT_PROVIDER=openai`) |
| `CHATBOT_PROVIDER` | `gemini` | No | Active chatbot engine (`gemini` or `openai`) |
| `CLOUDINARY_URL` | *Empty* | No | Format: `cloudinary://API_KEY:SECRET@CLOUD_NAME` |
| `SSLCOMMERZ_STORE_ID` | *Empty* | No | SSLCommerz Store ID |
| `SSLCOMMERZ_STORE_PASSWORD` | *Empty* | No | SSLCommerz Store Password |
| `SSLCOMMERZ_IS_SANDBOX` | `True` | No | Set to `False` for live payments |
| `BREVO_API_KEY` | *Empty* | No | Brevo transactional email API key |
| `BREVO_SENDER_EMAIL` | `noreply@urbanthread.com` | No | Verified Brevo sender address |
| `BREVO_SENDER_NAME` | `UrbanThread` | No | Display name in outgoing emails |
| `SENDGRID_API_KEY` | *Empty* | No | Alternative SendGrid API key |
| `SMS_API_URL` | *Empty* | No | Optional SMS gateway endpoint for phone OTP |
| `SMS_API_TOKEN` | *Empty* | No | Bearer token for SMS gateway |

---

## ⚡ Celery Background Workers & Beat Scheduler

When running outside Docker with Redis:

```powershell
# Terminal 1 — Start Celery worker:
celery -A urbanthread worker --loglevel=info

# Terminal 2 — Start Celery Beat scheduler:
celery -A urbanthread beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler

# Terminal 3 — (Optional) Start Flower monitor:
celery -A urbanthread flower --port=5555
```

> 💡 **Local Dev Note:** If `REDIS_URL=locmem` (default), Celery runs in eager mode (`CELERY_TASK_ALWAYS_EAGER=True`), meaning background tasks run synchronously inline without needing a separate Redis process or worker.

---

## 📡 Complete API Endpoints

All protected endpoints require the following header:
```http
Authorization: Bearer <access_token>
```

### Accounts (`/accounts/`)
| Method | Endpoint | Auth | Description |
| :--- | :--- | :---: | :--- |
| `POST` | `/accounts/register/` | Public | Register new user & dispatch email verification OTP |
| `POST` | `/accounts/login/` | Public | Sign in with username/email & password; returns JWT pair |
| `POST` | `/accounts/google/` | Public | Sign in or register using Google OAuth ID token |
| `POST` | `/accounts/token/refresh/` | Public | Rotate refresh token to receive new access token |
| `POST` | `/accounts/logout/` | Required | Blacklist refresh token & log out |
| `POST` | `/accounts/email/verification/confirm/` | Public | Confirm email OTP; activates account and returns JWT |
| `POST` | `/accounts/email/verification/resend/` | Public | Resend email verification code |
| `POST` | `/accounts/password/reset/request/` | Public | Request password-reset OTP via email or SMS |
| `POST` | `/accounts/password/reset/confirm/` | Public | Verify OTP and set new password |
| `POST` | `/accounts/password/change/` | Required | Change password while authenticated |
| `GET/PUT/PATCH` | `/accounts/profile/` | Required | View and update customer profile |
| `GET/POST` | `/accounts/address/` | Required | List and create delivery addresses |
| `GET/PUT/DELETE`| `/accounts/address/{id}/` | Required | Manage individual delivery address |
| `GET` | `/accounts/allusers/` | Staff | List all registered users |

### Products, Banners & Settings (`/products/`)
| Method | Endpoint | Auth | Description |
| :--- | :--- | :---: | :--- |
| `GET` | `/products/products/` | Public | List products (supports `?search=`, `?category=`, `?brand=`, `?ordering=`) |
| `GET` | `/products/products/{id_or_slug}/` | Public | Retrieve product details with images, sizes, colors |
| `POST/PUT/DELETE` | `/products/products/{id}/` | Staff | Create, update, or remove products |
| `GET` | `/products/categories/` | Public | List categories |
| `GET` | `/products/brands/` | Public | List brands |
| `GET` | `/products/sizes/` | Public | List available garment sizes (e.g., S, M, L, XL) |
| `GET` | `/products/colors/` | Public | List available colors |
| `GET` | `/products/banners/` | Public | Active promotional banners for homepage carousel |
| `GET` | `/products/store-settings/` | Public | Store shipping fees, free shipping threshold, announcements |
| `GET` | `/products/delivery-zones/` | Public | List delivery zones and rates (Dhaka, Outside Dhaka, etc.) |
| `GET/POST` | `/products/wishlist/` | Required | View user wishlist or add an item |
| `DELETE` | `/products/wishlist/{product_id}/` | Required | Remove item from wishlist |

### Inventory Management (`/inventory/inventorys/`)
| Method | Endpoint | Auth | Description |
| :--- | :--- | :---: | :--- |
| `GET` | `/inventory/inventorys/` | Staff | List all inventory entries |
| `GET` | `/inventory/inventorys/check_availability/` | Public | Query stock: `?product_id=X&color_id=Y&size_id=Z` |
| `GET` | `/inventory/inventorys/product_inventory/` | Public | Stock records for a product: `?product_id=X` |
| `POST/PUT/DELETE` | `/inventory/inventorys/` | Staff | Create or update inventory stock quantities |

### Shopping Cart (`/cart/`)
Supports authenticated user token or guest cart token header (`X-Guest-Cart: <token>`).

| Method | Endpoint | Auth | Description |
| :--- | :--- | :---: | :--- |
| `GET` | `/cart/my_cart/` | Public / Guest | Retrieve current cart items, quantities, and subtotal |
| `POST` | `/cart/add_item/` | Public / Guest | Add variant to cart (validates inventory availability) |
| `PATCH` | `/cart/update_item/` | Public / Guest | Update item quantity in cart |
| `DELETE` | `/cart/remove_item/` | Public / Guest | Remove single item from cart |
| `DELETE` | `/cart/clear_cart/` | Public / Guest | Empty entire shopping cart |

### Coupons (`/coupons/`)
| Method | Endpoint | Auth | Description |
| :--- | :--- | :---: | :--- |
| `GET` | `/coupons/` | Required | List active discount coupons |
| `POST` | `/coupons/validate_coupon/` | Required | Validate coupon code and get discount percentage |
| `POST/PUT/DELETE` | `/coupons/` | Staff | Create and manage discount coupons |

### Orders, Tracking & Returns (`/orders/`)
| Method | Endpoint | Auth | Description |
| :--- | :--- | :---: | :--- |
| `POST` | `/orders/create_order/` | Required | Checkout cart (`address_id`, `payment_method`, `coupon_code`) |
| `GET` | `/orders/order_history/` | Required | View authenticated customer's order history |
| `PATCH` | `/orders/{id}/cancel_order/` | Required | Cancel eligible order (auto-restores stock) |
| `GET` | `/orders/{id}/invoice/` | Required | Download generated PDF invoice |
| `GET/POST` | `/orders/return-requests/` | Required | List return requests or submit a return for delivered order |
| `PATCH` | `/orders/return-requests/{id}/` | Staff | Approve, reject, or complete a return request |
| `GET` | `/orders/admin_dashboard/` | Staff | Order analytics summary (sales, revenue, counts) |
| `GET` | `/orders/admin_orders/` | Staff | View all customer orders with filtering |
| `PATCH` | `/orders/{id}/admin_update_status/` | Staff | Update order status (`pending`, `processing`, `shipped`, `delivered`, `cancelled`) |
| `PATCH` | `/orders/{id}/admin_update_tracking/`| Staff | Update courier name and tracking code |
| `POST` | `/orders/export_sales_report/` | Staff | Export CSV sales report |

### Payments (`/payments/`)
| Method | Endpoint | Auth | Description |
| :--- | :--- | :---: | :--- |
| `POST` | `/payments/initiate/` | Required | Initiate SSLCommerz payment for an order; returns `gateway_url` |
| `POST` | `/payments/sslcommerz/success/` | Public | SSLCommerz browser success redirect |
| `POST` | `/payments/sslcommerz/fail/` | Public | SSLCommerz browser failure redirect |
| `POST` | `/payments/sslcommerz/cancel/` | Public | SSLCommerz browser cancellation redirect |
| `POST` | `/payments/sslcommerz/ipn/` | Public | SSLCommerz Instant Payment Notification webhook |
| `GET` | `/payments/my_payments/` | Required | View current user's payment records |
| `POST` | `/payments/refund/` | Staff | Process refund via gateway |

### Reviews (`/reviews/`)
| Method | Endpoint | Auth | Description |
| :--- | :--- | :---: | :--- |
| `GET` | `/reviews/` | Public | List reviews (filter by `?product_id=<id>`) |
| `POST` | `/reviews/` | Required | Submit product rating (1–5) and review |
| `PUT/PATCH/DELETE`| `/reviews/{id}/` | Required | Modify or delete own review |

### AI Chatbot (`/chatbot/`)
| Method | Endpoint | Auth | Description |
| :--- | :--- | :---: | :--- |
| `POST` | `/chatbot/` | Public (Throttled) | AI assistant endpoint (`message`, optional `history`) |

---

## 🤖 AI Chatbot Details

The chatbot endpoint (`/chatbot/`) provides an intelligent shopping assistant for customers:
- **Provider Flexibility:** Configure `CHATBOT_PROVIDER=gemini` (default, free tier) or `CHATBOT_PROVIDER=openai`.
- **Gemini Fallback Chain:** Automatically tries `gemini-3.8-flash` → `gemini-2.5-flash` → `gemini-1.5-flash` with automatic retry logic upon rate limit or transient errors.
- **Dynamic Context Injection:** Extracts keywords and URLs from the user's message, looks up matching products in the database, attaches prices and availability, and injects live delivery fees.
- **Bilingual & Polished:** Detects whether the user is typing in Bengali or English (including Romanized Bengali) and answers accurately in the customer's language.
- **Reliable Fallback:** If the external AI API is unreachable, an intelligent internal rule-based responder handles delivery charges, return instructions, order tracking directions, and product inquiries.

---

## 💳 Payment Gateway Integration

### SSLCommerz
1. Create a merchant test account on [SSLCommerz Sandbox](https://developer.sslcommerz.com/).
2. Set credentials in `.env`:
   ```env
   SSLCOMMERZ_STORE_ID=your_store_id
   SSLCOMMERZ_STORE_PASSWORD=your_store_password
   SSLCOMMERZ_IS_SANDBOX=True
   FRONTEND_URL=http://localhost:5173
   BACKEND_PUBLIC_URL=https://your-public-backend-url.ngrok-free.app
   ```
3. When the customer initiates checkout, `POST /payments/initiate/` generates a secure gateway URL.
4. After payment completion, the gateway invokes the callback endpoints, updates payment & order status, and redirects the customer back to the frontend result page.

---

## 📧 Transactional Emails (Brevo / SendGrid)

- **Brevo API (Recommended):** Set `BREVO_API_KEY`, `BREVO_SENDER_EMAIL`, and `BREVO_SENDER_NAME`. Outgoing emails use Brevo's HTTPS REST API to bypass blocked outbound SMTP ports on cloud hosts.
- **SendGrid API:** Set `SENDGRID_API_KEY` to send transactional emails via SendGrid's HTTPS API.
- **Console Backend:** When neither key is supplied, emails print directly to the server terminal (`console.EmailBackend`), ideal for local development.

---

## 🛡 Django Admin & Staff Features

Access the Django Admin panel at `http://127.0.0.1:8000/admin/`:
- **Inventory Matrix:** In-line editing of variant stock quantities.
- **Order Management:** Status transitions, delivery zone adjustments, and customer tracking IDs.
- **Coupons:** Expiration scheduling and usage limits.
- **Celery Periodic Tasks:** Custom scheduling through `django-celery-beat` stored in the database.

---

## 🔄 Testing & CI/CD

Run system checks and tests:
```powershell
python manage.py check
python manage.py test
```

GitHub Actions automatically runs on push to `main`:
1. **Flake8 Linting:** Code formatting and style adherence.
2. **Django System Checks:** Configuration validation and model checks.
3. **Migration Integrity:** Validates all models match database migration states.
4. **Docker Image Build:** Builds and publishes the runtime container to GitHub Container Registry (GHCR).

---

## 📝 License

This project is licensed under the **MIT License**.
