import os
from datetime import timedelta
from pathlib import Path
from urllib.parse import unquote, urlsplit
from decouple import config
import dj_database_url
from django.core.exceptions import ImproperlyConfigured


BASE_DIR = Path(__file__).resolve().parent.parent

# ─── Security ─────────────────────────────────────────────────────────────────

SECRET_KEY = config('SECRET_KEY', default='django-insecure-s&$9k=^wje4etnj+k1v(a98o80ivik#vxyov+u%v!(h$k8uv*t')
DEBUG_VALUE = str(config('DEBUG', default='True')).strip().lower()
DEBUG = DEBUG_VALUE in {'1', 'true', 'yes', 'on'}
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=lambda v: [s.strip() for s in v.split(',') if s.strip()])
render_hostname = config('RENDER_EXTERNAL_HOSTNAME', default='').strip()
if render_hostname and render_hostname not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(render_hostname)


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'django_filters',
    'django_celery_beat',
    'django_celery_results',
    'drf_yasg',
    'corsheaders',
    'accounts',
    'products',
    'cart',
    'orders',
    'coupons',
    'payments',
    'inventory',
    'reviews',
    'chatbot',
    'management.apps.ManagementConfig',
    'drf_spectacular',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
     'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'urbanthread.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'urbanthread.wsgi.application'


# ─── Database (PostgreSQL) ────────────────────────────────────────────────────

# Prefer a hosted DATABASE_URL (for Render/Supabase); otherwise retain the local DB_ENGINE settings.
database_url = config('DATABASE_URL', default='').strip()
if database_url:
    DATABASES = {
        'default': dj_database_url.parse(
            database_url,
            conn_max_age=600,
            conn_health_checks=True,
            ssl_require=True,
        )
    }
else:
    db_engine = config('DB_ENGINE', default='django.db.backends.sqlite3')
    if 'sqlite' in db_engine:
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': BASE_DIR / 'db.sqlite3',
            }
        }
    else:
        DATABASES = {
            'default': {
                'ENGINE': db_engine,
                'NAME': config('DB_NAME', default='urbanthread'),
                'USER': config('DB_USER', default=''),
                'PASSWORD': config('DB_PASSWORD', default=''),
                'HOST': config('DB_HOST', default='localhost'),
                'PORT': config('DB_PORT', default=''),
            }
        }

# Cache Configuration
REDIS_URL = config('REDIS_URL', default='locmem')
REDIS_ENABLED = REDIS_URL.startswith(('redis://', 'rediss://'))

if not REDIS_ENABLED:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'urbanthread-local-cache',
        }
    }
    SESSION_ENGINE = 'django.contrib.sessions.backends.db'
else:
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': REDIS_URL,
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                'IGNORE_EXCEPTIONS': True,
                'CONNECTION_POOL_KWARGS': {
                    'max_connections': 50,
                },
                'SOCKET_CONNECT_TIMEOUT': 5,
                'SOCKET_TIMEOUT': 5,
            },
            'KEY_PREFIX': 'urbanthread',
            'TIMEOUT': 300,
        }
    }
    SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
    SESSION_CACHE_ALIAS = 'default'

# ── Celery ────────────────────────────────────────────────────────────────────
if not REDIS_ENABLED:
    # Local Django cache mode has no Celery backend named "locmem". Use a
    # process-local broker and disable results until a real broker is configured.
    CELERY_BROKER_URL = config("CELERY_BROKER_URL", default="memory://")
    CELERY_RESULT_BACKEND = config("CELERY_RESULT_BACKEND", default=None) or None
    CELERY_TASK_IGNORE_RESULT = True
    # A memory broker has no separate worker, so execute background tasks inline locally.
    CELERY_TASK_ALWAYS_EAGER = config("CELERY_TASK_ALWAYS_EAGER", default=True, cast=bool)
    CELERY_TASK_EAGER_PROPAGATES = config("CELERY_TASK_EAGER_PROPAGATES", default=True, cast=bool)
