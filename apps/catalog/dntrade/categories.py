"""Мапінг категорій DNTrade → Category сайту."""

from __future__ import annotations

import re
import unicodedata

from apps.catalog.models import Category

IMPORT_CATEGORY_NAME = "Імпорт"
IMPORT_CATEGORY_SLUG = "import"

# Відомі розбіжності назв DNTrade ↔ дерево сайту
_ALIASES: dict[str, str] = {
    "редис та редька": "редис, редька",
    "салати, зелень та пряні трави": "салати, зелень, пряні трави",
    "гарбузи, кавуни, дині": "гарбузи, кавуни, дині",
    "вагове насіння": "вагове насіння",
    "газон насіння": "газонні трави",
    "квіти насіння": "насіння квітів",
    "насіння квітів": "насіння квітів",
    "послуги": "імпорт",
}


def normalize_category_key(value: str | None) -> str:
    text = unicodedata.normalize("NFKC", (value or "").strip().lower())
    text = text.replace("ё", "е")
    text = text.replace(" та ", ", ")
    text = re.sub(r"[«»\"'`]+", "", text)
    text = re.sub(r"[^\w\s,.-]+", " ", text, flags=re.UNICODE)
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\s*,\s*", ", ", text)
    return text


class CategoryResolver:
    def __init__(self):
        self._by_key: dict[str, Category] = {}
        self._import_category: Category | None = None
        self._rebuild_index()

    def _rebuild_index(self) -> None:
        self._by_key.clear()
        for cat in Category.objects.all().only("id", "name", "erp_name", "slug", "parent_id"):
            for raw in (cat.name, cat.erp_name, cat.slug.replace("-", " ")):
                key = normalize_category_key(raw)
                if key and key not in self._by_key:
                    self._by_key[key] = cat
            alias_target = _ALIASES.get(normalize_category_key(cat.name))
            if alias_target and alias_target not in self._by_key:
                self._by_key[alias_target] = cat

    def ensure_import_category(self) -> Category:
        if self._import_category is not None:
            return self._import_category
        cat = Category.objects.filter(slug=IMPORT_CATEGORY_SLUG).first()
        if cat is None:
            cat = Category.objects.filter(name=IMPORT_CATEGORY_NAME, parent__isnull=True).first()
        if cat is None:
            cat = Category(
                name=IMPORT_CATEGORY_NAME,
                slug=IMPORT_CATEGORY_SLUG,
                erp_name=IMPORT_CATEGORY_NAME,
                is_active=True,
                order=9999,
            )
            cat.save()
        self._import_category = cat
        self._by_key[normalize_category_key(IMPORT_CATEGORY_NAME)] = cat
        self._by_key[normalize_category_key(IMPORT_CATEGORY_SLUG)] = cat
        return cat

    def resolve(self, dntrade_category: dict | None) -> Category:
        title = ""
        if isinstance(dntrade_category, dict):
            title = (dntrade_category.get("title") or "").strip()
        if not title:
            return self.ensure_import_category()

        key = normalize_category_key(title)
        aliased = _ALIASES.get(key, key)
        found = self._by_key.get(aliased) or self._by_key.get(key)
        if found is not None:
            if title and not (found.erp_name or "").strip():
                found.erp_name = title[:160]
                found.save(update_fields=["erp_name"])
            return found
        return self.ensure_import_category()
