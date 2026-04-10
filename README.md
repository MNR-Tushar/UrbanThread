# 🧵 Urban Thread — E-Commerce REST API

A full-featured Django REST Framework e-commerce backend for a fashion/clothing store. Supports product management, inventory, cart, orders, coupons, payments (SSLCommerz + Cash on Delivery), and reviews.

---

## 📋 Table of Contents

- [🧵 Urban Thread — E-Commerce REST API](#-urban-thread--e-commerce-rest-api)
  - [📋 Table of Contents](#-table-of-contents)
  - [🛠 Tech Stack](#-tech-stack)
  - [📁 Project Structure](#-project-structure)
  - [✨ Features](#-features)
  - [⚙️ Installation \& Setup](#️-installation--setup)
    - [1. Clone the repository](#1-clone-the-repository)
    - [2. Create \& activate a virtual environment](#2-create--activate-a-virtual-environment)
    - [3. Install dependencies](#3-install-dependencies)
    - [4. Configure environment variables](#4-configure-environment-variables)
    - [5. Apply migrations](#5-apply-migrations)
    - [6. Create a superuser](#6-create-a-superuser)
    - [7. (Optional) Collect static files](#7-optional-collect-static-files)
  - [🔑 Environment Variables](#-environment-variables)
  - [🚀 Running the Server](#-running-the-server)
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
  - [📝 License](#-license)

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| Framework | Django 6.x + Django REST Framework |
| Auth | JWT via `djangorestframework-simplejwt` |
| Database | SQLite (dev) — easily swappable to PostgreSQL |
| Payment Gateway | SSLCommerz |
| Filtering | `django-filter` |
| API Docs | drf-spectacular (Swagger) + drf-yasg (ReDoc) |
| CORS | `django-cors-headers` |
| Config | `python-decouple` |

---

## 📁 Project Structure

```
urbanthread/
├── accounts/        # Custom user, profile, address
├── products/        # Category, brand, product, images, size, color
├── inventory/       # Stock management per product variant
├── cart/            # Shopping cart & cart items
├── coupons/         # Discount coupon management
├── orders/          # Order creation and management
├── payments/        # SSLCommerz & Cash on Delivery integration
├── reviews/         # Product reviews & ratings
├── urbanthread/     # Project settings, URLs, WSGI/ASGI
└── manage.py
```

---

## ✨ Features

- **User Auth** — Register, login, logout with JWT tokens
- **Products** — Full CRUD for categories, brands, products, images, sizes, colors
- **Inventory** — Track stock per (product × color × size) variant
- **Cart** — Add, update, remove items with real-time stock validation
- **Coupons** — Percentage-based discount coupons with expiry dates
- **Orders** — Place orders from cart, cancel orders, view history; inventory auto-decremented on order
- **Payments** — SSLCommerz online payment + Cash on Delivery; IPN support; refunds
- **Reviews** — Authenticated users can leave 1–5 star reviews on products
- **API Docs** — Swagger UI and ReDoc available out of the box

---

## ⚙️ Installation & Setup

### 1. Clone the repository

```bash
git clone https://github.com/MNR-Tushar/urbanthread.git
cd urbanthread
```

### 2. Create & activate a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

> If you don't have a `requirements.txt` yet, install the core packages:
> ```bash
> pip install django djangorestframework djangorestframework-simplejwt django-cors-headers django-filter drf-spectacular drf-yasg python-decouple pillow requests
> ```

### 4. Configure environment variables

Create a `.env` file in the project root (see [Environment Variables](#environment-variables) below).

### 5. Apply migrations

```bash
python manage.py migrate
```

### 6. Create a superuser

```bash
python manage.py createsuperuser
```

### 7. (Optional) Collect static files

```bash
python manage.py collectstatic
```

---

## 🔑 Environment Variables

Create a `.env` file in the root directory with the following keys:

```env
# Django
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# SSLCommerz Payment Gateway
SSLCOMMERZ_STORE_ID=your_store_id
SSLCOMMERZ_STORE_PASSWORD=your_store_password
SSLCOMMERZ_IS_SANDBOX=True

# Frontend URL (for payment redirects)
FRONTEND_URL=http://localhost:3000

# Email (optional)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your@email.com
EMAIL_HOST_PASSWORD=your-email-password
DEFAULT_FROM_EMAIL=noreply@urbanthread.com
```

---

## 🚀 Running the Server

```bash
python manage.py runserver
```

The API will be available at: `http://127.0.0.1:8000/`

---

## 📡 API Endpoints

All API routes are prefixed with their app name. JWT `Authorization: Bearer <access_token>` header is required for protected routes.

---

### Accounts

Base URL: `/accounts/`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/accounts/register/` | Public | Register a new user |
| POST | `/accounts/login/` | Public | Login and receive JWT tokens |
| POST | `/accounts/logout/` | Required | Blacklist refresh token / logout |
| POST | `/accounts/token/refresh/` | Public | Refresh access token |
| GET | `/accounts/allusers/` | Required | List users (admins see all) |
| GET/PUT/PATCH | `/accounts/allusers/{id}/` | Required | Get/update user |
| GET/POST | `/accounts/address/` | Required | List or create addresses |
| GET/PUT/PATCH/DELETE | `/accounts/address/{id}/` | Required | Manage a single address |
| GET/POST | `/accounts/profile/` | Required | List or create profile |
| GET/PUT/PATCH/DELETE | `/accounts/profile/{id}/` | Required | Manage profile |

**Register example:**
```json
POST /accounts/register/
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "securepassword123"
}
```

**Login example:**
```json
POST /accounts/login/
{
  "email": "john@example.com",
  "password": "securepassword123"
}
```

---

### Products

Base URL: `/products/`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/products/categories/` | Public | List all categories |
| POST | `/products/categories/` | Admin | Create category |
| GET | `/products/brands/` | Public | List all brands |
| POST | `/products/brands/` | Admin | Create brand |
| GET | `/products/products/` | Public | List all products |
| POST | `/products/products/` | Admin | Create product |
| GET | `/products/products/{id}/` | Public | Product detail |
| PUT/PATCH/DELETE | `/products/products/{id}/` | Admin | Update/delete product |
| GET/POST | `/products/product-images/` | Admin | Manage product images |
| GET | `/products/sizes/` | Public | List all sizes |
| GET | `/products/colors/` | Public | List all colors |

**Filtering & Search (products):**
- Filter: `?category=<id>&brand=<id>&is_available=true`
- Search: `?search=<keyword>`
- Order: `?ordering=price` or `?ordering=-created_at`
- Pagination: `?limit=10&offset=0`

---

### Inventory

Base URL: `/inventorys/`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/inventorys/inventorys/` | Public | List all inventory |
| POST | `/inventorys/inventorys/` | Admin | Create inventory entry |
| GET | `/inventorys/inventorys/{id}/` | Public | Single inventory entry |
| PUT/PATCH/DELETE | `/inventorys/inventorys/{id}/` | Admin | Update/delete inventory |
| GET | `/inventorys/inventorys/check_availability/` | Public | Check stock for a variant |
| GET | `/inventorys/inventorys/product_inventory/` | Public | All inventory for a product |

**Check availability:**
```
GET /inventorys/inventorys/check_availability/?product_id=1&color_id=2&size_id=3
```

---

### Cart

Base URL: `/cart/`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/cart/my_cart/` | Required | View current user's cart |
| POST | `/cart/add_item/` | Required | Add item to cart |
| PATCH | `/cart/update_item/` | Required | Update item quantity |
| DELETE | `/cart/remove_item/` | Required | Remove a single item |
| DELETE | `/cart/clear_cart/` | Required | Clear all items from cart |

**Add item example:**
```json
POST /cart/add_item/
{
  "product_id": 1,
  "color_id": 2,
  "size_id": 3,
  "quantity": 2
}
```

**Update item example:**
```json
PATCH /cart/update_item/
{
  "item_id": 5,
  "quantity": 4
}
```

---

### Coupons

Base URL: `/coupons/`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/coupons/` | Required | List coupons |
| GET | `/coupons/{id}/` | Required | Get single coupon |
| POST | `/coupons/` | Admin | Create coupon |
| PUT/PATCH/DELETE | `/coupons/{id}/` | Admin | Update/delete coupon |
| POST | `/coupons/validate_coupon/` | Required | Validate a coupon code |

**Validate coupon example:**
```json
POST /coupons/validate_coupon/
{
  "code": "SAVE20"
}
```

**Response:**
```json
{
  "valid": true,
  "discount": 20.0,
  "code": "SAVE20",
  "message": "Coupon applied! You get 20.00% off"
}
```

---

### Orders

Base URL: `/orders/`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/orders/create_order/` | Required | Place an order from the cart |
| PATCH | `/orders/{id}/cancel_order/` | Required | Cancel a pending/processing order |
| GET | `/orders/order_history/` | Required | View order history |

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

**Order status values:** `pending` → `processing` → `completed` / `cancelled`

**Payment status values:** `unpaid` → `paid` / `refunded`

---

### Payments

Base URL: `/payments/`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/payments/initiate/` | Required | Initiate payment for an order |
| POST | `/payments/sslcommerz/success/` | Public | SSLCommerz success callback |
| POST | `/payments/sslcommerz/fail/` | Public | SSLCommerz fail callback |
| POST | `/payments/sslcommerz/cancel/` | Public | SSLCommerz cancel callback |
| POST | `/payments/sslcommerz/ipn/` | Public | SSLCommerz IPN webhook |
| POST | `/payments/refund/` | Admin | Initiate refund |
| GET | `/payments/` | Required | List payments |
| GET | `/payments/{id}/` | Required | Payment detail |
| GET | `/payments/{id}/logs/` | Required | Payment logs |
| GET | `/payments/my_payments/` | Required | Current user's payments |

**Initiate SSLCommerz payment:**
```json
POST /payments/initiate/
{
  "order_number": "ORD-ABC12345",
  "payment_method": "sslcommerz"
}
```

**Response:**
```json
{
  "success": true,
  "gateway_url": "https://sandbox.sslcommerz.com/...",
  "session_key": "...",
  "transaction_id": "TXN-..."
}
```

---

### Reviews

Base URL: `/reviews/`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/reviews/` | Public | List all reviews |
| GET | `/reviews/?product_id=<id>` | Public | Reviews for a specific product |
| GET | `/reviews/{id}/` | Public | Single review |
| POST | `/reviews/` | Required | Create a review |
| PUT/PATCH | `/reviews/{id}/` | Required | Update your review |
| DELETE | `/reviews/{id}/` | Required | Delete your review |

**Create review example:**
```json
POST /reviews/
{
  "product": 1,
  "rating": 4,
  "review_text": "Great quality shirt, fits perfectly!"
}
```

> Rating must be between **1** and **5**.

---

## 🔐 Authentication

Urban Thread uses **JWT (JSON Web Token)** authentication.

1. Register or login to receive `access` and `refresh` tokens.
2. Include the access token in the request header:
   ```
   Authorization: Bearer <access_token>
   ```
3. Access tokens expire after **60 days**; refresh tokens after **10 days**.
4. Use `/accounts/token/refresh/` with your refresh token to get a new access token.
5. Use `/accounts/logout/` to blacklist the refresh token.

---

## 💳 Payment Integration

### SSLCommerz

1. Get sandbox credentials from [SSLCommerz](https://developer.sslcommerz.com/).
2. Set `SSLCOMMERZ_STORE_ID`, `SSLCOMMERZ_STORE_PASSWORD`, and `SSLCOMMERZ_IS_SANDBOX=True` in `.env`.
3. Call `POST /payments/initiate/` with `payment_method: "sslcommerz"` to get a gateway URL.
4. Redirect the user to `gateway_url`.
5. SSLCommerz will call the success/fail/cancel/IPN endpoints automatically.

### Cash on Delivery

Set `payment_method: "cash_on_delivery"` when creating the order or initiating payment. The order is placed immediately with `payment_status: unpaid`.

---

## 🛡 Admin Panel

Access the Django admin at: `http://127.0.0.1:8000/admin/`

All models are registered with sensible list displays, search, and filter configurations, including:
- Users, profiles, and addresses
- Products, brands, categories, images, sizes, colors
- Inventory stock levels
- Orders and order items
- Coupons
- Payments with status badges and payment logs

---

## 📖 API Documentation

Two interactive API documentation UIs are available after starting the server:

| UI | URL |
|---|---|
| **Swagger UI** (drf-spectacular) | `http://127.0.0.1:8000/api/docs/` |
| **Swagger UI** (drf-yasg) | `http://127.0.0.1:8000/swagger/` |
| **ReDoc** | `http://127.0.0.1:8000/redoc/` |
| **OpenAPI JSON/YAML** | `http://127.0.0.1:8000/api/schema/` |

---

## 📝 License

This project is licensed under the **MIT License**.
