from pathlib import Path

import environ
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY", default="insecure-dev-key-change-me")
DEBUG = env.bool("DEBUG", default=False)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])
# Use a non-obvious path in production, e.g. ADMIN_URL=gmm-staff-9f3k/
ADMIN_URL = env("ADMIN_URL", default="admin/")

INSTALLED_APPS = [
    "unfold",
    "unfold.contrib.filters",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "apps.core",
    "apps.accounts",
    "apps.catalog",
    "apps.orders",
    "apps.payments",
    "apps.invoicing",
    "apps.shop",
    "apps.advisory",
    "apps.thoughts",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "apps.shop.middleware.ShopLanguageMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.template.context_processors.i18n",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.shop.cart.cart_context",
            ],
        },
    },
]

# SQLite for quick local start; use PostgreSQL in staging/production:
# DATABASE_URL=postgres://user:pass@localhost:5432/gmm
DATABASES = {
    "default": env.db("DATABASE_URL", default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}")
}

AUTH_USER_MODEL = "accounts.User"
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
]
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "bn"  # default language; users can switch to English (remembered in a cookie)
LANGUAGE_COOKIE_AGE = 60 * 60 * 24 * 365
LANGUAGES = [("en", "English"), ("bn", "বাংলা")]
LOCALE_PATHS = [BASE_DIR / "locale"]
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}
# Payment proofs and invoices should move to private object storage in production
# (django-storages with signed URLs).

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Business rules (can also be overridden in the SiteSetting admin)
MAX_ADDRESSES_PER_USER = 10

LOGIN_URL = "shop:login"
LOGIN_REDIRECT_URL = "shop:products"
LOGOUT_REDIRECT_URL = "shop:products"

UNFOLD = {
    "SITE_TITLE": "GMM Distributors",
    "SITE_HEADER": "GMM Distributors",
    "SITE_SUBHEADER": "Orders & Catalogue",
    "SITE_SYMBOL": "agriculture",
    "SHOW_HISTORY": True,
    "COLORS": {
        "primary": {
            "50": "oklch(98.2% .018 155.826)",
            "100": "oklch(96.2% .044 156.743)",
            "200": "oklch(92.5% .084 155.995)",
            "300": "oklch(87.1% .15 154.449)",
            "400": "oklch(79.2% .209 151.711)",
            "500": "oklch(72.3% .219 149.579)",
            "600": "oklch(62.7% .194 149.214)",
            "700": "oklch(52.7% .154 150.069)",
            "800": "oklch(44.8% .119 151.328)",
            "900": "oklch(39.3% .095 152.535)",
            "950": "oklch(26.6% .065 152.934)",
        },
    },
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": False,
        "navigation": [
            {
                "title": _("Sales"),
                "separator": True,
                "items": [
                    {"title": _("Orders"), "icon": "receipt_long", "link": reverse_lazy("admin:orders_order_changelist")},
                    {"title": _("Payments"), "icon": "payments", "link": reverse_lazy("admin:payments_payment_changelist")},
                    {"title": _("Invoices"), "icon": "description", "link": reverse_lazy("admin:invoicing_invoice_changelist")},
                ],
            },
            {
                "title": _("Catalogue"),
                "separator": True,
                "items": [
                    {"title": _("Products"), "icon": "inventory_2", "link": reverse_lazy("admin:catalog_product_changelist")},
                    {"title": _("Categories"), "icon": "category", "link": reverse_lazy("admin:catalog_category_changelist")},
                ],
            },
            {
                "title": _("Customers & Delivery"),
                "separator": True,
                "items": [
                    {"title": _("Customers"), "icon": "group", "link": reverse_lazy("admin:accounts_user_changelist")},
                    {"title": _("Addresses"), "icon": "home_pin", "link": reverse_lazy("admin:accounts_address_changelist")},
                    {"title": _("Serviceable PIN codes"), "icon": "local_shipping", "link": reverse_lazy("admin:orders_serviceablepin_changelist")},
                ],
            },
            {
                "title": _("Settings"),
                "separator": True,
                "items": [
                    {"title": _("Business settings"), "icon": "settings", "link": reverse_lazy("admin:core_sitesetting_changelist")},
                ],
            },
        ],
    },
}
