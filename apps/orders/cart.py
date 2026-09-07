"""Кошик на основі сесії (без БД) — простий та швидкий для MVP."""

from decimal import Decimal

from django.conf import settings

from apps.catalog.models import ProductVariant


class Cart:
    """Кошик зберігається в сесії як {variant_id (str): quantity (int)}."""

    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_KEY)
        if cart is None:
            cart = self.session[settings.CART_SESSION_KEY] = {}
        self.cart = cart

    def add(self, variant_id, quantity=1):
        variant_id = str(variant_id)
        current = self.cart.get(variant_id, 0)
        self.cart[variant_id] = max(1, current + quantity)
        self.save()

    def set_quantity(self, variant_id, quantity):
        variant_id = str(variant_id)
        if quantity <= 0:
            self.remove(variant_id)
            return
        self.cart[variant_id] = quantity
        self.save()

    def remove(self, variant_id):
        variant_id = str(variant_id)
        if variant_id in self.cart:
            del self.cart[variant_id]
            self.save()

    def clear(self):
        self.session[settings.CART_SESSION_KEY] = {}
        self.save()

    def save(self):
        self.session[settings.CART_SESSION_KEY] = self.cart
        self.session.modified = True

    def __len__(self):
        return sum(self.cart.values())

    def get_variants(self):
        ids = [int(vid) for vid in self.cart.keys()]
        return ProductVariant.objects.filter(id__in=ids).select_related("product")

    def get_items(self):
        """Повертає список рядків кошика з обрахованими сумами."""
        items = []
        for variant in self.get_variants():
            qty = self.cart[str(variant.id)]
            line_total = variant.price * qty
            items.append({
                "variant": variant,
                "product": variant.product,
                "quantity": qty,
                "price": variant.price,
                "line_total": line_total,
            })
        return items

    def get_subtotal(self):
        return sum((item["line_total"] for item in self.get_items()), Decimal("0"))

    def is_empty(self):
        return len(self.cart) == 0
