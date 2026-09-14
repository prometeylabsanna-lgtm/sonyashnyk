"""Перевірка та списання залишків варіантів при оформленні."""

from __future__ import annotations

from django.db import transaction

from apps.catalog.models import ProductVariant


class InsufficientStock(Exception):
    def __init__(self, message: str, variant_id: int | None = None):
        super().__init__(message)
        self.variant_id = variant_id


def _stock_message(variant: ProductVariant) -> str:
    return (
        f"Недостатньо «{variant.product.name}» ({variant.label}): "
        f"є {variant.stock_qty} шт."
    )


def check_cart_stock(cart_items: list[dict]) -> None:
    """Кидає InsufficientStock, якщо якоїсь позиції не вистачає."""
    for item in cart_items:
        variant = item["variant"]
        qty = int(item["quantity"])
        if qty <= 0:
            raise InsufficientStock("Некоректна кількість.", variant.id)
        if variant.stock_qty < qty:
            raise InsufficientStock(_stock_message(variant), variant.id)


def decrement_cart_stock(cart_items: list[dict]) -> None:
    """Атомарно списує залишки (select_for_update). Викликати всередині transaction.atomic."""
    for item in cart_items:
        variant = (
            ProductVariant.objects.select_for_update()
            .select_related("product")
            .get(pk=item["variant"].pk)
        )
        qty = int(item["quantity"])
        if variant.stock_qty < qty:
            raise InsufficientStock(_stock_message(variant), variant.id)
        variant.stock_qty -= qty
        variant.save(update_fields=["stock_qty"])


@transaction.atomic
def reserve_stock_for_items(cart_items: list[dict]) -> None:
    decrement_cart_stock(cart_items)
