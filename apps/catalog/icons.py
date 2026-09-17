"""Резолв URL іконок категорій.

Корені (рівень 0): static шапки / головної (або Category.image).
Підкатегорії та підпідкатегорії: тільки соняшник (або Category.image).
"""

from django.templatetags.static import static

# Головна — акварельні плитки коренів
HOME_CATEGORY_ICONS = {
    "nasinnia": "img/home/categories/nasinnya.webp",
    "dobriva-ta-stimuliatori-rostu": "img/home/categories/dobryva.webp",
    "zasobi-zakhistu-roslin": "img/home/categories/zakhyst.webp",
    "sadovii-instrument": "img/header/categories/instrument.webp",
    "poliv-ta-opriskuvachi": "img/home/categories/polyv.webp",
    "posadkovii-material": "img/home/categories/posadkovyi.webp",
    "gorshchiki": "img/home/categories/gorshchyky.webp",
    "grunti-ta-vse-dlia-posadki": "img/home/categories/grunty.webp",
}
HOME_CATEGORY_ICON_FALLBACK = "img/home/categories/nasinnya.webp"

# Шапка — зелені лінійні іконки коренів
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

# Єдина іконка для всіх під- і підпідкатегорій
SUBCAT_ICON_FALLBACK = "img/catalog/subcats/default.png"


def category_uploaded_image_url(category):
    image = getattr(category, "image", None) if category is not None else None
    if not image:
        return None
    try:
        return image.url
    except Exception:
        return None


def category_static_fallback_path(category, *, for_nav=False):
    if category is None:
        return HOME_CATEGORY_ICON_FALLBACK
    parent_id = getattr(category, "parent_id", None)
    if parent_id is None:
        slug = getattr(category, "slug", "") or ""
        mapping = NAV_CATEGORY_ICONS if for_nav else HOME_CATEGORY_ICONS
        return mapping.get(slug, HOME_CATEGORY_ICON_FALLBACK)
    return SUBCAT_ICON_FALLBACK


def category_icon_url(category, *, for_nav=False):
    uploaded = category_uploaded_image_url(category)
    if uploaded:
        return uploaded
    return static(category_static_fallback_path(category, for_nav=for_nav))


def category_icon_is_custom(category):
    return bool(category_uploaded_image_url(category))


def category_icon_caption(category, *, for_nav=False):
    if category_icon_is_custom(category):
        return "Завантажена іконка"
    if category is None or getattr(category, "parent_id", None) is None:
        return "Іконка меню / головної (static)"
    return "Соняшник (для всіх підкатегорій)"


def attach_category_icons(categories, *, for_nav=False):
    for cat in categories:
        cat.icon_url = category_icon_url(cat, for_nav=for_nav)
    return categories
