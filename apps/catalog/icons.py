"""Резолв URL іконок категорій.

Корені:
  — шапка (for_nav): Category.image або static NAV
  — головна / каталог: SiteBlock CMS або static HOME (не Category.image)
Підкатегорії: Category.image або соняшник.
"""

from django.templatetags.static import static

# slug, CMS key, підпис в адмінці, static fallback головної
HOME_CATEGORY_TILES: tuple[tuple[str, str, str, str], ...] = (
    (
        "nasinnia",
        "categories_tile_nasinnia_image",
        "Насіння",
        "img/home/categories/nasinnya.webp",
    ),
    (
        "dobriva-ta-stimuliatori-rostu",
        "categories_tile_dobryva_image",
        "Добрива та стимулятори росту",
        "img/home/categories/dobryva.webp",
    ),
    (
        "zasobi-zakhistu-roslin",
        "categories_tile_zakhyst_image",
        "Засоби захисту рослин",
        "img/home/categories/zakhyst.webp",
    ),
    (
        "sadovii-instrument",
        "categories_tile_instrument_image",
        "Садовий інструмент",
        "img/home/categories/instrument.webp",
    ),
    (
        "poliv-ta-opriskuvachi",
        "categories_tile_polyv_image",
        "Полив та оприскувачі",
        "img/home/categories/polyv.webp",
    ),
    (
        "posadkovii-material",
        "categories_tile_posadkovyi_image",
        "Посадковий матеріал",
        "img/home/categories/posadkovyi.webp",
    ),
    (
        "gorshchiki",
        "categories_tile_gorshchyky_image",
        "Горщики",
        "img/home/categories/gorshchyky.webp",
    ),
    (
        "grunti-ta-vse-dlia-posadki",
        "categories_tile_grunty_image",
        "Ґрунти та все для посадки",
        "img/home/categories/grunty.webp",
    ),
)

HOME_CATEGORY_ICONS = {slug: path for slug, _key, _label, path in HOME_CATEGORY_TILES}
HOME_CATEGORY_TILE_BLOCK_KEY_BY_SLUG = {
    slug: key for slug, key, _label, _path in HOME_CATEGORY_TILES
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
SUBCAT_ICON_FALLBACK = "img/catalog/subcats/default.webp"


def category_uploaded_image_url(category):
    image = getattr(category, "image", None) if category is not None else None
    if not image:
        return None
    try:
        return image.url
    except Exception:
        return None


def home_category_tile_block_url(slug: str) -> str | None:
    """URL завантаженого фото плитки з CMS SiteBlock (home)."""
    key = HOME_CATEGORY_TILE_BLOCK_KEY_BY_SLUG.get(slug or "")
    if not key:
        return None

    block = None
    try:
        from django.core.cache import cache

        from apps.core.admin_site_content import SITE_BLOCKS_CACHE_KEY

        cached = cache.get(SITE_BLOCKS_CACHE_KEY)
        if cached is not None:
            block = cached.get(f"home.{key}")
    except Exception:
        block = None

    if block is None:
        try:
            from apps.core.models import SiteBlock

            block = SiteBlock.objects.filter(page="home", key=key).first()
        except Exception:
            return None

    image = getattr(block, "image", None) if block is not None else None
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
    parent_id = getattr(category, "parent_id", None) if category is not None else None

    if for_nav:
        uploaded = category_uploaded_image_url(category)
        if uploaded:
            return uploaded
        return static(category_static_fallback_path(category, for_nav=True))

    # Плитки головної / кореня каталогу — CMS, не іконка шапки
    if parent_id is None and category is not None:
        slug = getattr(category, "slug", "") or ""
        cms_url = home_category_tile_block_url(slug)
        if cms_url:
            return cms_url
        return static(category_static_fallback_path(category, for_nav=False))

    uploaded = category_uploaded_image_url(category)
    if uploaded:
        return uploaded
    return static(category_static_fallback_path(category, for_nav=False))


def category_icon_is_custom(category, *, for_nav=False):
    parent_id = getattr(category, "parent_id", None) if category is not None else None
    if for_nav or parent_id is not None:
        return bool(category_uploaded_image_url(category))
    slug = getattr(category, "slug", "") or ""
    return bool(home_category_tile_block_url(slug))


def category_icon_caption(category, *, for_nav=False):
    parent_id = getattr(category, "parent_id", None) if category is not None else None
    if for_nav:
        if category_uploaded_image_url(category):
            return "Завантажена іконка верхньої панелі"
        return "Іконка верхньої панелі (static)"
    if parent_id is None:
        slug = getattr(category, "slug", "") or ""
        if home_category_tile_block_url(slug):
            return "Фото плитки з CMS «Головна — Категорії»"
        return "Плитка головної (static)"
    if category_uploaded_image_url(category):
        return "Завантажена іконка"
    return "Соняшник (для всіх підкатегорій)"


def attach_category_icons(categories, *, for_nav=False):
    for cat in categories:
        cat.icon_url = category_icon_url(cat, for_nav=for_nav)
    return categories
