from django.core.cache import cache

from .models import Category

# Іконки desktop main-nav (WebP з прозорим фоном)
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


def nav_categories(request):
    """Верхньорівневі активні категорії з підкатегоріями для навігації в шапці/футері."""
    categories = cache.get("nav_categories")
    if categories is None:
        categories = list(
            Category.objects.filter(parent__isnull=True, is_active=True)
            .prefetch_related("children")
            .order_by("order", "name")
        )
        cache.set("nav_categories", categories, 300)
    for cat in categories:
        cat.nav_icon = NAV_CATEGORY_ICONS.get(cat.slug)
    return {
        "nav_categories": categories,
        "nav_sale_icon": NAV_SALE_ICON,
    }
