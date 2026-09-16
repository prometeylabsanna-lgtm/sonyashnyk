from django.core.cache import cache
from django.templatetags.static import static

from apps.core.db_safe import database_reachable

from .category_tree import HOME_ROOT_SLUGS
from .models import Category

# Іконки desktop main-nav (WebP з прозорим фоном) — fallback, якщо немає Category.image
NAV_CATEGORY_ICONS = {
    "nasinnia": "img/header/categories/nasinnia.webp",
    "dobriva-ta-stimuliatori-rostu": "img/header/categories/dobryva.webp",
    "zasobi-zakhistu-roslin": "img/header/categories/zakhyst.webp",
    "sadovii-instrument": "img/header/categories/instrument.webp",
    "poliv-ta-opriskuvachi": "img/header/categories/polyv.webp",
    "posadkovii-material": "img/header/categories/posadkovyi.webp",
    "gorshchiki": "img/header/categories/gorshchyky.webp",
    "grunti-ta-vse-dlia-posadki": "img/header/categories/grunty.webp",
}
NAV_SALE_ICON = "img/header/categories/aktsiyi.webp"


def _attach_nav_icon(cat):
    """Пріоритет: Category.image → статичний fallback за slug."""
    if cat.image:
        try:
            cat.nav_icon_url = cat.image.url
            cat.nav_icon_custom = True
            return
        except Exception:
            pass
    path = NAV_CATEGORY_ICONS.get(cat.slug)
    cat.nav_icon_url = static(path) if path else None
    cat.nav_icon_custom = False


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
