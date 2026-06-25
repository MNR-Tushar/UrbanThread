# 🧵 Urban Thread — E-Commerce REST API

A production-ready Django REST Framework e-commerce backend for a fashion/clothing store. Built with async task processing, multi-container Docker setup, and CI/CD pipeline. Supports product management, inventory, cart, orders, coupons, payments (SSLCommerz + Cash on Delivery), reviews, and automated background jobs.

---

## 🌐 Live Demo

| Resource       | URL                                                       |
| -------------- | --------------------------------------------------------- |
| **Swagger UI** | https://urbanthread-6nok.onrender.com/api/docs/           |
| **ReDoc**      | https://urbanthread-6nok.onrender.com/redoc/              |
| **Admin**      | https://urbanthread-6nok.onrender.com/admin/              |

---

## 📋 Table of Contents

- [🧵 Urban Thread — E-Commerce REST API](#-urban-thread--e-commerce-rest-api)
  - [🌐 Live Demo](#-live-demo)
  - [📋 Table of Contents](#-table-of-contents)
  - [🛠 Tech Stack](#-tech-stack)
  - [📁 Project Structure](#-project-structure)
  - [✨ Features](#-features)
    - [Core](#core)
    - [Background Tasks (Celery)](#background-tasks-celery)
  - [🏗 Architecture Overview](#-architecture-overview)
  - [⚙️ Installation \& Setup](#️-installation--setup)
    - [Option A: Docker (Recommended)](#option-a-docker-recommended)
    - [Option B: Local Setup](#option-b-local-setup)
  - [🔑 Environment Variables](#-environment-variables)
  - [🚀 Running the Server](#-running-the-server)
    - [Docker](#docker)
    - [Local](#local)
  - [⚡ Background Tasks (Celery)](#-background-tasks-celery)
    - [Async Tasks](#async-tasks)
    - [Periodic Tasks (Celery Beat)](#periodic-tasks-celery-beat)
    - [Monitor Celery (Docker)](#monitor-celery-docker)
  - [📡 API Endpoints](#-api-endpoints)
    - [Accounts](#accounts)
    - [Products](#products)
    - [Inventory](#inventory)
    - [Cart](#cart)
    - [Coupons](#coupons)
    - [Orders](#orders)
    - [Payments](#payments)
    - [Reviews](#reviews)
  - [🔐 Authentication](#-authentication)
  - [💳 Payment Integration](#-payment-integration)
    - [SSLCommerz](#sslcommerz)
    - [Cash on Delivery](#cash-on-delivery)
  - [🛡 Admin Panel](#-admin-panel)
  - [📖 API Documentation](#-api-documentation)
  - [🔄 CI/CD Pipeline](#-cicd-pipeline)
  - [📝 License](#-license)

---

## 🛠 Tech Stack

| Layer            | Technology                                                  |
| ---------------- | ----------------------------------------------------------- |
| Framework        | Django 4.x + Django REST Framework                          |
| Auth             | JWT via `djangorestframework-simplejwt`                     |
| Database         | PostgreSQL (production) / SQLite (dev)                      |
| Cache & Broker   | Redis (separate instances for cache and Celery broker)      |
| Async Tasks      | Celery + Celery Beat (periodic tasks)                       |
| Payment Gateway  | SSLCommerz + Cash on Delivery                               |
| Filtering        | `django-filter`                                             |
| API Docs         | drf-spectacular (Swagger UI) + drf-yasg (ReDoc)             |
| Containerization | Docker + Docker Compose (multi-container)                   |
| CI/CD            | GitHub Actions                                              |
| CORS             | `django-cors-headers`                                       |
| Config           | `python-decouple`                                           |

---

## 📁 Project Structure

```
urbanthread/
├── .github/
│   └── workflows/          # GitHub Actions CI/CD pipeline
├── accounts/               # Custom user, profile, address, email verification
├── cart/                   # Shopping cart & cart items
├── coupons/                # Discount coupon management + auto-expiry tasks
├── inventory/              # Stock management per product variant
├── orders/                 # Order creation, management, auto-cancellation tasks
├── payments/               # SSLCommerz & Cash on Delivery integration
├── products/               # Category, brand, product, images, size, color
├── reviews/                # Product reviews & ratings
├── urbanthread/            # Project settings, URLs, WSGI/ASGI, Celery config
├── Dockerfile
├── docker-compose.yml
├── manage.py
└── requirements.txt
```

---

## ✨ Features

### Core
- **User Auth** — Register with email verification, login/logout via JWT, token refresh & blacklist
- **Products** — Full CRUD for categories, brands, products, images, sizes, colors
- **Inventory** — Track stock per (product × color × size) variant with real-time availability check
- **Cart** — Add, update, remove items with real-time stock validation
- **Coupons** — Percentage-based discount coupons with expiry dates
- **Orders** — Place orders from cart, cancel orders, view history; inventory auto-decremented on order placement
- **Payments** — SSLCommerz online payment + Cash on Delivery; IPN webhook support; refunds
- **Reviews** — Authenticated users can leave 1–5 star reviews on products

### Background Tasks (Celery)
- **Email Verification** — Async email dispatch with retry logic on failure
- **Coupon Auto-Expiry** — Periodic task marks expired coupons as inactive
- **Order Auto-Cancellation** — Cancels unpaid/stale orders after a configurable timeout
- **Low Stock Alerts** — Notifies admins when inventory drops below threshold
- **Abandoned Cart Reminders** — Sends reminder emails to users with inactive carts

---

## 🏗 Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                   Docker Compose                    │
│                                                     │
│  ┌──────────┐   ┌──────────┐   ┌─────────────────┐ │
│  │  Django  │   │ Celery   │   │  Celery Beat    │ │
│  │  (web)   │   │ Worker   │   │  (Scheduler)    │ │
│  └────┬─────┘   └────┬─────┘   └────────┬────────┘ │
│       │              │                  │           │
│  ┌────▼──────────────▼──────────────────▼────────┐  │
│  │              Redis (Broker)                   │  │
│  └───────────────────────────────────────────────┘  │
│                                                     │
│  ┌─────────────────┐   ┌───────────────────────┐   │
│  │  Redis (Cache)  │   │      PostgreSQL        │   │
│  └─────────────────┘   └───────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

> Two separate Redis instances: one for **Celery broker/results**, one for **Django cache**.

---

## ⚙️ Installation & Setup

### Option A: Docker (Recommended)

**Prerequisites:** Docker & Docker Compose installed.

```bash
# 1. Clone the repository
git clone https://github.com/MNR-Tushar/UrbanThread.git
cd UrbanThread

# 2. Create environment file
cp .env.example .env
# Edit .env with your values

# 3. Build and start all containers
docker compose up --build

# 4. In a new terminal, run migrations
docker compose exec web python manage.py migrate

# 5. Create a superuser
docker compose exec web python manage.py createsuperuser
```

The API will be available at `http://localhost:8000/`

**Services started by Docker Compose:**
| Service        | Description                          |
| -------------- | ------------------------------------ |
| `web`          | Django application server            |
| `db`           | PostgreSQL database                  |
| `redis_broker` | Redis for Celery broker & results    |
| `redis_cache`  | Redis for Django cache               |
| `celery`       | Celery worker for async tasks        |
| `celery_beat`  | Celery Beat scheduler for cron tasks |

---

### Option B: Local Setup

**Prerequisites:** Python 3.10+, PostgreSQL, Redis

```bash
# 1. Clone the repository
git clone https://github.com/MNR-Tushar/UrbanThread.git
cd UrbanThread

# 2. Create & activate virtual environment
python -m venv venv
source venv/bin/activate        # macOS/Linux
# venv\Scripts\activate         # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env
# Edit .env with your values

# 5. Apply migrations
python manage.py migrate

# 6. Create superuser
python manage.py createsuperuser

# 7. Start Celery worker (separate terminal)
celery -A urbanthread worker --loglevel=info

# 8. Start Celery Beat scheduler (separate terminal)
celery -A urbanthread beat --loglevel=info

# 9. Run the server
python manage.py runserver
```

---

## 🔑 Environment Variables

Create a `.env` file in the project root:

```env
# Django
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (PostgreSQL)
DB_NAME=urbanthread
DB_USER=postgres
DB_PASSWORD=your-db-password
DB_HOST=db           # 'db' for Docker, 'localhost' for local
DB_PORT=5432

# Redis — Celery Broker
REDIS_BROKER_URL=redis://redis_broker:6379/0

# Redis — Django Cache
REDIS_CACHE_URL=redis://redis_cache:6379/0

# SSLCommerz Payment Gateway
SSLCOMMERZ_STORE_ID=your_store_id
SSLCOMMERZ_STORE_PASSWORD=your_store_password
SSLCOMMERZ_IS_SANDBOX=True

# Frontend URL (for payment redirects)
FRONTEND_URL=http://localhost:3000

# Email
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your@email.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@urbanthread.com
```

---

## 🚀 Running the Server

### Docker
```bash
docker compose up
```

### Local
```bash
python manage.py runserver
```

---

## ⚡ Background Tasks (Celery)

Urban Thread uses **Celery** for async and periodic task processing with Redis as the message broker.

### Async Tasks
| Task | Trigger | Description |
|------|---------|-------------|
| `send_verification_email` | User registration | Sends email verification link asynchronously with retry on failure |

### Periodic Tasks (Celery Beat)
| Task | Schedule | Description |
|------|----------|-------------|
| `expire_coupons` | Every hour | Marks expired coupons as inactive |
| `auto_cancel_orders` | Every 30 min | Cancels unpaid orders past timeout |
| `send_low_stock_alerts` | Daily | Emails admin for low-inventory variants |
| `send_abandoned_cart_reminders` | Daily | Sends reminder emails to users with old active carts |

### Monitor Celery (Docker)
```bash
# View worker logs
docker compose logs celery

# View beat scheduler logs
docker compose logs celery_beat

# Check active tasks
docker compose exec celery celery -A urbanthread inspect active
```

---

## 📡 API Endpoints

All API routes are prefixed with their app name. Protected routes require:
```
Authorization: Bearer <access_token>
```

---

### Accounts

Base URL: `/accounts/`

| Method               | Endpoint                      | Auth     | Description                      |
| -------------------- | ----------------------------- | -------- | -------------------------------- |
| POST                 | `/accounts/register/`         | Public   | Register + sends verification email |
| POST                 | `/accounts/login/`            | Public   | Login and receive JWT tokens     |
| POST                 | `/accounts/logout/`           | Required | Blacklist refresh token / logout |
| POST                 | `/accounts/token/refresh/`    | Public   | Refresh access token             |
| GET                  | `/accounts/allusers/`         | Required | List users (admins see all)      |
| GET/PUT/PATCH        | `/accounts/allusers/{id}/`    | Required | Get/update user                  |
| GET/POST             | `/accounts/address/`          | Required | List or create addresses         |
| GET/PUT/PATCH/DELETE | `/accounts/address/{id}/`     | Required | Manage a single address          |
| GET/POST             | `/accounts/profile/`          | Required | List or create profile           |
| GET/PUT/PATCH/DELETE | `/accounts/profile/{id}/`     | Required | Manage profile                   |

**Register example:**
```json
POST /accounts/register/
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "securepassword123"
}
```
> A verification email is sent asynchronously via Celery after registration.

---

### Products

Base URL: `/products/`

| Method           | Endpoint                    | Auth   | Description           |
| ---------------- | --------------------------- | ------ | --------------------- |
| GET              | `/products/categories/`     | Public | List all categories   |
| POST             | `/products/categories/`     | Admin  | Create category       |
| GET              | `/products/brands/`         | Public | List all brands       |
| POST             | `/products/brands/`         | Admin  | Create brand          |
| GET              | `/products/products/`       | Public | List all products     |
| POST             | `/products/products/`       | Admin  | Create product        |
| GET              | `/products/products/{id}/`  | Public | Product detail        |
| PUT/PATCH/DELETE | `/products/products/{id}/`  | Admin  | Update/delete product |
| GET/POST         | `/products/product-images/` | Admin  | Manage product images |
| GET              | `/products/sizes/`          | Public | List all sizes        |
| GET              | `/products/colors/`         | Public | List all colors       |

**Filtering & Search:**
- Filter: `?category=<id>&brand=<id>&is_available=true`
- Search: `?search=<keyword>`
- Order: `?ordering=price` or `?ordering=-created_at`
- Pagination: `?limit=10&offset=0`

---

### Inventory

Base URL: `/inventorys/`

| Method           | Endpoint                                     | Auth   | Description                 |
| ---------------- | -------------------------------------------- | ------ | --------------------------- |
| GET              | `/inventorys/inventorys/`                    | Public | List all inventory          |
| POST             | `/inventorys/inventorys/`                    | Admin  | Create inventory entry      |
| GET              | `/inventorys/inventorys/{id}/`               | Public | Single inventory entry      |
| PUT/PATCH/DELETE | `/inventorys/inventorys/{id}/`               | Admin  | Update/delete inventory     |
| GET              | `/inventorys/inventorys/check_availability/` | Public | Check stock for a variant   |
| GET              | `/inventorys/inventorys/product_inventory/`  | Public | All inventory for a product |

**Check availability:**
```
GET /inventorys/inventorys/check_availability/?product_id=1&color_id=2&size_id=3
```

---

### Cart

Base URL: `/cart/`

| Method | Endpoint             | Auth     | Description               |
| ------ | -------------------- | -------- | ------------------------- |
| GET    | `/cart/my_cart/`     | Required | View current user's cart  |
| POST   | `/cart/add_item/`    | Required | Add item to cart          |
| PATCH  | `/cart/update_item/` | Required | Update item quantity      |
| DELETE | `/cart/remove_item/` | Required | Remove a single item      |
| DELETE | `/cart/clear_cart/`  | Required | Clear all items from cart |

---

### Coupons

Base URL: `/coupons/`

| Method           | Endpoint                    | Auth     | Description            |
| ---------------- | --------------------------- | -------- | ---------------------- |
| GET              | `/coupons/`                 | Required | List coupons           |
| GET              | `/coupons/{id}/`            | Required | Get single coupon      |
| POST             | `/coupons/`                 | Admin    | Create coupon          |
| PUT/PATCH/DELETE | `/coupons/{id}/`            | Admin    | Update/delete coupon   |
| POST             | `/coupons/validate_coupon/` | Required | Validate a coupon code |

> Expired coupons are automatically deactivated by the `expire_coupons` Celery Beat task.

---

### Orders

Base URL: `/orders/`

| Method | Endpoint                     | Auth     | Description                       |
| ------ | ---------------------------- | -------- | --------------------------------- |
| POST   | `/orders/create_order/`      | Required | Place an order from the cart      |
| PATCH  | `/orders/{id}/cancel_order/` | Required | Cancel a pending/processing order |
| GET    | `/orders/order_history/`     | Required | View order history                |

**Create order example:**
```json
POST /orders/create_order/
{
  "address_id": 1,
  "payment_method": "cash_on_delivery",
  "coupon_code": "SAVE20"
}
```
> **Supported payment methods:** `cash_on_delivery`, `sslcommerz`

**Order status flow:** `pending` → `processing` → `completed` / `cancelled`

> Unpaid orders are automatically cancelled after a timeout by the `auto_cancel_orders` Celery Beat task.

---

### Payments

Base URL: `/payments/`

| Method | Endpoint                        | Auth     | Description                   |
| ------ | ------------------------------- | -------- | ----------------------------- |
| POST   | `/payments/initiate/`           | Required | Initiate payment for an order |
| POST   | `/payments/sslcommerz/success/` | Public   | SSLCommerz success callback   |
| POST   | `/payments/sslcommerz/fail/`    | Public   | SSLCommerz fail callback      |
| POST   | `/payments/sslcommerz/cancel/`  | Public   | SSLCommerz cancel callback    |
| POST   | `/payments/sslcommerz/ipn/`     | Public   | SSLCommerz IPN webhook        |
| POST   | `/payments/refund/`             | Admin    | Initiate refund               |
| GET    | `/payments/`                    | Required | List payments                 |
| GET    | `/payments/{id}/`               | Required | Payment detail                |
| GET    | `/payments/{id}/logs/`          | Required | Payment logs                  |
| GET    | `/payments/my_payments/`        | Required | Current user's payments       |

---

### Reviews

Base URL: `/reviews/`

| Method    | Endpoint                    | Auth     | Description                    |
| --------- | --------------------------- | -------- | ------------------------------ |
| GET       | `/reviews/`                 | Public   | List all reviews               |
| GET       | `/reviews/?product_id=<id>` | Public   | Reviews for a specific product |
| GET       | `/reviews/{id}/`            | Public   | Single review                  |
| POST      | `/reviews/`                 | Required | Create a review                |
| PUT/PATCH | `/reviews/{id}/`            | Required | Update your review             |
| DELETE    | `/reviews/{id}/`            | Required | Delete your review             |

> Rating must be between **1** and **5**.

---

## 🔐 Authentication

Urban Thread uses **JWT (JSON Web Token)** authentication via `djangorestframework-simplejwt`.

1. Register or login to receive `access` and `refresh` tokens.
2. Include the access token in every protected request:
   ```
   Authorization: Bearer <access_token>
   ```
3. Use `/accounts/token/refresh/` with your refresh token to get a new access token.
4. Use `/accounts/logout/` to blacklist the refresh token on logout.

---

## 💳 Payment Integration

### SSLCommerz
1. Get sandbox credentials from [SSLCommerz Developer Portal](https://developer.sslcommerz.com/).
2. Set `SSLCOMMERZ_STORE_ID`, `SSLCOMMERZ_STORE_PASSWORD`, and `SSLCOMMERZ_IS_SANDBOX=True` in `.env`.
3. Call `POST /payments/initiate/` → redirect user to returned `gateway_url`.
4. SSLCommerz calls the success/fail/cancel/IPN endpoints automatically.

### Cash on Delivery
Set `payment_method: "cash_on_delivery"` when creating the order. The order is placed immediately with `payment_status: unpaid`.

---

## 🛡 Admin Panel

Access the Django admin at: `http://127.0.0.1:8000/admin/`

All models are registered with sensible list displays, search, and filters including:
- Users, profiles, and addresses
- Products, brands, categories, images, sizes, colors
- Inventory stock levels per variant
- Orders and order items with status management
- Coupons with expiry tracking
- Payments with status badges and payment logs
- Celery periodic task management (via `django-celery-beat`)

---

## 📖 API Documentation

Two interactive API documentation UIs are available after starting the server:

| UI                               | URL                                 |
| -------------------------------- | ----------------------------------- |
| **Swagger UI** (drf-spectacular) | `http://127.0.0.1:8000/api/docs/`   |
| **Swagger UI** (drf-yasg)        | `http://127.0.0.1:8000/swagger/`    |
| **ReDoc**                        | `http://127.0.0.1:8000/redoc/`      |
| **OpenAPI JSON/YAML**            | `http://127.0.0.1:8000/api/schema/` |

---

## 🔄 CI/CD Pipeline

The project uses **GitHub Actions** for automated testing and deployment on every push to `main`.

Pipeline steps:
1. **Lint** — Code style checks
2. **Test** — Run test suite with pytest
3. **Build** — Build Docker image
4. **Deploy** — Push to registry / deploy to server

Pipeline configuration: `.github/workflows/`

---

## 📝 License

This project is licensed under the **MIT License**.