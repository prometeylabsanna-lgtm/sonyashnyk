"""Перевірка доступності БД (для тест-деплою без Postgres / ефемерного SQLite)."""

from django.db import connection
from django.db.utils import InterfaceError, OperationalError, ProgrammingError

# False після першого фейлу в процесі (Vercel cold start)
_db_reachable = None

# Таблиці, без яких головна / каталог не можуть працювати з БД
_REQUIRED_TABLES = frozenset({
    "django_migrations",
    "core_review",
    "core_heroslide",
    "catalog_category",
    "catalog_product",
})


def database_reachable() -> bool:
    global _db_reachable
    if _db_reachable is not None:
        return _db_reachable
    try:
        connection.ensure_connection()
        with connection.cursor() as cursor:
            tables = set(connection.introspection.table_names(cursor))
        missing = _REQUIRED_TABLES - tables
        if missing:
            raise OperationalError(f"missing tables: {sorted(missing)}")
        _db_reachable = True
    except (OperationalError, InterfaceError, ProgrammingError):
        _db_reachable = False
    return _db_reachable


def reset_database_reachable_cache() -> None:
    """Скинути кеш після migrate на cold start."""
    global _db_reachable
    _db_reachable = None
