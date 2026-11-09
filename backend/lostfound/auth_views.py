"""Login endpoints. Plain Django views, so Django's CSRF middleware protects the POSTs.

S1: people sign in with their IITGN Google account. There are no passwords in this app.
"""

import json

from django.conf import settings
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.hashers import make_password
from django.http import Http404, JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

from .permissions import email_allowed, is_admin, is_admin_email


def _user_json(user):
    return {
        "email": user.email,
        "name": user.first_name,
        "is_admin": is_admin(user),
        "unread_notifications": user.notifications.filter(is_read=False).count(),
    }


def _read_json(request):
    try:
        body = json.loads(request.body)
    except ValueError:
        return {}
    return body if isinstance(body, dict) else {}


def _role_error(email, role):
    """S24: the role picked on the login page must match the user's real role. Picking never grants it."""
    admin = is_admin_email(email)
    if role == "admin" and not admin:
        return "This account is not a security office admin. Use \"Sign in as student\"."
    if role == "student" and admin:
        return "This is a security office account. Use \"Sign in as admin\"."
    return None


def get_or_create_user(email, name=""):
    user, _ = get_user_model().objects.get_or_create(
        username=email,
        defaults={
            "email": email,
            "first_name": (name or email.split("@")[0])[:150],
            # Sign-in is through Google only, so no account has a password.
            "password": make_password(None),
        },
    )
    return user


def _log_in(request, email, name, role=None):
    # S1: Google (or the dev login) tells us the email; we still enforce the domain.
    if not email_allowed(email):
        return JsonResponse({"detail": f"Only @{settings.ALLOWED_EMAIL_DOMAIN} accounts can log in."}, status=403)
    if role is not None and (message := _role_error(email, role)):
        return JsonResponse({"detail": message}, status=403)
    user = get_or_create_user(email, name)
    login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    return JsonResponse(_user_json(user))


@require_GET
@ensure_csrf_cookie
def config(request):
    return JsonResponse({"google_client_id": settings.GOOGLE_CLIENT_ID, "dev_login": settings.DEV_LOGIN})


@require_GET
@ensure_csrf_cookie
def me(request):
    if not request.user.is_authenticated:
        return JsonResponse({"detail": "Not logged in."}, status=401)
    return JsonResponse(_user_json(request.user))


def verify_google_token(credential):
    """Return the claims of a Google ID token after checking its signature and audience."""
    return id_token.verify_oauth2_token(credential, google_requests.Request(), settings.GOOGLE_CLIENT_ID)


@require_POST
def google_login(request):
    if not settings.GOOGLE_CLIENT_ID:
        return JsonResponse({"detail": "Google sign-in is not configured."}, status=503)
    body = _read_json(request)
    try:
        claims = verify_google_token(body.get("credential", ""))
    except ValueError:
        return JsonResponse({"detail": "Google sign-in failed. Try again."}, status=400)
    # Only trust addresses Google has verified the person owns.
    if not claims.get("email_verified"):
        return JsonResponse({"detail": "Your Google email is not verified."}, status=403)
    return _log_in(request, claims["email"].lower(), claims.get("name", ""), body.get("role"))


@require_POST
def dev_login(request):
    if not settings.DEV_LOGIN:
        raise Http404
    body = _read_json(request)
    email = str(body.get("email", "")).strip().lower()
    return _log_in(request, email, email.split("@")[0], body.get("role"))


@require_POST
def logout_view(request):
    logout(request)
    return JsonResponse({"detail": "Logged out."})
