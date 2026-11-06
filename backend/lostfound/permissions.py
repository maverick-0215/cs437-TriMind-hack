from django.conf import settings
from rest_framework import authentication, permissions


def email_allowed(email):
    """S1: only addresses at exactly @iitgn.ac.in."""
    local, at, domain = (email or "").strip().lower().rpartition("@")
    return bool(local) and at == "@" and domain == settings.ALLOWED_EMAIL_DOMAIN


def is_admin(user):
    """S2: admins are the emails listed in ADMIN_EMAILS; everyone else is a student."""
    return user.is_authenticated and user.email.lower() in settings.ADMIN_EMAILS


class SessionAuthentication(authentication.SessionAuthentication):
    """Logged-out API requests get 401 instead of DRF's default 403 (S23)."""

    def authenticate_header(self, request):
        return "Session"


class IsAdmin(permissions.BasePermission):
    # S3: logged-in students get 403; logged-out visitors get 401.
    def has_permission(self, request, view):
        return is_admin(request.user)


class IsStudent(permissions.BasePermission):
    # Admins approve claims, so they must not be able to make them.
    def has_permission(self, request, view):
        return request.user.is_authenticated and not is_admin(request.user)
