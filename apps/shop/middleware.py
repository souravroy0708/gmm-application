"""Language: Bengali by default, English if the user picks it (remembered in a cookie).
Ignores the phone's Accept-Language so farmers always start in Bengali. Admin stays English."""
from django.conf import settings
from django.utils import translation


class ShopLanguageMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.lstrip("/").startswith(settings.ADMIN_URL):
            lang = "en"
        else:
            lang = request.COOKIES.get(settings.LANGUAGE_COOKIE_NAME)
            if lang not in dict(settings.LANGUAGES):
                lang = settings.LANGUAGE_CODE
        translation.activate(lang)
        request.LANGUAGE_CODE = lang
        response = self.get_response(request)
        response.headers.setdefault("Content-Language", lang)
        return response
