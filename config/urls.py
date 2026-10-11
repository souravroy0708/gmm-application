from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


def healthz(request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("healthz", healthz),
    path(settings.ADMIN_URL, admin.site.urls),
    path("i18n/", include("django.conf.urls.i18n")),
    path("", include("apps.pages.urls")),
    path("", include("apps.shop.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
