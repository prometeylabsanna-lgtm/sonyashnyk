"""Допоміжні функції фільтрації та сортування каталогу (§3.3 карти сайту)."""

from decimal import Decimal, InvalidOperation

from django.db.models import (
    DecimalField,
    F,
    IntegerField,
    OuterRef,
    Prefetch,
    Q,
    Subquery,
    Sum,
    Value,
)
from django.db.models.functions import Coalesce

from .category_tree import category_allows_catalog_filter
from .category_tree import pack_unit_kind
from .filter_models import CatalogFilter, CatalogFilterValue
from .models import ProductVariant

SORT_OPTIONS = {
    "popularity": ("-sold_qty", "-is_hit", "-id"),
    "price_asc": ("card_price", "-id"),
    "price_desc": ("-card_price", "-id"),
    "new": ("-created_at", "-id"),
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


def _parse_price(raw):
    if raw is None or raw == "":
        return None
    try:
        value = Decimal(str(raw).replace(",", ".").strip())
    except (InvalidOperation, TypeError, ValueError):
        return None
    if value < 0:
        return None
    return value


def annotate_card_price(products):
    """Ціна картки: дефолтний варіант у наявності → перший з залишком → base_price."""
    default_in_stock = (
        ProductVariant.objects.filter(
            product_id=OuterRef("pk"),
            is_default=True,
            stock_qty__gt=0,
        )
        .order_by("order", "id")
        .values("price")[:1]
    )
    any_in_stock = (
        ProductVariant.objects.filter(
            product_id=OuterRef("pk"),
            stock_qty__gt=0,
        )
        .order_by("order", "id")
        .values("price")[:1]
    )
    any_default = (
        ProductVariant.objects.filter(
            product_id=OuterRef("pk"),
            is_default=True,
        )
        .order_by("order", "id")
        .values("price")[:1]
    )
    any_first = (
        ProductVariant.objects.filter(product_id=OuterRef("pk"))
        .order_by("order", "id")
        .values("price")[:1]
    )
    return products.annotate(
        card_price=Coalesce(
            Subquery(default_in_stock, output_field=DecimalField(max_digits=10, decimal_places=2)),
            Subquery(any_in_stock, output_field=DecimalField(max_digits=10, decimal_places=2)),
            Subquery(any_default, output_field=DecimalField(max_digits=10, decimal_places=2)),
            Subquery(any_first, output_field=DecimalField(max_digits=10, decimal_places=2)),
            F("base_price"),
            output_field=DecimalField(max_digits=10, decimal_places=2),
        )
    )


def annotate_sold_qty(products):
    from apps.orders.models import OrderItem

    sold = (
        OrderItem.objects.filter(product_id=OuterRef("pk"))
        .values("product_id")
        .annotate(total=Sum("quantity"))
        .values("total")[:1]
    )
    return products.annotate(
        sold_qty=Coalesce(
            Subquery(sold, output_field=IntegerField()),
            Value(0),
            output_field=IntegerField(),
        )
    )


def filter_products(request, products, *, skip_slugs=None):
    get = request.GET
    skip = set(skip_slugs or ())

    price_min = _parse_price(get.get("price_min"))
    price_max = _parse_price(get.get("price_max"))
    if "price" not in skip:
        if price_min is not None:
            products = products.filter(card_price__gte=price_min)
        if price_max is not None:
            products = products.filter(card_price__lte=price_max)

    if get.get("in_stock") == "1" and "in_stock" not in skip:
        products = products.filter(variants__stock_qty__gt=0).distinct()

    if get.get("own_production") and "own_production" not in skip:
        products = products.filter(is_own_production=True)

    if get.get("hit") and "hit" not in skip:
        products = products.filter(is_hit=True)

    if get.get("new") and "new" not in skip:
        products = products.filter(is_new=True)

    for cf in active_catalog_filters():
        if cf.slug in skip:
            continue
        selected = get.getlist(cf.slug)
        if not selected:
            continue
        if cf.slug in ("volume", "weight", "pieces"):
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
    order_fields = SORT_OPTIONS.get(sort_key, SORT_OPTIONS["popularity"])
    if sort_key == "popularity" or sort_key not in SORT_OPTIONS:
        products = annotate_sold_qty(products)
    return products.order_by(*order_fields)


def _ordered_values_for_filter(cf, products):
    dict_ordered = [v.value for v in cf.values.all()]
    product_vals = set(
        products.filter(filter_attrs__catalog_filter=cf)
        .exclude(filter_attrs__value="")
        .values_list("filter_attrs__value", flat=True)
        .distinct()
    )
    if cf.slug in ("volume", "weight", "pieces"):
        product_vals.update(
            label
            for label in products.exclude(variants__label="")
            .values_list("variants__label", flat=True)
            .distinct()
            if pack_unit_kind(label) == cf.slug
            or (pack_unit_kind(label) is None and cf.slug == "pieces")
        )
    result = [v for v in dict_ordered if v in product_vals]
    orphans = sorted(v for v in product_vals if v not in set(dict_ordered))
    return result + orphans


def build_filter_context(request, products, category=None, *, base_products=None):
    """Контекст панелі фільтрів: системні + динамічні групи.

    Опції вже обраної групи рахуються з queryset без цього ж параметра.
    """
    get = request.GET
    dynamic = []
    active_count = 0
    base = base_products if base_products is not None else products

    for key in ("price_min", "price_max", "in_stock", "own_production", "hit", "new"):
        if get.get(key):
            active_count += 1

    for cf in active_catalog_filters():
        if not category_allows_catalog_filter(category, cf):
            continue
        selected = get.getlist(cf.slug)
        facet_qs = base
        if selected:
            # base вже з card_price; не анотати повторно
            facet_qs = filter_products(request, base, skip_slugs={cf.slug})
        values = _ordered_values_for_filter(cf, facet_qs)
        if not values and not selected:
            continue
        active_count += len(selected)
        dynamic.append({
            "slug": cf.slug,
            "name": cf.display_name(),
            "use_country_labels": cf.use_country_labels,
            "values": values or selected,
            "selected": selected,
        })

    return {
        "dynamic_filters": dynamic,
        "active_filters_count": active_count,
        "available_brands": [],
        "available_countries": [],
        "available_volumes": [],
        "available_weights": [],
        "available_pieces": [],
        "selected_brands": [],
        "selected_countries": [],
        "selected_volumes": [],
        "selected_weights": [],
        "selected_pieces": [],
        "show_brand_filter": False,
        "show_country_filter": False,
        "show_volume_filter": False,
        "show_weight_filter": False,
        "show_pieces_filter": False,
    }
