from django.conf import settings


class ContentSecurityPolicyMiddleware:
    """Sends settings.CONTENT_SECURITY_POLICY on every response: the React app, its built
    files (served by WhiteNoise, which is why this sits first) and the API. React already
    escapes text; this limits the damage if something ever slips through."""

    def __init__(self, get_response):
        self.get_response = get_response
        self.policy = "; ".join(f"{name} {' '.join(values)}" for name, values in settings.CONTENT_SECURITY_POLICY.items())

    def __call__(self, request):
        response = self.get_response(request)
        response.headers.setdefault("Content-Security-Policy", self.policy)
        return response
