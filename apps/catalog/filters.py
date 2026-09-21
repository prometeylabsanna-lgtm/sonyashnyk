"""Допоміжні функції фільтрації та сортування каталогу (§3.3 карти сайту)."""

from django.db.models import Prefetch, Q

from .category_tree import category_allows_catalog_filter
from .filter_models import CatalogFilter, CatalogFilterValue

SORT_OPTIONS = {
    "popularity": "-is_hit",
    "price_asc": "base_price",
    "price_desc": "-base_price",
    "new": "-created_at",
}


def active_catalog_filters():
    return (
        CatalogFilter.objects.filter(is_active=True)
        .exclude(slug__in=("power", "potuzhnist", "moshchnost"))
        .exclude(name__in=("Потужність", "Мощность"))
        .exclude(name_ru__in=("Потужність", "Мощность"))
        .prefetch_related(
            Prefetch(
                "values",
                queryset=CatalogFilterValue.objects.filter(is_active=True).order_by(
                    "order", "value"
                ),
            ),
            "category_bindings",
        )
        .order_by("order", "name")
    )


def filter_products(request, products):
    get = request.GET

    price_min = get.get("price_min")
    price_max = get.get("price_max")
    if price_min:
        products = products.filter(base_price__gte=price_min)
    if price_max:
        products = products.filter(base_price__lte=price_max)

    if get.get("in_stock"):
        products = products.filter(variants__stock_qty__gt=0).distinct()

    if get.get("own_production"):
        products = products.filter(is_own_production=True)

    if get.get("hit"):
        products = products.filter(is_hit=True)

    if get.get("new"):
        products = products.filter(is_new=True)

    for cf in active_catalog_filters():
        selected = get.getlist(cf.slug)
        if not selected:
            continue
        if cf.slug == "volume":
            products = products.filter(
                Q(filter_attrs__catalog_filter=cf, filter_attrs__value__in=selected)
                | Q(variants__label__in=selected),
            ).distinct()
            continue
        products = products.filter(
            filter_attrs__catalog_filter=cf,
            filter_attrs__value__in=selected,
        ).distinct()

    return products


def apply_sorting(request, products):
    sort_key = request.GET.get("sort", "popularity")
    order_field = SORT_OPTIONS.get(sort_key, SORT_OPTIONS["popularity"])
    return products.order_by(order_field, "-id")


def _ordered_values_for_filter(cf, products):
    dict_ordered = [v.value for v in cf.values.all()]
    product_vals = set(
        products.filter(filter_attrs__catalog_filter=cf)
        .exclude(filter_attrs__value="")
        .values_list("filter_attrs__value", flat=True)
        .distinct()
    )
    if cf.slug == "volume":
        product_vals.update(
            products.exclude(variants__label="")
            .values_list("variants__label", flat=True)
            .distinct()
        )
    result = [v for v in dict_ordered if v in product_vals]
    orphans = sorted(v for v in product_vals if v not in set(dict_ordered))
    return result + orphans


def build_filter_context(request, products, category=None):
    """Контекст панелі фільтрів: системні + динамічні групи."""
    get = request.GET
    dynamic = []
    active_count = 0

    for key in ("price_min", "price_max", "in_stock", "own_production", "hit", "new"):
        if get.get(key):
            active_count += 1

    for cf in active_catalog_filters():
        if not category_allows_catalog_filter(category, cf):
            continue
        values = _ordered_values_for_filter(cf, products)
        if not values:
            continue
        selected = get.getlist(cf.slug)
        active_count += len(selected)
        dynamic.append({
            "slug": cf.slug,
            "name": cf.display_name(),
            "use_country_labels": cf.use_country_labels,
            "values": values,
            "selected": selected,
        })

    return {
        "dynamic_filters": dynamic,
        "active_filters_count": active_count,
        # Сумісність зі старими шаблонами (якщо ще десь очікують)
        "available_brands": [],
        "available_countries": [],
        "available_volumes": [],
        "available_powers": [],
        "selected_brands": [],
        "selected_countries": [],
        "selected_volumes": [],
        "selected_powers": [],
        "show_brand_filter": False,
        "show_country_filter": False,
        "show_volume_filter": False,
        "show_power_filter": False,
    }
