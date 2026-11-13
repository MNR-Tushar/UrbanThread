# UrbanThread backend

Django 6 and Django REST Framework API for the UrbanThread clothing store. The API provides accounts, catalog, inventory, cart, coupons, orders, payments, reviews, admin reporting, and optional Celery background jobs.

## Requirements

- Python 3.12 (the Docker image uses Python 3.12)
- pip
- PostgreSQL only if you choose PostgreSQL; SQLite is the local default
- Redis only for shared Redis caching and production Celery workers; local settings use in-memory cache and a process-local Celery broker

Install dependencies from this directory:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

If using the workspace-level virtual environment instead, run `..\venv\Scripts\Activate.ps1` from this directory.

## Configuration

Django reads settings from environment variables and an optional `.env` file in this directory. Local SQLite and in-memory cache have defaults, so a minimal local setup does not require `.env`. For a team or production setup, create `.env` locally and never commit credentials.

| Variable | Default / purpose |
| --- | --- |
| `SECRET_KEY` | Development-only insecure fallback; set a private random value outside local development. |
| `DEBUG` | `True` by default; set `False` in production. |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1`; comma-separated Django host names. |
| `DB_ENGINE` | `django.db.backends.sqlite3`; use `django.db.backends.postgresql` for PostgreSQL. |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | PostgreSQL connection values when `DB_ENGINE` is not SQLite. |
| `REDIS_URL` | `locmem`; use a Redis URL such as `redis://localhost:6379/0` for Redis cache and the default Celery broker/result backend. |
| `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND` | Optional overrides when Redis is configured. |
| `SSLCOMMERZ_STORE_ID`, `SSLCOMMERZ_STORE_PASSWORD` | SSLCommerz credentials; blank by default. |
| `SSLCOMMERZ_IS_SANDBOX` | `True` by default. |
| `FRONTEND_URL` | `http://localhost:5173`; payment return destination. |
| `BACKEND_PUBLIC_URL` | Empty by default; set to the public HTTPS backend URL so SSLCommerz can call back/IPN. A payment provider cannot reach a localhost callback. |
| `EMAIL_BACKEND` | Django console email backend. Use `django.core.mail.backends.smtp.EmailBackend` with `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USE_TLS`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, and `DEFAULT_FROM_EMAIL` for SMTP. |

The configured Django timezone and Celery timezone are `Asia/Dhaka`. CORS currently allows local Vite origins on ports 5173 and 5174.

## Run locally

From the backend directory, with its virtual environment active:

```powershell
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 127.0.0.1:8000
```

The superuser command is optional if you already have an admin account. SQLite database and uploaded media live under this directory (`db.sqlite3` and `media/`).

## Docker Compose

Compose starts PostgreSQL, Redis, Django/Gunicorn, Celery worker, Celery Beat, and Flower. Create a local `.env` file first with at least:

```dotenv
SECRET_KEY=replace-with-a-private-random-secret
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1
DB_ENGINE=django.db.backends.postgresql
DB_NAME=urbanthread
DB_USER=urbanthread
DB_PASSWORD=replace-with-a-local-password
DB_HOST=db
DB_PORT=5432
REDIS_URL=redis://redis:6379/0
```

Then run:

```powershell
docker compose up --build
```

Create an admin account with `docker compose exec web python manage.py createsuperuser`. Compose exposes Django on port 8000, Redis on 6379, and Flower on 5555. Stop containers with `docker compose down`; named data volumes remain. `docker compose down -v` removes stored database/media/cache data.

## API and authentication

All API routes are rooted at `http://127.0.0.1:8000/`. JWT authentication uses `Authorization: Bearer <access-token>`. Public catalog/review reads and payment gateway callbacks are exceptions; other API endpoints require authentication, with management operations restricted to staff where implemented.

