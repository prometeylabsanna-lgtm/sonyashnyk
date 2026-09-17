"""Proxy-моделі рівнів категорій для розділеної адмінки «Меню»."""

from .models import Category


class RootCategory(Category):
    """1 рівень — головні категорії (шапка / головна)."""

    class Meta:
        proxy = True
        verbose_name = "1 рівень категорій"
        verbose_name_plural = "1 рівень категорій"


class SubCategory(Category):
    """2 рівень — підкатегорії."""

    class Meta:
        proxy = True
        verbose_name = "2 рівень категорій"
        verbose_name_plural = "2 рівень категорій"


class SubSubCategory(Category):
    """3 рівень — підпідкатегорії."""

    class Meta:
        proxy = True
        verbose_name = "3 рівень категорій"
        verbose_name_plural = "3 рівень категорій"
