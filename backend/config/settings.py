import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from django.core.management.utils import get_random_secret_key
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

DEBUG = os.environ.get("DEBUG", "0") == "1"
# Never fall back to a fixed key: anyone who knows the key can forge a login cookie.
SECRET_KEY = os.environ.get("SECRET_KEY") or (get_random_secret_key() if DEBUG else "")
if not SECRET_KEY:
    raise ImproperlyConfigured("Set SECRET_KEY in backend/.env")
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
# Where the React app is served from; its POSTs carry this Origin.
CSRF_TRUSTED_ORIGINS = os.environ.get("CSRF_TRUSTED_ORIGINS", "http://localhost:5173").split(",")
# Azure App Service sets WEBSITE_HOSTNAME (e.g. iitgn-lostfound.azurewebsites.net).
if AZURE_HOST := os.environ.get("WEBSITE_HOSTNAME"):
    ALLOWED_HOSTS.append(AZURE_HOST)
    CSRF_TRUSTED_ORIGINS.append(f"https://{AZURE_HOST}")

# S1: only this domain can sign up or log in.
ALLOWED_EMAIL_DOMAIN = "iitgn.ac.in"
# S2: comma-separated admin emails; everyone else is a student.
ADMIN_EMAILS = {e.strip().lower() for e in os.environ.get("ADMIN_EMAILS", "").split(",") if e.strip()}
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
# S25: who students should contact about a matching found item.
SECURITY_CONTACT = os.environ.get("SECURITY_CONTACT", "IITGN Security Office, Main Gate")
# Development-only email login, for trying the app before a Google client ID exists.
# It can only be switched on together with DEBUG.
DEV_LOGIN = DEBUG and os.environ.get("DEV_LOGIN", "0") == "1"

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "rest_framework",
    "lostfound",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # Serves the built React app (FRONTEND_DIST) in production.
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

# Where the database and photos live. On Azure this is /home/data, which survives
# restarts and redeploys; locally it is the backend folder.
DATA_DIR = Path(os.environ.get("DATA_DIR", BASE_DIR))

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": DATA_DIR / "db.sqlite3",
        "OPTIONS": {
            # Wait up to 20 s for a busy database instead of the default 5 s. Azure keeps
            # /home on network storage, where SQLite's locks are slower.
            "timeout": 20,
            # Take the write lock when a transaction starts, so simultaneous writers queue
            # up instead of failing with "database is locked" halfway through.
            "transaction_mode": "IMMEDIATE",
        },
    }
}

# Optional: a real database server such as Azure Database for PostgreSQL, e.g.
# DATABASE_URL=postgres://user:password@host:5432/lostfound?sslmode=require
# Without it, the SQLite file above is used.
if DATABASE_URL := os.environ.get("DATABASE_URL"):
    import dj_database_url

    DATABASES["default"] = dj_database_url.parse(DATABASE_URL, conn_max_age=600, conn_health_checks=True)

# Shared by every server process (unlike the default per-process memory cache), so the
# wrong-password lockout (S29) counts tries from all of them. Created by startup.sh.
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "django_cache",
    }
}

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

# Photos are private (S7): never served from a public URL, only through an admin endpoint.
MEDIA_ROOT = DATA_DIR / "media"

# The built React app (`npm run build`, copied here by the deploy workflow). Django serves
# its files and sends index.html for every page that is not under /api/.
FRONTEND_DIST = Path(os.environ.get("FRONTEND_DIST", BASE_DIR / "frontend_dist"))
STATIC_URL = "static/"
if FRONTEND_DIST.is_dir():
    WHITENOISE_ROOT = FRONTEND_DIST
    # Vite puts a content hash in every file under assets/, so browsers may cache them forever.
    WHITENOISE_IMMUTABLE_FILE_TEST = r"^/assets/.+-[0-9A-Za-z_-]{8,}\.\w+$"

# Production behind HTTPS (Azure terminates TLS and forwards the original scheme).
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    # Browsers remember to always use https for this site (HSTS), for a year.
    SECURE_HSTS_SECONDS = 31536000

# Send warnings and errors to the console, so they show in Azure's log stream.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "WARNING"},
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["lostfound.permissions.SessionAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
}

# S30: email for sign-up and password-reset codes. Without EMAIL_HOST, emails are printed
# in the runserver terminal instead of sent, which is handy for trying the app.
EMAIL_HOST = os.environ.get("EMAIL_HOST", "")
if EMAIL_HOST:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
    EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
    EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
    EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "1") == "1"
else:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "IITGN Lost & Found <noreply@iitgn.ac.in>")
# Give up on a mail server that does not answer instead of hanging the request.
EMAIL_TIMEOUT = 15

# S29: same rules Django uses for admin passwords.
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
