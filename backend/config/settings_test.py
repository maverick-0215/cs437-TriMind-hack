import os

os.environ.setdefault("SECRET_KEY", "test-only-key")

from .settings import *  # noqa: E402, F403

ADMIN_EMAILS = {"guard@iitgn.ac.in"}
GOOGLE_CLIENT_ID = "test-client-id"
DEV_LOGIN = False
