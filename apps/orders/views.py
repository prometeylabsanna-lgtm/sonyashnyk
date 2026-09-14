import json
from decimal import Decimal

from django.contrib import messages
from django.db import transaction
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from apps.catalog.models import ProductVariant

from .cart import Cart
from .forms import CheckoutForm
from . import liqpay
from .models import Order, OrderItem
from .nova_poshta import is_configured as np_is_configured
from .nova_poshta import search_cities, search_warehouses
from .promo import apply_promo_code, clear_session_promo_code, resolve_promo
from .stock import InsufficientStock, reserve_stock_for_items


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
        "free_shipping_threshold": 1500,
    }


def cart_page(request):
    cart = Cart(request)
    return render(request, "orders/cart.html", _cart_totals(request, cart))


@require_POST
def cart_add(request):
    variant_id = request.POST.get("variant_id")
    quantity = int(request.POST.get("quantity", 1) or 1)
    variant = get_object_or_404(ProductVariant, pk=variant_id)
    cart = Cart(request)

    current = cart.cart.get(str(variant.id), 0)
    if current + quantity > variant.stock_qty:
        msg = f"Недостатньо на складі: доступно {variant.stock_qty} шт."
        if request.headers.get("x-requested-with") == "fetch":
            return JsonResponse({"ok": False, "error": msg}, status=400)
        messages.error(request, msg)
        return redirect(request.POST.get("next") or reverse("orders_cart:page"))

    cart.add(variant.id, quantity)

    if request.headers.get("x-requested-with") == "fetch":
        return JsonResponse({"ok": True, "cart_count": len(cart)})

    messages.success(request, f"«{variant.product.name}» додано в кошик.")
    return redirect(request.POST.get("next") or reverse("orders_cart:page"))


@require_POST
def cart_update(request, variant_id):
    quantity = int(request.POST.get("quantity", 1) or 1)
    cart = Cart(request)
    variant = get_object_or_404(ProductVariant, pk=variant_id)
    if quantity > variant.stock_qty:
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
            cart_items = cart.get_items()
            try:
                with transaction.atomic():
                    reserve_stock_for_items(cart_items)

                    order = form.save(commit=False)
                    order.subtotal = subtotal
                    code = promo_state["code"] or (form.cleaned_data.get("promo_code") or "").strip().upper()
                    if code and not promo_state["code"]:
                        applied = apply_promo_code(request, code, subtotal)
                        discount = applied["discount"] if applied["ok"] else promo_state["discount"]
                        code = applied["code"] if applied["ok"] else code
                    else:
                        discount = promo_state["discount"]

                    order.promo_code = code
                    order.discount_total = discount
                    order.total = max(subtotal - discount, Decimal("0"))
                    order.payment_status = Order.PaymentStatus.PENDING
                    order.save()

                    for item in cart_items:
                        OrderItem.objects.create(
                            order=order,
                            product=item["product"],
                            variant=item["variant"],
                            product_name=item["product"].name,
                            variant_label=item["variant"].label,
                            price=item["price"],
                            quantity=item["quantity"],
                        )
            except InsufficientStock as exc:
                messages.error(request, str(exc))
                return redirect(reverse("orders_cart:page"))

            cart.clear()
            clear_session_promo_code(request)

            if order.payment_method == Order.PaymentMethod.LIQPAY:
                return redirect(reverse("orders_checkout:pay", args=[order.order_number]))
            return redirect(reverse("orders_checkout:thank_you", args=[order.order_number]))
    else:
        initial = {}
        if promo_state["code"]:
            initial["promo_code"] = promo_state["code"]
        form = CheckoutForm(initial=initial)

    context = {
        "form": form,
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
    order = get_object_or_404(Order, order_number=order_number)
    can_pay_again = (
        order.payment_method == Order.PaymentMethod.LIQPAY
        and order.payment_status in (Order.PaymentStatus.FAILED, Order.PaymentStatus.PENDING)
    )
    return render(request, "orders/thank_you.html", {
        "order": order,
        "can_pay_again": can_pay_again,
    })


def pay(request, order_number):
    """Сторінка оплати LiqPay (реальний form-post або mock без ключів)."""
    order = get_object_or_404(Order, order_number=order_number)
    if order.payment_method != Order.PaymentMethod.LIQPAY:
        return redirect(reverse("orders_checkout:thank_you", args=[order.order_number]))
    if order.payment_status == Order.PaymentStatus.PAID:
        return redirect(reverse("orders_checkout:thank_you", args=[order.order_number]))

    if liqpay.is_configured():
        form_data = liqpay.build_checkout_form(order)
        return render(request, "orders/liqpay_redirect.html", {
            "order": order,
            "liqpay_url": form_data["url"],
            "liqpay_data": form_data["data"],
            "liqpay_signature": form_data["signature"],
        })

    return render(request, "orders/liqpay_mock.html", {"order": order})


@require_POST
def pay_mock(request, order_number):
    """Локальний sandbox без ключів LiqPay: симуляція success/fail."""
    order = get_object_or_404(Order, order_number=order_number)
    if order.payment_method != Order.PaymentMethod.LIQPAY:
        return redirect(reverse("orders_checkout:thank_you", args=[order.order_number]))
    if liqpay.is_configured():
        return redirect(reverse("orders_checkout:pay", args=[order.order_number]))

    action = (request.POST.get("action") or "").strip().lower()
    if action == "success":
        order.payment_status = Order.PaymentStatus.PAID
    else:
        order.payment_status = Order.PaymentStatus.FAILED
    order.save(update_fields=["payment_status"])
    return redirect(reverse("orders_checkout:thank_you", args=[order.order_number]))


@csrf_exempt
@require_POST
def liqpay_callback(request):
    """Server-to-server callback від LiqPay."""
    data = request.POST.get("data", "")
    signature = request.POST.get("signature", "")
    if not liqpay.verify_signature(data, signature):
        return HttpResponseBadRequest("invalid signature")

    try:
        payload = liqpay.decode_data(data)
    except (ValueError, TypeError, json.JSONDecodeError):
        return HttpResponseBadRequest("invalid data")

    order_id = payload.get("order_id")
    if not order_id:
        return HttpResponseBadRequest("missing order_id")

    order = Order.objects.filter(order_number=order_id).first()
    if not order:
        return HttpResponseBadRequest("order not found")

    mapped = liqpay.map_status(payload.get("status", ""))
    if mapped and order.payment_status != Order.PaymentStatus.PAID:
        order.payment_status = mapped
        order.save(update_fields=["payment_status"])

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
