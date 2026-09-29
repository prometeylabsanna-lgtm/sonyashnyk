"""Безпечний пошук каталогу: санітизація, літеральний матч, remap розкладки UK↔EN."""

from __future__ import annotations

import re

from django.db.models import Q

SEARCH_MAX_LEN = 80

# Символи на тих самих клавішах (українська ↔ англійська QWERTY).
_EN_TO_UA = str.maketrans(
    "qwertyuiop[]asdfghjkl;'zxcvbnm,./"
    "QWERTYUIOP{}ASDFGHJKL:\"ZXCVBNM<>?",
    "йцукенгшщзхїфівапролджєячсмитьбю."
    "ЙЦУКЕНГШЩЗХЇФІВАПРОЛДЖЄЯЧСМИТЬБЮ,",
)
_UA_TO_EN = str.maketrans(
    "йцукенгшщзхїфівапролджєячсмитьбю."
    "ЙЦУКЕНГШЩЗХЇФІВАПРОЛДЖЄЯЧСМИТЬБЮ,",
    "qwertyuiop[]asdfghjkl;'zxcvbnm,./"
    "QWERTYUIOP{}ASDFGHJKL:\"ZXCVBNM<>?",
)

_CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")


def sanitize_query(raw: str | None) -> str:
    text = _CONTROL_RE.sub("", (raw or "")).strip()
    if len(text) > SEARCH_MAX_LEN:
        text = text[:SEARCH_MAX_LEN]
    return text


def layout_variants(query: str) -> list[str]:
    """Оригінал + remap UK→EN і EN→UA (унікальні непусті)."""
    variants = [query]
    for table in (_EN_TO_UA, _UA_TO_EN):
        remapped = query.translate(table)
        if remapped and remapped != query and remapped not in variants:
            variants.append(remapped)
    return variants


def _term_q(term: str) -> Q:
    # iregex + re.escape: %, _, ', <script> — літерали, не SQL/LIKE-wildcard.
    pattern = re.escape(term)
    return (
        Q(name__iregex=pattern)
        | Q(name_ru__iregex=pattern)
        | Q(sku__iregex=pattern)
        | Q(short_description__iregex=pattern)
        | Q(short_description_ru__iregex=pattern)
        | Q(brand__iregex=pattern)
    )


def search_products(queryset, raw_query: str):
    """Фільтрує queryset. Повертає (qs, display_query). Порожній запит → none."""
    query = sanitize_query(raw_query)
    if not query:
        return queryset.none(), ""

    combined = Q()
    for term in layout_variants(query):
        combined |= _term_q(term)
    return queryset.filter(combined), query
