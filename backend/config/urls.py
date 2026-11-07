from django.conf import settings
from django.http import FileResponse, Http404
from django.urls import include, path, re_path


def frontend(request):
    """Every page that is not the API gets the React app, which handles its own routes."""
    index = settings.FRONTEND_DIST / "index.html"
    if not index.is_file():
        raise Http404("The frontend is not built. Run `npm run build` in frontend/ and copy dist/ to backend/frontend_dist/.")
    response = FileResponse(index.open("rb"), content_type="text/html")
    response["Cache-Control"] = "no-cache"  # always pick up a new deploy
    return response


urlpatterns = [
    path("api/", include("lostfound.urls")),
    re_path(r"^(?!api/).*$", frontend),
]
