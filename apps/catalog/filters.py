"""Допоміжні функції фільтрації та сортування каталогу (§3.3 карти сайту)."""

from .category_tree import category_allows_filter
from .filter_models import FILTER_PRODUCT_FIELDS, FilterOption, FilterType

SORT_OPTIONS = {
    "popularity": "-is_hit",
    "price_asc": "base_price",
    "price_desc": "-base_price",
    "new": "-created_at",
}


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

    brands = get.getlist("brand")
    if brands:
        products = products.filter(brand__in=brands)

    countries = get.getlist("country")
    if countries:
        products = products.filter(country_of_origin__in=countries)

    volumes = get.getlist("volume")
    if volumes:
        products = products.filter(pack_volume__in=volumes)

    powers = get.getlist("power")
    if powers:
        products = products.filter(power__in=powers)

    return products


def apply_sorting(request, products):
    sort_key = request.GET.get("sort", "popularity")
    order_field = SORT_OPTIONS.get(sort_key, SORT_OPTIONS["popularity"])
    return products.order_by(order_field, "-id")


def _ordered_filter_values(filter_type, products):
    """Значення з довідника (порядок) ∩ товари + «сирі» значення поза довідником."""
    field = FILTER_PRODUCT_FIELDS[filter_type]
    dict_ordered = list(
        FilterOption.objects.filter(filter_type=filter_type, is_active=True)
        .order_by("order", "value")
        .values_list("value", flat=True)
    )
    product_vals = set(
        products.exclude(**{field: ""})
        .order_by(field)
        .values_list(field, flat=True)
        .distinct()
    )
    result = [v for v in dict_ordered if v in product_vals]
    orphans = sorted(v for v in product_vals if v not in set(dict_ordered))
    return result + orphans


def build_filter_context(request, products, category=None):
    """Формує список доступних брендів/країн/обʼємів/потужностей для чекбоксів."""
    show_brand = category_allows_filter(category, FilterType.BRAND)
    show_country = category_allows_filter(category, FilterType.COUNTRY)
    show_volume_filter = category_allows_filter(category, FilterType.VOLUME)
    show_power_filter = category_allows_filter(category, FilterType.POWER)

    brands = _ordered_filter_values(FilterType.BRAND, products) if show_brand else []
    countries = (
        _ordered_filter_values(FilterType.COUNTRY, products) if show_country else []
    )
    volumes = (
        _ordered_filter_values(FilterType.VOLUME, products) if show_volume_filter else []
    )
    powers = (
        _ordered_filter_values(FilterType.POWER, products) if show_power_filter else []
    )

    active_filters = 0
    get = request.GET
    for key in ("price_min", "price_max", "in_stock", "own_production"):
        if get.get(key):
            active_filters += 1
    active_filters += len(get.getlist("brand")) + len(get.getlist("country"))
    active_filters += len(get.getlist("volume")) + len(get.getlist("power"))

    return {
        "available_brands": brands,
        "available_countries": countries,
        "available_volumes": volumes,
        "available_powers": powers,
        "selected_brands": get.getlist("brand"),
        "selected_countries": get.getlist("country"),
        "selected_volumes": get.getlist("volume"),
        "selected_powers": get.getlist("power"),
        "show_brand_filter": show_brand,
        "show_country_filter": show_country,
        "show_volume_filter": show_volume_filter,
        "show_power_filter": show_power_filter,
        "active_filters_count": active_filters,
    }
