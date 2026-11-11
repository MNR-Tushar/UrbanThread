import os
from datetime import timedelta
from pathlib import Path
from decouple import config


BASE_DIR = Path(__file__).resolve().parent.parent

# ─── Security ─────────────────────────────────────────────────────────────────

SECRET_KEY = config('SECRET_KEY', default='django-insecure-s&$9k=^wje4etnj+k1v(a98o80ivik#vxyov+u%v!(h$k8uv*t')
DEBUG_VALUE = str(config('DEBUG', default='True')).strip().lower()
DEBUG = DEBUG_VALUE in {'1', 'true', 'yes', 'on'}
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=lambda v: [s.strip() for s in v.split(',')])


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

# Database - PostgreSQL
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

if REDIS_URL == 'locmem' or not REDIS_URL.startswith('redis://'):
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
if REDIS_URL == "locmem" or not REDIS_URL.startswith("redis://"):
    # Local Django cache mode has no Celery backend named "locmem". Use a
    # process-local broker and disable results until a real broker is configured.
    CELERY_BROKER_URL = config("CELERY_BROKER_URL", default="memory://")
    CELERY_RESULT_BACKEND = config("CELERY_RESULT_BACKEND", default=None) or None
    CELERY_TASK_IGNORE_RESULT = True
else:
    CELERY_BROKER_URL = config("CELERY_BROKER_URL", default=REDIS_URL)
    CELERY_RESULT_BACKEND = config("CELERY_RESULT_BACKEND", default=REDIS_URL)
 
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
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    "http://localhost:8080",
]

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
}

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
SSLCOMMERZ_STORE_PASSWORD = config('SSLCOMMERZ_STORE_PASSWORD', default='')
SSLCOMMERZ_IS_SANDBOX = config('SSLCOMMERZ_IS_SANDBOX', default=True, cast=bool)

# Frontend URL for payment redirects
FRONTEND_URL = config('FRONTEND_URL', default='http://localhost:5173')
BACKEND_PUBLIC_URL = config('BACKEND_PUBLIC_URL', default='')

# Email Configuration
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@urbanthread.com')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
