"""Login endpoints. Plain Django views, so Django's CSRF middleware protects the POSTs."""

import hashlib
import hmac
import json
import logging
import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.password_validation import validate_password
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone
from django.http import Http404, JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

from .models import PasswordCode
from .permissions import email_allowed, is_admin, is_admin_email

logger = logging.getLogger(__name__)


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
        username=email, defaults={"email": email, "first_name": (name or email.split("@")[0])[:150]}
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


# --- Email and password (S29, S30) ---

CODE_LIFETIME = timedelta(minutes=10)
CODE_RESEND_WAIT = timedelta(seconds=60)
# Wrong tries allowed per email within CODE_LIFETIME, across all of its codes.
MAX_CODE_ATTEMPTS = 5
# Emails can arrive late or out of order, so the newest few codes all work, not only the last.
CODES_ACCEPTED = 3
MAX_LOGIN_FAILURES = 5
LOGIN_LOCKOUT_SECONDS = 15 * 60


def _email_from(body):
    return str(body.get("email", "")).strip().lower()


def _failures_key(email):
    return f"login-failures:{email}"


def _code_hash(email, code):
    """S30: only this is stored, never the code. A keyed SHA-256 is enough for a code that
    lives 10 minutes and allows 5 tries, and it is far faster than password hashing."""
    message = f"{email}:{code}".encode()
    return hmac.new(settings.SECRET_KEY.encode(), message, hashlib.sha256).hexdigest()


@require_POST
def password_login(request):
    """S29: sign in with email and password. Locked for 15 minutes after 5 wrong passwords."""
    body = _read_json(request)
    email, password = _email_from(body), str(body.get("password", ""))
    if not email_allowed(email):
        return JsonResponse({"detail": f"Only @{settings.ALLOWED_EMAIL_DOMAIN} accounts can log in."}, status=403)
    if cache.get(_failures_key(email), 0) >= MAX_LOGIN_FAILURES:
        return JsonResponse({"detail": "Too many wrong passwords. Try again in 15 minutes, or reset it."}, status=429)
    user = authenticate(request, username=email, password=password)
    if user is None:
        cache.set(_failures_key(email), cache.get(_failures_key(email), 0) + 1, LOGIN_LOCKOUT_SECONDS)
        # Same message whether or not the account exists.
        return JsonResponse({"detail": "Wrong email or password."}, status=400)
    cache.delete(_failures_key(email))
    return _log_in(request, email, user.first_name, body.get("role"))


@require_POST
def password_code(request):
    """S30: email a 6-digit code for setting or resetting a password."""
    email = _email_from(_read_json(request))
    if not email_allowed(email):
        return JsonResponse({"detail": f"Only @{settings.ALLOWED_EMAIL_DOMAIN} emails can be used."}, status=403)
    sent = {"detail": f"We sent a 6-digit code to {email}. It works for 10 minutes."}
    latest = PasswordCode.objects.filter(email=email).first()
    if latest and not latest.used and timezone.now() - latest.created_at < CODE_RESEND_WAIT:
        return JsonResponse(sent)  # Already sent moments ago: don't flood their inbox.
    code = f"{secrets.randbelow(10**6):06d}"
    # Send first, save after. Talking to the mail server can take seconds, and holding a
    # database transaction open meanwhile locks SQLite for every other request
    # ("database is locked"). If sending fails nothing is saved, so the next request sends
    # a fresh code instead of claiming "we sent a code".
    try:
        send_mail(
            "Your IITGN Lost & Found code",
            f"Your code is {code}\n\nEnter it on the sign-in page to set your password. It works for 10 minutes.\n"
            "If you did not ask for this, ignore this email.",
            None,
            [email],
        )
    except OSError:  # smtplib errors and network failures
        logger.exception("Could not send the password code email to %s", email)
        return JsonResponse(
            {"detail": "We couldn't send the email right now. Try again in a few minutes."}, status=503
        )
    PasswordCode.objects.create(email=email, code_hash=_code_hash(email, code))
    return JsonResponse(sent)


@require_POST
def password_reset(request):
    """S30: check the emailed code, then set the password (creating the account if new)."""
    body = _read_json(request)
    email, code, password = _email_from(body), str(body.get("code", "")).strip(), str(body.get("password", ""))
    recent = list(
        PasswordCode.objects.filter(email=email, used=False, created_at__gte=timezone.now() - CODE_LIFETIME).order_by(
            "-created_at", "-id"
        )
    )  # newest first
    if not recent:
        return JsonResponse({"detail": "That code has expired. Ask for a new one."}, status=400)
    if sum(entry.attempts for entry in recent) >= MAX_CODE_ATTEMPTS:
        return JsonResponse(
            {"detail": "Too many wrong tries. Wait 10 minutes, then ask for a new code."}, status=429
        )
    given = _code_hash(email, code)
    if not any(hmac.compare_digest(given, entry.code_hash) for entry in recent[:CODES_ACCEPTED]):
        newest = recent[0]
        newest.attempts += 1
        newest.save(update_fields=["attempts"])
        return JsonResponse(
            {"detail": "That code isn't right. Check the code in your most recent email."}, status=400
        )
    if "password_confirm" in body and str(body["password_confirm"]) != password:
        # The code stays valid so they can fix the typo.
        return JsonResponse({"detail": "The two passwords do not match."}, status=400)
    user = get_user_model().objects.filter(username=email).first() or get_user_model()(
        username=email, email=email, first_name=email.split("@")[0]
    )
    try:
        validate_password(password, user)
    except ValidationError as e:
        # The code stays valid so they can try a better password.
        return JsonResponse({"detail": " ".join(e.messages)}, status=400)
    is_new = user.pk is None
    with transaction.atomic():
        # Every code for this email is spent once one of them works.
        PasswordCode.objects.filter(email=email, used=False).update(used=True)
        user.set_password(password)
        user.save()
    cache.delete(_failures_key(email))
    _send_password_changed_email(email, is_new)
    return JsonResponse({"detail": "Password set. Sign in with your new password."})


def _send_password_changed_email(email, is_new):
    """S30: confirm by email, so the owner notices if someone else changed their password."""
    if is_new:
        subject = "Your IITGN Lost & Found account is ready"
        opening = "Your IITGN Lost & Found account was created and its password was set."
    else:
        subject = "Your IITGN Lost & Found password was changed"
        opening = "The password for your IITGN Lost & Found account was just changed."
    body = (
        f"{opening}\n\nIf this was you, there is nothing else to do.\n"
        'If it was not you, use "Forgot password?" on the sign-in page right away to set a new one.'
    )
    try:
        send_mail(subject, body, None, [email])
    except OSError:
        # The password is already set; a missing confirmation email must not undo that.
        logger.exception("Could not send the password changed email to %s", email)
