"""
Vercel Python entrypoint (WSGI → Django).

На Vercel: SQLite у /tmp → migrate (+ seed_demo якщо потрібно).
Bootstrap не повинен валити cold start; головна вміє static-fallback.
"""

import os
import shutil
import sys
from pathlib import Path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

from django.core.wsgi import get_wsgi_application

app = get_wsgi_application()

from django.conf import settings

# Зміна рядка = повний re-seed на наступному cold start
SEED_PROFILE = "half-with-images-v4-schema-guard"

VERCEL_SUPERUSER_USERNAME = "admin"
VERCEL_SUPERUSER_EMAIL = "admin@sonyashnyk.com"
VERCEL_SUPERUSER_PASSWORD = "admin"

_REQUIRED_TABLES = frozenset({
    "django_migrations",
    "core_review",
    "core_heroslide",
    "catalog_category",
    "catalog_product",
})


def _ensure_vercel_superuser() -> None:
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


def _existing_tables() -> set[str]:
    from django.db import connection

    with connection.cursor() as cursor:
        return set(connection.introspection.table_names(cursor))


def _schema_ready() -> bool:
    return _REQUIRED_TABLES.issubset(_existing_tables())


def _reset_sqlite() -> None:
    from django.db import connection

    connection.close()
    db_path = Path(settings.DATABASES["default"]["NAME"])
    if db_path.exists():
        db_path.unlink()
    media_root = Path(settings.MEDIA_ROOT)
    if media_root.exists():
        shutil.rmtree(media_root, ignore_errors=True)


def _migrate() -> None:
    from django.core.management import call_command
    from django.db import connection

    from apps.core.db_safe import reset_database_reachable_cache

    call_command("migrate", interactive=False, verbosity=1)
    connection.close()
    reset_database_reachable_cache()


if getattr(settings, "IS_VERCEL", False):
    try:
        from apps.catalog.models import Category, ProductImage

        profile_path = Path("/tmp/sonyashnyk_seed_profile")
        profile_ok = (
            profile_path.exists() and profile_path.read_text().strip() == SEED_PROFILE
        )

        # Якщо профіль застарів або схеми немає — чистий SQLite + migrate
        if not profile_ok or not _schema_ready():
            print("[vercel] resetting sqlite + migrate", file=sys.stderr)
            _reset_sqlite()
            _migrate()
        elif not _schema_ready():
            _migrate()

        if not _schema_ready():
            print("[vercel] schema still incomplete, force reset", file=sys.stderr)
            _reset_sqlite()
            _migrate()

        if not _schema_ready():
            missing = sorted(_REQUIRED_TABLES - _existing_tables())
            raise RuntimeError(f"migrate ok but missing tables: {missing}")

        _ensure_vercel_superuser()

        need_seed = (
            not profile_ok
            or not Category.objects.exists()
            or not ProductImage.objects.exists()
        )
        if need_seed:
            from django.core.management import call_command

            print("[vercel] seed_demo starting", file=sys.stderr)
            call_command("seed_demo")
            profile_path.write_text(SEED_PROFILE)
            _ensure_vercel_superuser()
            print("[vercel] seed_demo done", file=sys.stderr)
        else:
            print("[vercel] bootstrap ok (cached profile)", file=sys.stderr)
    except Exception as exc:
        print(f"[vercel] bootstrap failed: {exc}", file=sys.stderr)
        try:
            from apps.core.db_safe import reset_database_reachable_cache

            reset_database_reachable_cache()
        except Exception:
            pass