else:
    CELERY_BROKER_URL = config("CELERY_BROKER_URL", default=REDIS_URL)
    CELERY_RESULT_BACKEND = config("CELERY_RESULT_BACKEND", default=REDIS_URL)
    CELERY_TASK_ALWAYS_EAGER = config("CELERY_TASK_ALWAYS_EAGER", default=False, cast=bool)
    CELERY_TASK_EAGER_PROPAGATES = config("CELERY_TASK_EAGER_PROPAGATES", default=False, cast=bool)
 
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "Asia/Dhaka"
 
# Store task results so Flower can display them
CELERY_TASK_TRACK_STARTED = True
CELERY_RESULT_EXTENDED = True
 
# Retry policy defaults — individual tasks can override
CELERY_TASK_ACKS_LATE = True                  # ack only after task succeeds
CELERY_TASK_REJECT_ON_WORKER_LOST = True
 
# Beat scheduler — stores schedule in the database (survives restarts)
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"

CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOW_CREDENTIALS = False
from corsheaders.defaults import default_headers
CORS_ALLOW_HEADERS = (*default_headers, 'x-guest-cart')
CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    default='http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174,http://localhost:8080,https://urbanthreadshop.vercel.app',
    cast=lambda value: [origin.strip().rstrip('/') for origin in value.split(',') if origin.strip()],
)

# Password validation

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Dhaka'

USE_I18N = True

USE_TZ = True



STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
AUTH_USER_MODEL = "accounts.CustomUser"
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Configure Cloudinary for every Django ImageField when credentials are present.
# Keep local filesystem storage available for development without Cloudinary keys.
CLOUDINARY_URL = config('CLOUDINARY_URL', default='').strip()
if CLOUDINARY_URL:
    if not CLOUDINARY_URL.startswith('cloudinary://'):
        raise ImproperlyConfigured(
            'CLOUDINARY_URL must use the format cloudinary://API_KEY:API_SECRET@CLOUD_NAME.'
        )
    parsed_cloudinary_url = urlsplit(CLOUDINARY_URL)
    CLOUDINARY_API_KEY = unquote(parsed_cloudinary_url.username or '')
    CLOUDINARY_API_SECRET = unquote(parsed_cloudinary_url.password or '')
    CLOUDINARY_CLOUD_NAME = parsed_cloudinary_url.hostname or ''
    if not all((CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET, CLOUDINARY_CLOUD_NAME)):
        raise ImproperlyConfigured(
            'CLOUDINARY_URL must include API_KEY, API_SECRET, and CLOUD_NAME.'
        )
    os.environ.setdefault('CLOUDINARY_URL', CLOUDINARY_URL)
    import cloudinary

    cloudinary.config(
        cloud_name=CLOUDINARY_CLOUD_NAME,
        api_key=CLOUDINARY_API_KEY,
        api_secret=CLOUDINARY_API_SECRET,
        secure=True,
    )
    STORAGES = {
        'default': {'BACKEND': 'urbanthread.storage.CloudinaryMediaStorage'},
        'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage'},
    }
else:
    CLOUDINARY_CLOUD_NAME = config('CLOUDINARY_CLOUD_NAME', default='').strip()
    CLOUDINARY_API_KEY = config('CLOUDINARY_API_KEY', default='').strip()
    CLOUDINARY_API_SECRET = config('CLOUDINARY_API_SECRET', default='').strip()
    cloudinary_values = (CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET)
    if any(cloudinary_values) and not all(cloudinary_values):
        raise ImproperlyConfigured(
            'Set all of CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, and CLOUDINARY_API_SECRET.'
        )

    if all(cloudinary_values):
        import cloudinary

        cloudinary.config(
            cloud_name=CLOUDINARY_CLOUD_NAME,
            api_key=CLOUDINARY_API_KEY,
            api_secret=CLOUDINARY_API_SECRET,
            secure=True,
        )
        default_storage_backend = 'urbanthread.storage.CloudinaryMediaStorage'
    else:
        default_storage_backend = 'django.core.files.storage.FileSystemStorage'

    STORAGES = {
        'default': {'BACKEND': default_storage_backend},
        'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage'},
    }


