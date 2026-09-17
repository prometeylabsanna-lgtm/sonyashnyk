from django.core.cache import cache

from apps.core.db_safe import database_reachable

from .category_tree import HOME_ROOT_SLUGS
from .icons import NAV_SALE_ICON, category_icon_is_custom, category_icon_url
from .models import Category


def _attach_nav_icon(cat):
    """Пріоритет: Category.image → статичний fallback за slug."""
    cat.nav_icon_url = category_icon_url(cat, for_nav=True)
    cat.nav_icon_custom = category_icon_is_custom(cat)


def nav_categories(request):
    """Кореневі категорії 1 рівня (як на головній) + підкатегорії для шапки/футера."""
    if not database_reachable():
        return {
            "nav_categories": [],
            "nav_sale_icon": NAV_SALE_ICON,
        }
    categories = cache.get("nav_categories")
    if categories is None:
        cats_by_slug = {
            c.slug: c
            for c in Category.objects.filter(
                slug__in=HOME_ROOT_SLUGS, parent__isnull=True, is_active=True
            ).prefetch_related("children")
        }
        categories = [cats_by_slug[s] for s in HOME_ROOT_SLUGS if s in cats_by_slug]
        cache.set("nav_categories", categories, 300)
    for cat in categories:
        _attach_nav_icon(cat)
    return {
        "nav_categories": categories,
        "nav_sale_icon": NAV_SALE_ICON,
    }
