from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from apps.catalog.models import ProductVariant

from .cart import Cart
from .forms import CheckoutForm
from .models import Order, OrderItem


def cart_drawer_partial(request):
    """Повертає розмітку шторки кошика (для AJAX-оновлення без перезавантаження сторінки)."""
    return render(request, "includes/cart_drawer.html")


def cart_page(request):
    cart = Cart(request)
    context = {
        "cart_items": cart.get_items(),
        "cart_subtotal": cart.get_subtotal(),
        "free_shipping_threshold": 1500,
    }
    return render(request, "orders/cart.html", context)


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


def checkout(request):
    cart = Cart(request)
    if cart.is_empty():
        return redirect(reverse("orders_cart:page"))

    if request.method == "POST":
        form = CheckoutForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            subtotal = cart.get_subtotal()
            order.subtotal = subtotal
            order.total = subtotal - order.discount_total
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
            return redirect(reverse("orders_checkout:thank_you", args=[order.order_number]))
    else:
        form = CheckoutForm()

    context = {
        "form": form,
        "cart_items": cart.get_items(),
        "cart_subtotal": cart.get_subtotal(),
    }
    return render(request, "orders/checkout.html", context)


def thank_you(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    return render(request, "orders/thank_you.html", {"order": order})