# REST Framework Configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_THROTTLE_RATES': {
        'login': '5/minute',
        'register': '5/hour',
        'coupon_validate': '30/minute',
        'password_reset_request': '3/hour',
        'password_reset_confirm': '10/hour',
        'password_change': '5/hour',
        'email_verification_request': '3/hour',
        'email_verification_confirm': '10/hour',
        'google_sign_in': '20/minute',
        'chatbot': '20/minute',
    },
}
EMAIL_DAILY_SEND_CAP = config('EMAIL_DAILY_SEND_CAP', default=250, cast=int)
EMAIL_OTP_COOLDOWN_SECONDS = config('EMAIL_OTP_COOLDOWN_SECONDS', default=60, cast=int)
EMAIL_OTP_PER_ADDRESS_PER_HOUR = config('EMAIL_OTP_PER_ADDRESS_PER_HOUR', default=3, cast=int)

# drf-spectacular (OpenAPI/Swagger) configuration
SPECTACULAR_SETTINGS = {
    'TITLE': 'UrbanThread API',
    'DESCRIPTION': 'Comprehensive API documentation for UrbanThread e-commerce services.',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'SCHEMA_PATH_PREFIX': r'/api/v1',
    'SORT_OPERATIONS': True,
    'SORT_OPERATION_PARAMETERS': True,
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'displayRequestDuration': True,
        'persistAuthorization': True,
        'filter': True,
        'tryItOutEnabled': True,
        'docExpansion': 'none',
    },
    'COMPONENT_SPLIT_REQUEST': True,
    'COMPONENT_NO_READ_ONLY_REQUIRED': True,
    'SECURITY': [{'BearerAuth': []}],
    'APPEND_COMPONENTS': {
        'securitySchemes': {
            'BearerAuth': {
                'type': 'http',
                'scheme': 'bearer',
                'bearerFormat': 'JWT',
            }
        }
    },
    'TAGS': [
        {'name': 'Accounts - Register', 'description': 'User registration endpoints.'},
        {'name': 'Accounts - Login', 'description': 'Authentication and logout endpoints.'},
        {'name': 'Accounts - Users', 'description': 'User management endpoints.'},
        {'name': 'Accounts - Profile', 'description': 'Profile management endpoints.'},
        {'name': 'Accounts - Address', 'description': 'Address management endpoints.'},
        
        {'name': 'Products', 'description': 'Product listing and detail endpoints.'},
        {'name': 'Products - Categories', 'description': 'Category management endpoints.'},
        {'name': 'Products - Brands', 'description': 'Brand management endpoints.'},
        {'name': 'Products - Images', 'description': 'Product image endpoints.'},
        {'name': 'Products - Sizes', 'description': 'Available sizes endpoints.'},
        {'name': 'Products - Colors', 'description': 'Available colors endpoints.'},
        
        {'name': 'Inventory - List & Detail', 'description': 'Inventory read/write endpoints.'},
        {'name': 'Inventory - Availability', 'description': 'Stock availability lookup endpoints.'},
        {'name': 'Coupons', 'description': 'Coupon validation and management endpoints.'},
        
        {'name': 'Cart', 'description': 'Cart management endpoints.'},
        
        {'name': 'Orders', 'description': 'Order management endpoints.'},
        
        {'name': 'Payments - Gateway', 'description': 'Payment gateway endpoints.'},
        {'name': 'Payments - History', 'description': 'Payment history endpoints.'},
        {'name': 'Payments - Initiate', 'description': 'Payment initiation endpoints.'},
        {'name': 'Payments - Callbacks', 'description': 'Payment gateway callback endpoints.'},
        {'name': 'Payments - IPN', 'description': 'IPN update endpoints.'},
        {'name': 'Payments - Refunds', 'description': 'Admin refund endpoints.'},
    ],
}


# JWT Configuration (Fixed - Using standard tokens, not sliding)
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=10),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': False,

    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    'JWK_URL': None,
    'LEEWAY': 0,

    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',

    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'TOKEN_USER_CLASS': 'rest_framework_simplejwt.models.TokenUser',

    'JTI_CLAIM': 'jti',
}

