"""Оформлення замовлення: одноразовий токен, блокування залишків, снапшот цін."""

from __future__ import annotations

import secrets
from decimal import Decimal

from django.db import IntegrityError, transaction
from django.db.models import F

from apps.catalog.models import ProductVariant
from apps.core.models import SiteSettings

from .access import CHECKOUT_TOKEN_SESSION_KEY
from .cart import Cart
from .models import CheckoutNonce, Order, OrderItem, PromoCode
from .promo import clear_session_promo_code, get_session_promo_code
from .stock import InsufficientStock, decrement_cart_stock


class CheckoutError(Exception):
    pass


def ensure_checkout_token(request) -> str:
    token = request.session.get(CHECKOUT_TOKEN_SESSION_KEY)
    if not token:
        token = secrets.token_urlsafe(24)
        request.session[CHECKOUT_TOKEN_SESSION_KEY] = token
        request.session.modified = True
    return token


def rotate_checkout_token(request) -> str:
    token = secrets.token_urlsafe(24)
    request.session[CHECKOUT_TOKEN_SESSION_KEY] = token
    request.session.modified = True
    return token


def _free_shipping_threshold() -> Decimal:
    try:
        solo = SiteSettings.load()
        value = solo.free_shipping_threshold
    except Exception:
        from django.conf import settings

        value = getattr(settings, "FREE_SHIPPING_THRESHOLD", 1500)
    return Decimal(value or 0)


def _lock_promo(code: str, subtotal: Decimal) -> tuple[PromoCode | None, Decimal, str]:
    if not code:
        return None, Decimal("0"), ""
    promo = (
        PromoCode.objects.select_for_update()
        .filter(code__iexact=code)
        .first()
    )
    if not promo:
        return None, Decimal("0"), ""
    ok, _error = promo.is_usable(subtotal)
    if not ok:
        return None, Decimal("0"), ""
    discount = promo.calc_discount(subtotal)
    return promo, discount, promo.code


@transaction.atomic
def place_order(request, form) -> Order:
    """Створює замовлення з одноразовим токеном. Кидає CheckoutError / InsufficientStock."""
    raw_token = (request.POST.get("checkout_token") or "").strip()
    session_token = request.session.get(CHECKOUT_TOKEN_SESSION_KEY) or ""
    if not raw_token or raw_token != session_token:
        raise CheckoutError("Сесія оформлення застаріла. Оновіть сторінку і спробуйте ще раз.")

    try:
        CheckoutNonce.objects.create(token=raw_token)
    except IntegrityError as exc:
        raise CheckoutError("Замовлення вже надсилається. Зачекайте або перевірте сторінку «Дякуємо».") from exc

    cart = Cart(request)
    cart.prune_missing()
    if cart.is_empty():
        raise CheckoutError("Кошик порожній.")

    # Блокуємо активні варіанти і перераховуємо ціни з БД.
    locked_items = []
    for variant_id_str, qty in list(cart.cart.items()):
        qty = int(qty)
        if qty <= 0:
            continue
        variant = (
            ProductVariant.objects.select_for_update()
            .select_related("product")
            .filter(pk=int(variant_id_str), product__is_active=True)
            .first()
        )
        if variant is None:
            cart.remove(variant_id_str)
            continue
        if variant.price <= 0:
            raise CheckoutError(
                f"«{variant.product.name}» ({variant.label}) недоступний для замовлення (ціна)."
            )
        if variant.stock_qty < qty:
            raise InsufficientStock(
                f"Недостатньо «{variant.product.name}» ({variant.label}): "
                f"є {variant.stock_qty} шт.",
                variant.id,
            )
        locked_items.append({
            "variant": variant,
            "product": variant.product,
            "quantity": qty,
            "price": variant.price,
            "line_total": variant.price * qty,
        })

    if not locked_items:
        raise CheckoutError("Кошик порожній.")

    subtotal = sum((item["line_total"] for item in locked_items), Decimal("0"))
    if subtotal <= 0:
        raise CheckoutError("Сума замовлення має бути більшою за нуль.")

    session_code = get_session_promo_code(request)
    form_code = (form.cleaned_data.get("promo_code") or "").strip().upper()
    code = session_code or form_code
    promo, discount, applied_code = _lock_promo(code, subtotal)
    total = max(subtotal - discount, Decimal("0"))
    threshold = _free_shipping_threshold()

    decrement_cart_stock(locked_items)

    order = form.save(commit=False)
    order.subtotal = subtotal
    order.promo_code = applied_code
    order.discount_total = discount
    order.total = total
    order.shipping_is_free = total >= threshold if threshold else False
    order.payment_status = Order.PaymentStatus.PENDING
    order.save()

    for item in locked_items:
        OrderItem.objects.create(
            order=order,
            product=item["product"],
            variant=item["variant"],
            product_name=item["product"].name,
            variant_label=item["variant"].label,
            price=item["price"],
            quantity=item["quantity"],
        )

    if promo is not None:
        PromoCode.objects.filter(pk=promo.pk).update(used_count=F("used_count") + 1)

    cart.clear()
    clear_session_promo_code(request)
    request.session.pop(CHECKOUT_TOKEN_SESSION_KEY, None)
    request.session.modified = True
    return order
