from .cart import Cart


def cart_summary(request):
    """Дає доступ до кошика (лічильник у шапці + шторка) на всіх сторінках."""
    cart = Cart(request)
    return {
        "cart_count": len(cart),
        "cart_is_empty": cart.is_empty(),
        "cart_drawer_items": cart.get_items(),
        "cart_drawer_subtotal": cart.get_subtotal(),
    }
