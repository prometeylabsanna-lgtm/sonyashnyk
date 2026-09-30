"""Доступ до сторінок thank-you / pay за сесією або підписаним токеном."""

from urllib.parse import urlencode

from django.core import signing
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.urls import reverse

from .models import Order

LAST_ORDER_SESSION_KEY = "last_order_number"
ORDER_ACCESS_SALT = "orders.order_access"
ORDER_ACCESS_MAX_AGE = 7 * 24 * 60 * 60  # 7 днів
CHECKOUT_TOKEN_SESSION_KEY = "checkout_token"


def make_order_access_token(order_number: str) -> str:
    return signing.dumps({"n": order_number}, salt=ORDER_ACCESS_SALT)


def verify_order_access_token(token: str, order_number: str) -> bool:
    if not token:
        return False
    try:
        data = signing.loads(token, salt=ORDER_ACCESS_SALT, max_age=ORDER_ACCESS_MAX_AGE)
    except signing.BadSignature:
        return False
    return data.get("n") == order_number


def remember_order(request, order: Order) -> str:
    """Пише номер у сесію і повертає підписаний токен доступу."""
    request.session[LAST_ORDER_SESSION_KEY] = order.order_number
    request.session.modified = True
    return make_order_access_token(order.order_number)


def user_can_access_order(request, order: Order) -> bool:
    session_num = request.session.get(LAST_ORDER_SESSION_KEY)
    if session_num and session_num == order.order_number:
        return True
    token = request.GET.get("t") or ""
    return verify_order_access_token(token, order.order_number)


def get_accessible_order(request, order_number: str) -> Order:
    order = get_object_or_404(Order, order_number=order_number)
    if not user_can_access_order(request, order):
        raise Http404()
    return order


def order_url(viewname: str, order: Order, access_token: str | None = None) -> str:
    url = reverse(viewname, args=[order.order_number])
    token = access_token or make_order_access_token(order.order_number)
    return f"{url}?{urlencode({'t': token})}"
