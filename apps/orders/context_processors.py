from decimal import Decimal

from apps.core.db_safe import database_reachable

from .cart import Cart
from .promo import resolve_promo


def cart_summary(request):
    """Дає доступ до кошика (лічильник у шапці + шторка) на всіх сторінках."""
    cart = Cart(request)
    if not database_reachable() or cart.is_empty():
        return {
            "cart_count": len(cart) if database_reachable() else 0,
            "cart_is_empty": True,
            "cart_drawer_items": [],
            "cart_drawer_subtotal": Decimal("0"),
            "cart_drawer_discount": Decimal("0"),
            "cart_drawer_total": Decimal("0"),
            "cart_drawer_promo_code": "",
        }
    subtotal = cart.get_subtotal()
    promo = resolve_promo(request, subtotal)
    return {
        "cart_count": len(cart),
        "cart_is_empty": cart.is_empty(),
        "cart_drawer_items": cart.get_items(),
        "cart_drawer_subtotal": subtotal,
        "cart_drawer_discount": promo["discount"],
        "cart_drawer_total": promo["total"],
        "cart_drawer_promo_code": promo["code"],
    }
