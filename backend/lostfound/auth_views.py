"""Login endpoints. Plain Django views, so Django's CSRF middleware protects the POSTs."""

import json

from django.conf import settings
from django.contrib.auth import get_user_model, login, logout
from django.http import Http404, JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

from .permissions import email_allowed, is_admin


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


def _log_in(request, email, name):
    # S1: Google (or the dev login) tells us the email; we still enforce the domain.
    if not email_allowed(email):
        return JsonResponse({"detail": f"Only @{settings.ALLOWED_EMAIL_DOMAIN} accounts can log in."}, status=403)
    user, _ = get_user_model().objects.get_or_create(username=email, defaults={"email": email, "first_name": name[:150]})
    login(request, user)
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
    try:
        claims = verify_google_token(_read_json(request).get("credential", ""))
    except ValueError:
        return JsonResponse({"detail": "Google sign-in failed. Try again."}, status=400)
    # Only trust addresses Google has verified the person owns.
    if not claims.get("email_verified"):
        return JsonResponse({"detail": "Your Google email is not verified."}, status=403)
    return _log_in(request, claims["email"].lower(), claims.get("name", ""))


@require_POST
def dev_login(request):
    if not settings.DEV_LOGIN:
        raise Http404
    email = str(_read_json(request).get("email", "")).strip().lower()
    return _log_in(request, email, email.split("@")[0])


@require_POST
def logout_view(request):
    logout(request)
    return JsonResponse({"detail": "Logged out."})
