import json

from django.contrib import messages
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from django.utils import timezone

from apps.catalog.models import ProductVariant

from . import monopay
from .access import (
    get_accessible_order,
    order_url,
    remember_order,
)
from .cart import Cart
from .checkout import CheckoutError, ensure_checkout_token, place_order, rotate_checkout_token
from .forms import CheckoutForm
from .models import Order
from .nova_poshta import is_configured as np_is_configured
from .nova_poshta import search_cities, search_warehouses
from .promo import apply_promo_code, clear_session_promo_code, resolve_promo
from .stock import InsufficientStock, apply_monopay_status, maybe_expire_order, rereserve_order_stock


def _safe_next(raw: str | None, fallback: str) -> str:
    if not raw:
        return fallback
    raw = raw.strip()
    if raw.startswith("/") and not raw.startswith("//"):
        return raw
    return fallback


def _parse_quantity(raw) -> int | None:
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return None
    return value


def cart_drawer_partial(request):
    """Повертає розмітку шторки кошика (для AJAX-оновлення без перезавантаження сторінки)."""
    return render(request, "includes/cart_drawer.html")


def _cart_totals(request, cart):
    subtotal = cart.get_subtotal()
    promo = resolve_promo(request, subtotal)
    return {
        "cart_items": cart.get_items(),
        "cart_subtotal": subtotal,
        "cart_discount": promo["discount"],
        "cart_total": promo["total"],
        "promo_code": promo["code"],
        "promo_error": promo["error"],
    }


def cart_page(request):
    cart = Cart(request)
    return render(request, "orders/cart.html", _cart_totals(request, cart))


@require_POST
def cart_add(request):
    fallback = reverse("orders_cart:page")
    next_url = _safe_next(request.POST.get("next"), fallback)
    quantity = _parse_quantity(request.POST.get("quantity", 1) or 1)
    if quantity is None or quantity < 1:
        msg = "Некоректна кількість."
        if request.headers.get("x-requested-with") == "fetch":
            return JsonResponse({"ok": False, "error": msg}, status=400)
        messages.error(request, msg)
        return redirect(next_url)

    variant = get_object_or_404(
        ProductVariant.objects.select_related("product"),
        pk=request.POST.get("variant_id"),
        product__is_active=True,
    )
    if variant.price <= 0:
        msg = "Цей товар зараз недоступний для замовлення."
        if request.headers.get("x-requested-with") == "fetch":
            return JsonResponse({"ok": False, "error": msg}, status=400)
        messages.error(request, msg)
        return redirect(next_url)

    cart = Cart(request)
    current = int(cart.cart.get(str(variant.id), 0) or 0)
    desired = current + quantity
    if desired > variant.stock_qty:
        msg = f"Недостатньо на складі: доступно {variant.stock_qty} шт."
        if request.headers.get("x-requested-with") == "fetch":
            return JsonResponse({"ok": False, "error": msg}, status=400)
        messages.error(request, msg)
        return redirect(next_url)

    cart.add(variant.id, quantity)

    if request.headers.get("x-requested-with") == "fetch":
        return JsonResponse({"ok": True, "cart_count": len(cart)})

    messages.success(request, f"«{variant.product.name}» додано в кошик.")
    return redirect(next_url)


