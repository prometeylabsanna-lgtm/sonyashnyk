"""Допоміжні функції фільтрації та сортування каталогу (§3.3 карти сайту)."""

from .category_tree import category_allows_power_filter, category_allows_volume_filter

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


def build_filter_context(request, products, category=None):
    """Формує список доступних брендів/країн/обʼємів/потужностей для чекбоксів."""
    brands = (
        products.exclude(brand="").order_by("brand").values_list("brand", flat=True).distinct()
    )
    countries = (
        products.exclude(country_of_origin="")
        .order_by("country_of_origin")
        .values_list("country_of_origin", flat=True)
        .distinct()
    )

    show_volume_filter = category_allows_volume_filter(category)
    volumes = []
    if show_volume_filter:
        volumes = list(
            products.exclude(pack_volume="")
            .order_by("pack_volume")
            .values_list("pack_volume", flat=True)
            .distinct()
        )

    show_power_filter = category_allows_power_filter(category)
    powers = []
    if show_power_filter:
        powers = list(
            products.exclude(power="")
            .order_by("power")
            .values_list("power", flat=True)
            .distinct()
        )

    active_filters = 0
    get = request.GET
    for key in ("price_min", "price_max", "in_stock", "own_production"):
        if get.get(key):
            active_filters += 1
    active_filters += len(get.getlist("brand")) + len(get.getlist("country"))
    active_filters += len(get.getlist("volume")) + len(get.getlist("power"))

    return {
        "available_brands": list(brands),
        "available_countries": list(countries),
        "available_volumes": volumes,
        "available_powers": powers,
        "selected_brands": get.getlist("brand"),
        "selected_countries": get.getlist("country"),
        "selected_volumes": get.getlist("volume"),
        "selected_powers": get.getlist("power"),
        "show_volume_filter": show_volume_filter,
        "show_power_filter": show_power_filter,
        "active_filters_count": active_filters,
    }
