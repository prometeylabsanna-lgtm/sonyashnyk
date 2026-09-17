"""Локалізація вітрини: cookie/моделі з fallback UK → RU."""

from __future__ import annotations

from django.utils.translation import get_language

LANG_COOKIE = "sonyashnyk_lang"
SUPPORTED = ("uk", "ru")


def normalize_lang(code: str | None) -> str:
    if not code:
        return "uk"
    code = str(code).lower().replace("_", "-")
    if code.startswith("ru"):
        return "ru"
    return "uk"


def current_lang() -> str:
    return normalize_lang(get_language())


def is_ru() -> bool:
    return current_lang() == "ru"


def pick(uk: str | None, ru: str | None) -> str:
    """Повертає RU якщо мова ru і є непорожній ru, інакше uk."""
    uk_val = "" if uk is None else str(uk)
    if is_ru():
        ru_val = "" if ru is None else str(ru).strip()
        if ru_val:
            return str(ru).strip() if ru is not None else ru_val
    return uk_val


def loc(obj, field: str) -> str:
    """Поле моделі з optional ``{field}_ru``."""
    base = getattr(obj, field, None)
    ru = getattr(obj, f"{field}_ru", None)
    return pick(base if base is not None else "", ru)


COUNTRY_LABELS_RU = {
    "Україна": "Украина",
    "Польща": "Польша",
    "Нідерланди": "Нидерланды",
}


def country_label(name: str) -> str:
    if not name:
        return ""
    if is_ru():
        return COUNTRY_LABELS_RU.get(name, name)
    return name
