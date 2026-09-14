"""Перевірка доступності БД (для тест-деплою без Postgres)."""

from django.db import connection
from django.db.utils import InterfaceError, OperationalError

# False після першого фейлу в процесі (Vercel cold start)
_db_reachable = None


def database_reachable() -> bool:
    global _db_reachable
    if _db_reachable is not None:
        return _db_reachable
    try:
        connection.ensure_connection()
        _db_reachable = True
    except (OperationalError, InterfaceError):
        _db_reachable = False
    return _db_reachable
