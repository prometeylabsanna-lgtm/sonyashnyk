"""Перевірка доступності БД (для тест-деплою без Postgres / ефемерного SQLite)."""

from django.db import connection
from django.db.utils import InterfaceError, OperationalError, ProgrammingError

# False після першого фейлу в процесі (Vercel cold start)
_db_reachable = None

# Мінімальна таблиця для головної — якщо її немає, міграції не пройшли
_REQUIRED_TABLE = "core_review"


def database_reachable() -> bool:
    global _db_reachable
    if _db_reachable is not None:
        return _db_reachable
    try:
        connection.ensure_connection()
        with connection.cursor() as cursor:
            tables = set(connection.introspection.table_names(cursor))
            if _REQUIRED_TABLE not in tables:
                raise OperationalError(f"missing table {_REQUIRED_TABLE}")
        _db_reachable = True
    except (OperationalError, InterfaceError, ProgrammingError):
        _db_reachable = False
    return _db_reachable


def reset_database_reachable_cache() -> None:
    """Скинути кеш після migrate на cold start."""
    global _db_reachable
    _db_reachable = None
