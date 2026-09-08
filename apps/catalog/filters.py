"""Допоміжні функції фільтрації та сортування каталогу (§3.3 карти сайту)."""

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

    return products


def apply_sorting(request, products):
    sort_key = request.GET.get("sort", "popularity")
    order_field = SORT_OPTIONS.get(sort_key, SORT_OPTIONS["popularity"])
    return products.order_by(order_field, "-id")


def build_filter_context(request, products):
    """Формує список доступних брендів/країн для чекбоксів фільтра."""
    brands = (
        products.exclude(brand="").order_by("brand").values_list("brand", flat=True).distinct()
    )
    countries = (
        products.exclude(country_of_origin="")
        .order_by("country_of_origin")
        .values_list("country_of_origin", flat=True)
        .distinct()
    )
    active_filters = 0
    get = request.GET
    for key in ("price_min", "price_max", "in_stock", "own_production"):
        if get.get(key):
            active_filters += 1
    active_filters += len(get.getlist("brand")) + len(get.getlist("country"))

    return {
        "available_brands": list(brands),
        "available_countries": list(countries),
        "selected_brands": get.getlist("brand"),
        "selected_countries": get.getlist("country"),
        "active_filters_count": active_filters,
    }