| Area | Routes |
| --- | --- |
| Accounts | `/accounts/register/`, `/accounts/login/`, `/accounts/token/refresh/`, `/accounts/logout/`, `/accounts/allusers/`, `/accounts/profile/`, `/accounts/address/` |
| Catalog | `/products/categories/`, `/products/brands/`, `/products/products/`, `/products/product-images/`, `/products/banners/`, `/products/store-settings/`, `/products/sizes/`, `/products/colors/`, `/products/wishlist/` |
| Inventory | `/inventory/inventorys/`, including `check_availability/` and `product_inventory/` actions |
| Cart | `/cart/my_cart/`, `/cart/add_item/`, `/cart/update_item/`, `/cart/remove_item/`, `/cart/clear_cart/` |
| Coupons | `/coupons/`, `/coupons/validate_coupon/` |
| Orders | `/orders/create_order/`, `/orders/order_history/`, `/orders/{id}/`, `/orders/{id}/cancel_order/`; staff actions include `/orders/admin_dashboard/`, `/orders/admin_orders/`, `/orders/{id}/admin_update_status/`, `/orders/export_sales_report/` |
| Payments | `/payments/initiate/`, `/payments/my_payments/`, `/payments/`, `/payments/{id}/logs/`, `/payments/refund/`, and `/payments/sslcommerz/{success,fail,cancel,ipn}/` |
| Reviews | `/reviews/` and `/reviews/{id}/`; filter reviews with `?product_id=<id>` |

Product list supports filters for `category`, `brand`, and `is_available`, text search through `search`, and ordering through `ordering`. For example:

```text
GET /products/products/?search=shirt&category=1&brand=2&is_available=true&ordering=-created_at&limit=20&offset=0
```

The product, category, and brand list endpoints use limit/offset pagination. Inventory supports `product`, `size`, and `color` filters plus search and ordering; its read-only availability actions are public, while inventory management requires staff. Product, category, and brand management also requires staff. Cart and order history are scoped to the signed-in user; staff reporting endpoints are restricted to staff.

Exact methods, payloads, serializers, filters, and permissions are documented by the live OpenAPI schema. A typical order request is:

```json
{
  "address_id": 1,
  "payment_method": "cash_on_delivery",
  "coupon_code": ""
}
```

Allowed order payment methods are `cash_on_delivery` and `sslcommerz`. Order placement snapshots the chosen delivery address, creates a payment record, decrements inventory, and removes purchased cart items in the same transaction. SSLCommerz requires credentials and a publicly reachable callback URL for provider callbacks/IPN.

## API documentation

With Django running:

- Swagger UI: `http://127.0.0.1:8000/api/docs/`
- OpenAPI schema: `http://127.0.0.1:8000/api/schema/`
- ReDoc: `http://127.0.0.1:8000/api/schema/redoc/`
- Django admin: `http://127.0.0.1:8000/admin/`

## Celery jobs

For asynchronous email, stock sync, callback retry, analytics and scheduled tasks, configure Redis and run these commands in separate terminals from this directory:

```powershell
celery -A urbanthread worker --loglevel=info
celery -A urbanthread beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

Flower is included in Compose at `http://127.0.0.1:5555/`. Scheduled tasks include coupon activation/expiry, stale order cancellation, daily order summaries, stock/restock notices, abandoned-cart reminders, and failed-payment callback retries. Without a broker, selected request flows have local fallback behavior; queued and scheduled jobs do not run in the background.

## Checks and tests

Run from the backend directory:

```powershell
python manage.py check
python manage.py test
```

The app `tests.py` files are currently Django test placeholders, so `manage.py test` does not provide meaningful feature coverage yet. The GitHub Actions workflow runs Django checks and tests, then builds and publishes the backend Docker image to GHCR on pushes to `main` or `master`. Its production SSH deploy job is commented out, so the workflow does not currently deploy the app automatically.

For model changes, create and apply migrations with `python manage.py makemigrations` and `python manage.py migrate`. `populate_test_data.py` creates predictable demo accounts, including a hard-coded admin password; use it only in a disposable local database, never on a shared or production database.
