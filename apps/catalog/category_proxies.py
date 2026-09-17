"""Proxy-моделі рівнів категорій для розділеної адмінки «Меню»."""

from .models import Category


class RootCategory(Category):
    """Рівень 0 — головні категорії (шапка / головна)."""

    class Meta:
        proxy = True
        verbose_name = "Головна категорія"
        verbose_name_plural = "Головні категорії"


class SubCategory(Category):
    """Рівень 1 — підкатегорії."""

    class Meta:
        proxy = True
        verbose_name = "Підкатегорія"
        verbose_name_plural = "Підкатегорії"


class SubSubCategory(Category):
    """Рівень 2 — підпідкатегорії (уточнення)."""

    class Meta:
        proxy = True
        verbose_name = "Підпідкатегорія"
        verbose_name_plural = "Підпідкатегорії"
