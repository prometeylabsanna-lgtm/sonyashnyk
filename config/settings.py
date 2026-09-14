"""
Django settings for Соняшник (config project).
"""

from pathlib import Path

from decouple import Csv, config

BASE_DIR = Path(__file__).resolve().parent.parent

# --- Security -----------------------------------------------------------
SECRET_KEY = config(
    "DJANGO_SECRET_KEY",
    default="django-insecure-dev-key-change-me-in-production",
)
DEBUG = config("DJANGO_DEBUG", default=True, cast=bool)
# Vercel завжди виставляє VERCEL=1
IS_VERCEL = config("VERCEL", default=False, cast=bool)
ALLOWED_HOSTS = config(
    "DJANGO_ALLOWED_HOSTS",
    default="127.0.0.1,localhost,.vercel.app",
    cast=Csv(),
)
if IS_VERCEL and "*" not in ALLOWED_HOSTS and ".vercel.app" not in ALLOWED_HOSTS:
    ALLOWED_HOSTS = list(ALLOWED_HOSTS) + [".vercel.app"]

CSRF_TRUSTED_ORIGINS = config(
    "DJANGO_CSRF_TRUSTED_ORIGINS",
    default="https://*.vercel.app",
    cast=Csv(),
)

# --- Applications ---------------------------------------------------------
INSTALLED_APPS = [
    "unfold",
    "unfold.contrib.filters",
    "unfold.contrib.forms",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
    # local apps
    "apps.core",
    "apps.catalog",
    "apps.orders",
    "apps.leads",
    "apps.pages",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.core.context_processors.site_settings",
                "apps.catalog.context_processors.nav_categories",
                "apps.orders.context_processors.cart_summary",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# --- Database -------------------------------------------------------------
# Локально / DO — Postgres. Тест-Vercel — SQLite у /tmp (єдине writable місце).
if IS_VERCEL:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": "/tmp/sonyashnyk.sqlite3",
        }
    }
    SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": config("DB_NAME", default="sonyashnyk_db"),
            "USER": config("DB_USER", default="sonyashnyk"),
            "PASSWORD": config("DB_PASSWORD", default="sonyashnyk_dev_pass"),
            "HOST": config("DB_HOST", default="127.0.0.1"),
            "PORT": config("DB_PORT", default="5432"),
            "CONN_MAX_AGE": 0,
            "OPTIONS": {
                "connect_timeout": 3,
            },
        }
    }

# --- Passwords --------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --- Localization -------------------------------------------------------
LANGUAGE_CODE = "uk"
TIME_ZONE = "Europe/Kyiv"
USE_I18N = True
USE_TZ = True

# --- Static & media files -------------------------------------------------
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}
# На Vercel без collectstatic у CI — віддаємо static через finders
if IS_VERCEL:
    WHITENOISE_USE_FINDERS = True
    WHITENOISE_AUTOREFRESH = True

MEDIA_URL = "media/"
MEDIA_ROOT = Path("/tmp/sonyashnyk_media") if IS_VERCEL else (BASE_DIR / "media")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Site / business settings -------------------------------------------
SITE_NAME = "Соняшник"
SITE_PHONE = "+38 (067) 123-45-67"
SITE_PHONE_RAW = "+380671234567"
SITE_WORKING_HOURS = "Пн–Сб 9:00–18:00"
FREE_SHIPPING_THRESHOLD = 1500

# Платіж / логістика (ключі з .env; без ключів — mock / ручний fallback)
SITE_URL = config("SITE_URL", default="http://127.0.0.1:8000")
LIQPAY_PUBLIC_KEY = config("LIQPAY_PUBLIC_KEY", default="")
LIQPAY_PRIVATE_KEY = config("LIQPAY_PRIVATE_KEY", default="")
LIQPAY_SANDBOX = config("LIQPAY_SANDBOX", default=True, cast=bool)
NOVA_POSHTA_API_KEY = config("NOVA_POSHTA_API_KEY", default="")

CART_SESSION_KEY = "cart"
PROMO_SESSION_KEY = "cart_promo"

LOGIN_URL = "/admin/login/"

MESSAGE_STORAGE = "django.contrib.messages.storage.session.SessionStorage"

# --- Unfold admin (акцент #E4DA69) ----------------------------------------
def _content_sidebar_items():
    from apps.core.site_content_registry import build_content_sidebar_items

    return build_content_sidebar_items()


UNFOLD = {
    "SITE_TITLE": "Соняшник Admin",
    "SITE_HEADER": "Соняшник — Адмінпанель",
    "SITE_SYMBOL": "spa",
    "COLORS": {
        "primary": {
            "50": "250 247 220",
            "100": "246 241 190",
            "200": "240 232 150",
            "300": "234 225 120",
            "400": "230 221 100",
            "500": "228 218 105",
            "600": "200 190 70",
            "700": "160 150 50",
            "800": "120 112 40",
            "900": "80 74 28",
            "950": "45 42 16",
        },
    },
    "SIDEBAR": {
        "show_search": True,
        "command_search": True,
        "show_all_applications": False,
        "navigation": [
            {
                "title": "Налаштування",
                "items": [
                    {
                        "title": "Налаштування сайту",
                        "icon": "settings",
                        "link": "/admin/core/sitesettings/",
                    },
                ],
            },
            {
                "title": "Контент сторінок",
                "separator": True,
                "items": _content_sidebar_items(),
            },
            {
                "title": "Каталог",
                "separator": True,
                "items": [
                    {"title": "Категорії", "icon": "category", "link": "/admin/catalog/category/"},
                    {"title": "Товари", "icon": "inventory_2", "link": "/admin/catalog/product/"},
                ],
            },
            {
                "title": "Продажі",
                "separator": True,
                "items": [
                    {"title": "Замовлення", "icon": "shopping_cart", "link": "/admin/orders/order/"},
                    {"title": "Промокоди", "icon": "local_offer", "link": "/admin/orders/promocode/"},
                ],
            },
            {
                "title": "Ліди",
                "separator": True,
                "items": [
                    {"title": "Заявки", "icon": "support_agent", "link": "/admin/leads/lead/"},
                ],
            },
            {
                "title": "Контент",
                "separator": True,
                "items": [
                    {"title": "Переваги", "icon": "loyalty", "link": "/admin/core/highlightpoint/"},
                    {"title": "Відгуки", "icon": "rate_review", "link": "/admin/core/review/"},
                    {"title": "Сертифікати", "icon": "workspace_premium", "link": "/admin/pages/certificate/"},
                ],
            },
        ],
    },
}
