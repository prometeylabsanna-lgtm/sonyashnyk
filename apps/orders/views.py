from decimal import Decimal

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from apps.catalog.models import ProductVariant

from .cart import Cart
from .forms import CheckoutForm
from .models import Order, OrderItem
from .promo import apply_promo_code, clear_session_promo_code, resolve_promo


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
    cart.add(variant.id, quantity)

    if request.headers.get("x-requested-with") == "fetch":
        return JsonResponse({"ok": True, "cart_count": len(cart)})

    messages.success(request, f"«{variant.product.name}» додано в кошик.")
    return redirect(request.POST.get("next") or reverse("orders_cart:page"))


@require_POST
def cart_update(request, variant_id):
    quantity = int(request.POST.get("quantity", 1) or 1)
    cart = Cart(request)
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
            order = form.save(commit=False)
            order.subtotal = subtotal
            # Пріоритет — промокод із сесії кошика; інакше з форми
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
            order.save()

            for item in cart.get_items():
                OrderItem.objects.create(
                    order=order,
                    product=item["product"],
                    variant=item["variant"],
                    product_name=item["product"].name,
                    variant_label=item["variant"].label,
                    price=item["price"],
                    quantity=item["quantity"],
                )

            if order.payment_method == Order.PaymentMethod.LIQPAY:
                # TODO: тут буде реальна інтеграція LiqPay (mock на етапі скелета).
                order.payment_status = Order.PaymentStatus.PENDING
                order.save(update_fields=["payment_status"])

            cart.clear()
            clear_session_promo_code(request)
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
    }
    return render(request, "orders/checkout.html", context)


def thank_you(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    return render(request, "orders/thank_you.html", {"order": order})
