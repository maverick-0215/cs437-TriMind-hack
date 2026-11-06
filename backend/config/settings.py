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

# S1: only this domain can sign up or log in.
ALLOWED_EMAIL_DOMAIN = "iitgn.ac.in"
# S2: comma-separated admin emails; everyone else is a student.
ADMIN_EMAILS = {e.strip().lower() for e in os.environ.get("ADMIN_EMAILS", "").split(",") if e.strip()}
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
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
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

# Photos are private (S7): never served from a public URL, only through an admin endpoint.
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["lostfound.permissions.SessionAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
}