# SSL Commerce Configuration
SSLCOMMERZ_STORE_ID = config('SSLCOMMERZ_STORE_ID', default='')
OPENAI_API_KEY = config('OPENAI_API_KEY', default='').strip()
OPENAI_CHAT_MODEL = config('OPENAI_CHAT_MODEL', default='gpt-4o-mini').strip()

# Google Gemini API (free tier) — used as primary chatbot provider
GEMINI_API_KEY = config('GEMINI_API_KEY', default='').strip()
GEMINI_CHAT_MODEL = config('GEMINI_CHAT_MODEL', default='gemini-3.8-flash').strip()

# Which chatbot provider to use: 'gemini' (free) or 'openai'
CHATBOT_PROVIDER = config('CHATBOT_PROVIDER', default='gemini').strip().lower()
SSLCOMMERZ_STORE_PASSWORD = config('SSLCOMMERZ_STORE_PASSWORD', default='')
SSLCOMMERZ_IS_SANDBOX = config('SSLCOMMERZ_IS_SANDBOX', default=True, cast=bool)

# Frontend URL for payment redirects
_raw_frontend_url = config('FRONTEND_URL', default='http://localhost:5173')
FRONTEND_URL = _raw_frontend_url.split(',')[0].strip().rstrip('/')
BACKEND_PUBLIC_URL = config('BACKEND_PUBLIC_URL', default='')

# Email Configuration
SENDGRID_API_KEY = config('SENDGRID_API_KEY', default='').strip()
BREVO_API_KEY = config('BREVO_API_KEY', default='').strip()
ORDER_EMAILS_SYNC = config('ORDER_EMAILS_SYNC', default=False, cast=bool)
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@urbanthread.com').strip()
BREVO_SENDER_EMAIL = config('BREVO_SENDER_EMAIL', default=DEFAULT_FROM_EMAIL).strip()
BREVO_SENDER_NAME = config('BREVO_SENDER_NAME', default='UrbanThread').strip()
if BREVO_API_KEY:
    # Brevo takes precedence over the old SendGrid backend when its API key is configured.
    EMAIL_BACKEND = 'accounts.brevo_email_backend.BrevoEmailBackend'
else:
    EMAIL_BACKEND = config(
        'EMAIL_BACKEND',
        default=(
            'accounts.email_backend.SendGridEmailBackend'
            if SENDGRID_API_KEY
            else 'django.core.mail.backends.console.EmailBackend'
        ),
    )
# SendGrid's HTTPS API avoids outbound SMTP ports that are often blocked.
SENDGRID_API_URL = config(
    'SENDGRID_API_URL',
    default='https://api.sendgrid.com/v3/mail/send',
)
SENDGRID_API_TIMEOUT = config('SENDGRID_API_TIMEOUT', default=15, cast=int)
BREVO_API_URL = config('BREVO_API_URL', default='https://api.brevo.com/v3/smtp/email').strip()
BREVO_API_TIMEOUT = config('BREVO_API_TIMEOUT', default=15, cast=int)
EMAIL_HOST = config('EMAIL_HOST', default='smtp.sendgrid.net')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
# Retain the SMTP settings for deployments that explicitly choose Django's SMTP backend.
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='apikey' if SENDGRID_API_KEY else '')
# Ignore a stale Gmail password in .env when SendGrid is selected.
EMAIL_HOST_PASSWORD = (
    SENDGRID_API_KEY
    if SENDGRID_API_KEY and EMAIL_HOST == 'smtp.sendgrid.net'
    else config('EMAIL_HOST_PASSWORD', default='')
)
EMAIL_TIMEOUT = config('EMAIL_TIMEOUT', default=10, cast=int)
SMS_API_URL = config('SMS_API_URL', default='')
SMS_API_TOKEN = config('SMS_API_TOKEN', default='')
SMS_SENDER_ID = config('SMS_SENDER_ID', default='UrbanThread')
GOOGLE_CLIENT_ID = config('GOOGLE_CLIENT_ID', default='')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
