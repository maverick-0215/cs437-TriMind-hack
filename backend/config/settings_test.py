import os

os.environ.setdefault("SECRET_KEY", "test-only-key")

from .settings import *  # noqa: E402, F403

ADMIN_EMAILS = {"guard@iitgn.ac.in"}
GOOGLE_CLIENT_ID = "test-client-id"
DEV_LOGIN = False
# Fast in-memory cache for tests; production shares one in the database.
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
# Tests read sent mail from django.core.mail.outbox.
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
