"""
Vercel Python entrypoint (WSGI → Django).

На Vercel: SQLite у /tmp → migrate + seed_demo (якщо БД порожня).
"""

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

from django.core.wsgi import get_wsgi_application

app = get_wsgi_application()

from django.conf import settings

if getattr(settings, "IS_VERCEL", False):
    try:
        from django.core.management import call_command

        from apps.catalog.models import Category

        call_command("migrate", interactive=False, run_syncdb=False)
        if not Category.objects.exists():
            call_command("seed_demo", "--skip-images")
    except Exception as exc:
        # Не валимо cold start — сторінки все одно відкриються
        print(f"[vercel] bootstrap failed: {exc}")
