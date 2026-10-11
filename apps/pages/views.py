from django.http import HttpResponse
from django.shortcuts import render
from django.template.loader import render_to_string


def service_worker(request):
    resp = HttpResponse(render_to_string("pwa/sw.js", request=request), content_type="application/javascript")
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
