"""Об'єднання окремих SKU одного засобу в товар із варіантами обʼєму / ваги / кількості."""

from __future__ import annotations

import re

from django.db import transaction
from django.db.models import QuerySet

from .models import Product, ProductVariant

_PACK_TAIL = re.compile(
    r"[\s,;:\-]*(?:\d+(?:[.,]\d+)?\s*(?:мл|л|г|кг|шт|упак)\.?)\s*$",
    re.IGNORECASE,
)


class MergeError(ValueError):
    pass


def _clear_prefetch(product: Product, *related: str) -> None:
    cache = getattr(product, "_prefetched_objects_cache", None)
    if not cache:
        return
    for name in related:
        cache.pop(name, None)


def strip_pack_from_name(name: str) -> str:
    cleaned = _PACK_TAIL.sub("", (name or "").strip()).strip()
    return cleaned or (name or "").strip()


def _unique_label(label: str, taken: set[str], sku: str) -> str:
    base = (label or "").strip() or sku or "варіант"
    key = base.casefold()
    if key not in taken:
        return base
    suffix = (sku or "").strip()
    candidate = f"{base} ({suffix})" if suffix else f"{base} ·"
    n = 2
    while candidate.casefold() in taken:
        candidate = f"{base} ({suffix or n})"
        n += 1
    return candidate


def _ensure_parent_variant(parent: Product) -> int:
    existing = list(parent.variants.all())
    if existing:
        return max(item.order for item in existing) + 1
    ProductVariant.objects.create(
        product=parent,
        label=(parent.pack_volume or "1 шт").strip() or "1 шт",
        sku_variant=parent.sku,
        price=parent.base_price,
        old_price=parent.old_price,
        stock_qty=0,
        is_default=True,
        order=0,
    )
    _clear_prefetch(parent, "variants")
    return 1


def merge_products(queryset: QuerySet[Product], parent: Product | None = None) -> tuple[Product, list[Product]]:
    products = list(queryset.order_by("id").prefetch_related("variants", "images"))
    if len(products) < 2:
        raise MergeError("Оберіть щонайменше два товари з різним обʼємом, вагою або кількістю.")

    if parent is None:
        parent = products[0]
    elif parent.pk not in {item.pk for item in products}:
        raise MergeError("Основний товар має бути серед вибраних.")

    children = [item for item in products if item.pk != parent.pk]

    with transaction.atomic():
        next_order = _ensure_parent_variant(parent)
        taken = {item.label.strip().casefold() for item in parent.variants.all() if item.label}

        for child in children:
            child_variants = list(child.variants.all())
            if child_variants:
                for variant in child_variants:
                    variant.product = parent
                    if not (variant.sku_variant or "").strip():
                        variant.sku_variant = child.sku
                    variant.label = _unique_label(variant.label, taken, child.sku)
                    variant.is_default = False
                    variant.order = next_order
                    variant.save()
                    taken.add(variant.label.casefold())
                    next_order += 1
            else:
                label = _unique_label(child.pack_volume or child.name, taken, child.sku)
                ProductVariant.objects.create(
                    product=parent,
                    label=label,
                    sku_variant=child.sku,
                    price=child.base_price,
                    old_price=child.old_price,
                    stock_qty=0,
                    is_default=False,
                    order=next_order,
                )
                taken.add(label.casefold())
                next_order += 1

            image_order = parent.images.count()
            for image in child.images.all():
                image.product = parent
                image.order = image_order
                image.save(update_fields=["product", "order"])
                image_order += 1

            child.certificates.update(product=parent)
            child.is_active = False
            child.save(update_fields=["is_active"])
            _clear_prefetch(parent, "variants", "images")

        stripped = {strip_pack_from_name(item.name) for item in products}
        if len(stripped) == 1:
            common = stripped.pop()
            if common and common != parent.name:
                parent.name = common
                parent.save(update_fields=["name"])

        default = parent.default_variant
        if default and default.label and not parent.pack_volume:
            parent.pack_volume = default.label
            parent.save(update_fields=["pack_volume"])

    parent.refresh_from_db()
    return parent, children
