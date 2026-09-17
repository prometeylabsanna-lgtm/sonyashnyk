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
SEED_PROFILE = "half-with-images-v3-dynamic-filters"

VERCEL_SUPERUSER_USERNAME = "admin"
VERCEL_SUPERUSER_EMAIL = "admin@sonyashnyk.com"
VERCEL_SUPERUSER_PASSWORD = "admin"


def _ensure_vercel_superuser() -> None:
    """Один і той самий password hash на всіх cold start → сесія не злітає між інстансами."""
    from django.contrib.auth import get_user_model
    from django.contrib.auth.hashers import make_password

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


def _schema_ready() -> bool:
    from django.db import connection

    with connection.cursor() as cursor:
        tables = set(connection.introspection.table_names(cursor))
    return "core_review" in tables and "django_migrations" in tables


def _reset_sqlite() -> None:
    db_path = Path(settings.DATABASES["default"]["NAME"])
    if db_path.exists():
        db_path.unlink()
    media_root = Path(settings.MEDIA_ROOT)
    if media_root.exists():
        shutil.rmtree(media_root, ignore_errors=True)


if getattr(settings, "IS_VERCEL", False):
    try:
        from django.core.management import call_command
        from django.db import connection

        from apps.catalog.models import Category, ProductImage
        from apps.core.db_safe import reset_database_reachable_cache

        profile_path = Path("/tmp/sonyashnyk_seed_profile")
        profile_ok = profile_path.exists() and profile_path.read_text() == SEED_PROFILE

        if not profile_ok:
            _reset_sqlite()

        call_command("migrate", interactive=False, run_syncdb=False)
        connection.close()
        reset_database_reachable_cache()

        if not _schema_ready():
            # Пошкоджена / порожня схема — повний reset і ще раз migrate
            _reset_sqlite()
            call_command("migrate", interactive=False, run_syncdb=False)
            connection.close()
            reset_database_reachable_cache()

        if not _schema_ready():
            raise RuntimeError("migrate finished but core_review is missing")

        _ensure_vercel_superuser()

        need_seed = (
            not profile_ok
            or not Category.objects.exists()
            or not ProductImage.objects.exists()
        )
        if need_seed:
            call_command("seed_demo")
            profile_path.write_text(SEED_PROFILE)
            _ensure_vercel_superuser()
    except Exception as exc:
        # Не валимо cold start — home віддасть порожній контент через database_reachable()
        print(f"[vercel] bootstrap failed: {exc}")
        try:
            from apps.core.db_safe import reset_database_reachable_cache

            reset_database_reachable_cache()
        except Exception:
            pass
