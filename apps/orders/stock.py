"""Перевірка, списання та повернення залишків варіантів."""

from __future__ import annotations

import logging
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.catalog.models import ProductVariant

logger = logging.getLogger(__name__)


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
    return max(1, int(getattr(settings, "MONOPAY_STOCK_RESERVE_MINUTES", 15) or 15))


def _reserve_anchor(order):
    return order.monopay_invoice_at or order.created_at


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


def apply_monopay_status(order, mono_status: str, *, payload: dict | None = None) -> bool:
    """Застосовує статус Mono до замовлення. True якщо щось змінилось."""
    from . import monopay
    from .models import Order

    mapped = monopay.map_status(mono_status)
    if mapped is None:
        return False

    if mapped == Order.PaymentStatus.PAID:
        if payload is not None and not monopay.amount_matches_order(payload, order):
            return False
        if order.payment_status == Order.PaymentStatus.PAID:
            return False
        order.payment_status = mapped
        order.save(update_fields=["payment_status"])
        return True

    if mapped == Order.PaymentStatus.REFUNDED:
        if order.payment_status == Order.PaymentStatus.REFUNDED and order.stock_released:
            return False
        order.payment_status = mapped
        order.save(update_fields=["payment_status"])
        release_order_stock(order)
        return True

    if mapped == Order.PaymentStatus.FAILED:
        if order.payment_status == Order.PaymentStatus.PAID:
            return False
        if order.payment_status == Order.PaymentStatus.FAILED and order.stock_released:
            return False
        order.payment_status = mapped
        order.save(update_fields=["payment_status"])
        release_order_stock(order)
        return True

    return False


def sync_order_from_monopay(order) -> bool:
    """Poll статусу інвойсу (критично: Mono не шле webhook на expired)."""
    from . import monopay
    from .models import Order

    if order.payment_method != Order.PaymentMethod.MONOPAY:
        return False
    if order.payment_status not in (
        Order.PaymentStatus.PENDING,
        Order.PaymentStatus.FAILED,
    ):
        return False
    if not order.monopay_invoice_id or not monopay.is_configured():
        return False
    try:
        data = monopay.get_invoice_status(order.monopay_invoice_id)
    except monopay.MonopayError as exc:
        logger.info("Monopay status sync skip %s: %s", order.order_number, exc)
        return False
    return apply_monopay_status(order, data.get("status", ""), payload=data)


def release_stale_monopay_orders(*, minutes: int | None = None) -> int:
    """Pending Monopay: poll Mono + TTL → failed + повернення залишку."""
    from .models import Order

    mins = minutes if minutes is not None else reserve_minutes()
    cutoff = timezone.now() - timedelta(minutes=mins)
    pending = list(
        Order.objects.filter(
            payment_method=Order.PaymentMethod.MONOPAY,
            payment_status=Order.PaymentStatus.PENDING,
            stock_released=False,
        ).order_by("id")[:200]
    )
    released = 0
    for order in pending:
        if sync_order_from_monopay(order):
            order.refresh_from_db()
            if order.stock_released or order.payment_status != Order.PaymentStatus.PENDING:
                released += 1
                continue
        anchor = _reserve_anchor(order)
        if anchor and anchor < cutoff:
            if release_order_stock(order, mark_failed=True):
                released += 1
    return released


def maybe_expire_order(order) -> bool:
    """Poll Mono + TTL для pending Monopay. True якщо статус/залишок змінено."""
    from .models import Order

    if order.payment_method != Order.PaymentMethod.MONOPAY:
        return False
    if order.payment_status != Order.PaymentStatus.PENDING:
        return False
    if order.stock_released:
        return False

    if sync_order_from_monopay(order):
        order.refresh_from_db()
        return True

    anchor = _reserve_anchor(order)
    if not anchor:
        return False
    if timezone.now() - anchor < timedelta(minutes=reserve_minutes()):
        return False
    return release_order_stock(order, mark_failed=True)
