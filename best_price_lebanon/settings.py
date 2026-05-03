from pathlib import Path
import os
from datetime import timedelta
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

def env_bool(name, default=False):
    return os.environ.get(name, str(default)).lower() in {'1', 'true', 'yes', 'on'}

# SECURITY WARNING: keep the secret key used in production secret.
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'dev-only-change-me')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env_bool('DEBUG', False) # Default to False for safety

# ALLOWED_HOSTS needs to include your fly.dev domain
ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get('ALLOWED_HOSTS', '').split(',')
    if host.strip()
]
if os.environ.get('FLY_APP_NAME'):
    ALLOWED_HOSTS.append(f"{os.environ.get('FLY_APP_NAME')}.fly.dev")

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'rest_framework',
    'rest_framework_simplejwt.token_blacklist',
    'authentication',
    'scraping',
    'api',
    'comparisons',
    'whitenoise.runserver_nostatic', # For serving static files
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', # MUST be here
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# CORS/CSRF Configuration
FRONTEND_URLS = os.environ.get('FRONTEND_URLS', 'http://localhost:5173,http://127.0.0.1:5173')
origins = [url.strip() for url in FRONTEND_URLS.split(',') if url.strip()]
CORS_ALLOWED_ORIGINS = origins
CSRF_TRUSTED_ORIGINS = origins
CORS_ALLOW_CREDENTIALS = True

ROOT_URLCONF = 'best_price_lebanon.urls'

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

WSGI_APPLICATION = 'best_price_lebanon.wsgi.application'

# Database
# Fly.io provides DATABASE_URL automatically if you attach a Postgres cluster
if os.environ.get('DATABASE_URL'):
    DATABASES = {
        'default': dj_database_url.config(
            conn_max_age=600,
            conn_health_checks=True,
            ssl_require=True
        )
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('POSTGRES_NAME', 'lebanon_prices'),
            'USER': os.environ.get('POSTGRES_USER', 'awfarlak'),
            'PASSWORD': os.environ.get('POSTGRES_PASSWORD', '123StrongPass@'),
            'HOST': os.environ.get('POSTGRES_HOST', 'localhost'),
            'PORT': '5432',
        }
    }

# Celery & Redis
redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
CELERY_BROKER_URL = redis_url
CELERY_RESULT_BACKEND = redis_url

# Static Files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Auth & REST settings (Keeping your existing logic)
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}

# AI & OAuth Keys
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
GOOGLE_OAUTH_CLIENT_ID = os.environ.get('GOOGLE_OAUTH_CLIENT_ID', '')

# Production Security
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
