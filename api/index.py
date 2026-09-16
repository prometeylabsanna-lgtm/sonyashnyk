"""
Vercel Python entrypoint (WSGI → Django).

На Vercel: SQLite у /tmp → migrate + seed_demo (якщо БД порожня / застарів профіль)
+ тестовий суперюзер admin/admin (БД ефемерна).
"""

import os
import shutil
from pathlib import Path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

from django.core.wsgi import get_wsgi_application

app = get_wsgi_application()

from django.conf import settings

# Зміна рядка = повний re-seed на наступному cold start
SEED_PROFILE = "half-with-images-v1"

VERCEL_SUPERUSER_USERNAME = "admin"
VERCEL_SUPERUSER_EMAIL = "admin@sonyashnyk.com"
VERCEL_SUPERUSER_PASSWORD = "admin"


def _ensure_vercel_superuser() -> None:
    """Один і той самий password hash на всіх cold start → сесія не злітає між інстансами."""
    from django.contrib.auth import get_user_model
    from django.contrib.auth.hashers import make_password

    # Фіксований salt → стабільний session auth hash між serverless-інстансами
    password_hash = make_password(
        VERCEL_SUPERUSER_PASSWORD,
        salt="sonyashnyk-vercel-admin-v1",
    )
    User = get_user_model()
    User.objects.update_or_create(
        username=VERCEL_SUPERUSER_USERNAME,
        defaults={
            "email": VERCEL_SUPERUSER_EMAIL,
            "is_staff": True,
            "is_superuser": True,
            "password": password_hash,
        },
    )


if getattr(settings, "IS_VERCEL", False):
    try:
        from django.core.management import call_command

        from apps.catalog.models import Category, ProductImage

        db_path = Path(settings.DATABASES["default"]["NAME"])
        profile_path = Path("/tmp/sonyashnyk_seed_profile")
        profile_ok = profile_path.exists() and profile_path.read_text() == SEED_PROFILE

        if not profile_ok:
            if db_path.exists():
                db_path.unlink()
            media_root = Path(settings.MEDIA_ROOT)
            if media_root.exists():
                shutil.rmtree(media_root, ignore_errors=True)

        call_command("migrate", interactive=False, run_syncdb=False)
        _ensure_vercel_superuser()

        if not profile_ok or not Category.objects.exists() or not ProductImage.objects.exists():
            call_command("seed_demo")
            profile_path.write_text(SEED_PROFILE)
            _ensure_vercel_superuser()
    except Exception as exc:
        # Не валимо cold start — сторінки все одно відкриються
        print(f"[vercel] bootstrap failed: {exc}")