@require_POST
def cart_update(request, variant_id):
    quantity = _parse_quantity(request.POST.get("quantity", 1) or 1)
    if quantity is None:
        msg = "Некоректна кількість."
        if request.headers.get("x-requested-with") == "fetch":
            return JsonResponse({"ok": False, "error": msg}, status=400)
        messages.error(request, msg)
        return redirect(reverse("orders_cart:page"))

    cart = Cart(request)
    variant = get_object_or_404(
        ProductVariant.objects.select_related("product"),
        pk=variant_id,
        product__is_active=True,
    )
    if quantity > 0 and variant.price <= 0:
        msg = "Цей товар зараз недоступний для замовлення."
        if request.headers.get("x-requested-with") == "fetch":
            return JsonResponse({"ok": False, "error": msg}, status=400)
        messages.error(request, msg)
        return redirect(reverse("orders_cart:page"))
    if quantity > 0 and quantity > variant.stock_qty:
        msg = f"Недостатньо на складі: доступно {variant.stock_qty} шт."
        if request.headers.get("x-requested-with") == "fetch":
            return JsonResponse({"ok": False, "error": msg}, status=400)
        messages.error(request, msg)
        return redirect(reverse("orders_cart:page"))

    cart.set_quantity(variant_id, quantity)
    if request.headers.get("x-requested-with") == "fetch":
        return JsonResponse({
            "ok": True,
            "cart_count": len(cart),
            "cart_subtotal": str(cart.get_subtotal()),
        })
    return redirect(reverse("orders_cart:page"))


@require_POST
def cart_remove(request, variant_id):
    cart = Cart(request)
    cart.remove(variant_id)
    if request.headers.get("x-requested-with") == "fetch":
        return JsonResponse({"ok": True, "cart_count": len(cart)})
    return redirect(reverse("orders_cart:page"))


@require_POST
def cart_promo(request):
    cart = Cart(request)
    action = (request.POST.get("action") or "apply").strip().lower()
    if action == "clear":
        clear_session_promo_code(request)
        messages.info(request, "Промокод скасовано.")
        return redirect(reverse("orders_cart:page"))

    result = apply_promo_code(request, request.POST.get("promo_code", ""), cart.get_subtotal())
    if result["ok"]:
        messages.success(request, f"Промокод «{result['code']}» застосовано.")
    else:
        messages.error(request, result["error"] or "Не вдалося застосувати промокод.")
    return redirect(reverse("orders_cart:page"))


def checkout(request):
    cart = Cart(request)
    if cart.is_empty():
        return redirect(reverse("orders_cart:page"))

    subtotal = cart.get_subtotal()
    promo_state = resolve_promo(request, subtotal)

    if request.method == "POST":
        form = CheckoutForm(request.POST)
        if form.is_valid():
            try:
                order = place_order(request, form)
            except InsufficientStock as exc:
                messages.error(request, str(exc))
                return redirect(reverse("orders_cart:page"))
            except CheckoutError as exc:
                messages.error(request, str(exc))
                rotate_checkout_token(request)
                return redirect(reverse("orders_checkout:page"))

            access = remember_order(request, order)
            if order.payment_method == Order.PaymentMethod.MONOPAY:
                return redirect(order_url("orders_checkout:pay", order, access))
            return redirect(order_url("orders_checkout:thank_you", order, access))
    else:
        initial = {}
        if promo_state["code"]:
            initial["promo_code"] = promo_state["code"]
        form = CheckoutForm(initial=initial)
        ensure_checkout_token(request)

    context = {
        "form": form,
        "checkout_token": ensure_checkout_token(request),
        "cart_items": cart.get_items(),
        "cart_subtotal": subtotal,
        "cart_discount": promo_state["discount"],
        "cart_total": promo_state["total"],
        "promo_code": promo_state["code"],
        "np_api_enabled": np_is_configured(),
        "np_cities_url": reverse("orders_checkout:np_cities"),
        "np_warehouses_url": reverse("orders_checkout:np_warehouses"),
    }
    return render(request, "orders/checkout.html", context)


def thank_you(request, order_number):
    order = get_accessible_order(request, order_number)
    if maybe_expire_order(order):
        order.refresh_from_db()
    can_pay_again = (
        order.payment_method == Order.PaymentMethod.MONOPAY
        and order.payment_status in (Order.PaymentStatus.FAILED, Order.PaymentStatus.PENDING)
    )
    pay_again_url = ""
    if can_pay_again:
        pay_again_url = order_url("orders_checkout:pay", order)
    status_url = ""
    if order.payment_method == Order.PaymentMethod.MONOPAY and order.payment_status == Order.PaymentStatus.PENDING:
        status_url = order_url("orders_checkout:payment_status", order)
    return render(request, "orders/thank_you.html", {
        "order": order,
        "can_pay_again": can_pay_again,
        "pay_again_url": pay_again_url,
        "payment_status_url": status_url,
    })


