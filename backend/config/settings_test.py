import os
import tempfile

os.environ.setdefault("SECRET_KEY", "test-only-key")

from .settings import *  # noqa: E402, F403

ADMIN_EMAILS = {"guard@iitgn.ac.in"}
GOOGLE_CLIENT_ID = "test-client-id"
DEV_LOGIN = False
# Tests read sent mail from django.core.mail.outbox.
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
# A file, not SQLite's default in-memory database, so threaded tests can run requests at
# the same time: in memory, a second connection fails at once with "table is locked".
DATABASES["default"]["TEST"] = {"NAME": os.path.join(tempfile.gettempdir(), "lostfound_test.sqlite3")}  # noqa: F405
