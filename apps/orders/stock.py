"""Перевірка, списання та повернення залишків варіантів."""

from __future__ import annotations

from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone

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


def reserve_minutes() -> int:
    return max(1, int(getattr(settings, "MONOPAY_STOCK_RESERVE_MINUTES", 60) or 60))


@transaction.atomic
def release_order_stock(order, *, mark_failed: bool = False) -> bool:
    """Повертає зарезервований залишок. False, якщо вже повернуто або оплачено."""
    from .models import Order

    locked = (
        Order.objects.select_for_update()
        .prefetch_related("items")
        .get(pk=order.pk)
    )
    if locked.stock_released:
        return False
    if locked.payment_status == Order.PaymentStatus.PAID:
        return False

    for item in locked.items.all():
        if not item.variant_id:
            continue
        variant = ProductVariant.objects.select_for_update().get(pk=item.variant_id)
        variant.stock_qty += int(item.quantity)
        variant.save(update_fields=["stock_qty"])

    locked.stock_released = True
    update_fields = ["stock_released"]
    if mark_failed and locked.payment_status == Order.PaymentStatus.PENDING:
        locked.payment_status = Order.PaymentStatus.FAILED
        update_fields.append("payment_status")
    locked.save(update_fields=update_fields)
    return True


@transaction.atomic
def rereserve_order_stock(order) -> None:
    """Повторний резерв після failed (кнопка «оплатити ще раз»). Кидає InsufficientStock."""
    from .models import Order

    locked = (
        Order.objects.select_for_update()
        .prefetch_related("items")
        .get(pk=order.pk)
    )
    if not locked.stock_released:
        if locked.payment_status == Order.PaymentStatus.FAILED:
            locked.payment_status = Order.PaymentStatus.PENDING
            locked.save(update_fields=["payment_status"])
        return

    items = list(locked.items.all())
    for item in items:
        if not item.variant_id:
            raise InsufficientStock(
                f"Варіант для «{item.product_name}» більше недоступний.",
            )
        variant = (
            ProductVariant.objects.select_for_update()
            .select_related("product")
            .get(pk=item.variant_id)
        )
        qty = int(item.quantity)
        if variant.stock_qty < qty:
            raise InsufficientStock(_stock_message(variant), variant.id)
        variant.stock_qty -= qty
        variant.save(update_fields=["stock_qty"])

    locked.stock_released = False
    locked.payment_status = Order.PaymentStatus.PENDING
    locked.save(update_fields=["stock_released", "payment_status"])


def release_stale_monopay_orders(*, minutes: int | None = None) -> int:
    """Pending Monopay старші за N хв → failed + повернення залишку. Повертає кількість."""
    from .models import Order

    cutoff = timezone.now() - timedelta(minutes=minutes if minutes is not None else reserve_minutes())
    stale_ids = list(
        Order.objects.filter(
            payment_method=Order.PaymentMethod.MONOPAY,
            payment_status=Order.PaymentStatus.PENDING,
            stock_released=False,
            created_at__lt=cutoff,
        ).values_list("pk", flat=True)
    )
    released = 0
    for pk in stale_ids:
        order = Order.objects.get(pk=pk)
        if release_order_stock(order, mark_failed=True):
            released += 1
    return released


def maybe_expire_order(order) -> bool:
    """Якщо Monopay pending і прострочений — повернути залишок. Інакше False."""
    from .models import Order

    if order.payment_method != Order.PaymentMethod.MONOPAY:
        return False
    if order.payment_status != Order.PaymentStatus.PENDING:
        return False
    if order.stock_released:
        return False
    age = timezone.now() - order.created_at
    if age < timedelta(minutes=reserve_minutes()):
        return False
    return release_order_stock(order, mark_failed=True)