@require_GET
def payment_status(request, order_number):
    """Легкий JSON для poll на thank-you (той самий access-gate)."""
    order = get_accessible_order(request, order_number)
    if maybe_expire_order(order):
        order.refresh_from_db()
    return JsonResponse({
        "ok": True,
        "order_number": order.order_number,
        "payment_status": order.payment_status,
        "payment_method": order.payment_method,
    })


def pay(request, order_number):
    """Створює Monopay-інвойс і редіректить на pageUrl."""
    order = get_accessible_order(request, order_number)
    if maybe_expire_order(order):
        order.refresh_from_db()
    if order.payment_method != Order.PaymentMethod.MONOPAY:
        return redirect(order_url("orders_checkout:thank_you", order))
    if order.payment_status == Order.PaymentStatus.PAID:
        return redirect(order_url("orders_checkout:thank_you", order))
    if order.payment_status not in (
        Order.PaymentStatus.PENDING,
        Order.PaymentStatus.FAILED,
    ):
        return redirect(order_url("orders_checkout:thank_you", order))

    if not monopay.is_configured():
        messages.error(request, "Онлайн-оплата тимчасово недоступна. Спробуйте пізніше або оберіть інший спосіб.")
        return redirect(order_url("orders_checkout:thank_you", order))

    try:
        rereserve_order_stock(order)
    except InsufficientStock as exc:
        messages.error(request, str(exc))
        return redirect(order_url("orders_checkout:thank_you", order))
    order.refresh_from_db()

    try:
        invoice = monopay.create_invoice(order)
    except monopay.MonopayError:
        messages.error(request, "Не вдалося створити оплату Monobank. Спробуйте ще раз.")
        return redirect(order_url("orders_checkout:thank_you", order))

    order.monopay_invoice_id = invoice["invoice_id"]
    order.monopay_invoice_at = timezone.now()
    order.save(update_fields=["monopay_invoice_id", "monopay_invoice_at"])

    return render(request, "orders/monopay_redirect.html", {
        "order": order,
        "page_url": invoice["page_url"],
    })


@csrf_exempt
@require_POST
def monopay_callback(request):
    """Server-to-server webhook від Monobank Acquiring."""
    body = request.body or b""
    x_sign = request.headers.get("X-Sign") or request.META.get("HTTP_X_SIGN", "")
    if not monopay.verify_webhook(body, x_sign):
        return HttpResponseBadRequest("invalid signature")

    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return HttpResponseBadRequest("invalid data")

    if not isinstance(payload, dict):
        return HttpResponseBadRequest("invalid data")

    order_id = monopay.resolve_order_number(payload)
    if not order_id:
        return HttpResponseBadRequest("missing reference")

    order = Order.objects.filter(order_number=order_id).first()
    if not order:
        return HttpResponseBadRequest("order not found")

    invoice_id = (payload.get("invoiceId") or "").strip()
    if invoice_id and invoice_id != order.monopay_invoice_id:
        order.monopay_invoice_id = invoice_id
        order.save(update_fields=["monopay_invoice_id"])

    mapped = monopay.map_status(payload.get("status", ""))
    if mapped == Order.PaymentStatus.PAID and not monopay.amount_matches_order(payload, order):
        return HttpResponseBadRequest("amount mismatch")

    apply_monopay_status(order, payload.get("status", ""), payload=payload)
    return HttpResponse("ok")


@require_GET
def np_cities(request):
    q = request.GET.get("q", "")
    result = search_cities(q)
    return JsonResponse(result)


@require_GET
def np_warehouses(request):
    city_ref = request.GET.get("city_ref", "")
    q = request.GET.get("q", "")
    delivery = request.GET.get("kind", "branch")
    kind = "locker" if delivery == "locker" else "branch"
    result = search_warehouses(city_ref, q, kind=kind)
    return JsonResponse(result)
