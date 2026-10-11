from pathlib import Path

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render
from django.template.loader import render_to_string


def _sw_version():
    """Changes after every collectstatic (or when DEPLOY_VERSION changes) so phones refresh their cache."""
    parts = [str(getattr(settings, "DEPLOY_VERSION", ""))]
    try:
        parts.append(str(int((Path(str(settings.STATIC_ROOT)) / "staticfiles.json").stat().st_mtime)))
    except OSError:
        pass
    return "-".join(p for p in parts if p) or "1"


def service_worker(request):
    body = render_to_string("pwa/sw.js", {"sw_version": _sw_version()}, request=request)
    resp = HttpResponse(body, content_type="application/javascript")
    resp["Service-Worker-Allowed"] = "/"
    resp["Cache-Control"] = "no-cache"
    return resp


def manifest(request):
    return HttpResponse(
        render_to_string("pwa/manifest.webmanifest", request=request),
        content_type="application/manifest+json",
    )


def offline(request):
    return render(request, "pwa/offline.html")
