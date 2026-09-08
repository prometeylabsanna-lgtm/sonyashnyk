"""Промокод у сесії кошика — застосування та розрахунок знижки."""

from decimal import Decimal

from django.conf import settings

from .models import PromoCode

PROMO_SESSION_KEY = getattr(settings, "PROMO_SESSION_KEY", "cart_promo")


def get_session_promo_code(request) -> str:
    return (request.session.get(PROMO_SESSION_KEY) or "").strip().upper()


def set_session_promo_code(request, code: str) -> None:
    code = (code or "").strip().upper()
    if code:
        request.session[PROMO_SESSION_KEY] = code
    elif PROMO_SESSION_KEY in request.session:
        del request.session[PROMO_SESSION_KEY]
    request.session.modified = True


def clear_session_promo_code(request) -> None:
    set_session_promo_code(request, "")


def resolve_promo(request, subtotal: Decimal) -> dict:
    """Повертає {code, discount, error, promo} для поточного кошика."""
    code = get_session_promo_code(request)
    empty = {
        "code": "",
        "discount": Decimal("0"),
        "error": "",
        "promo": None,
        "total": max(subtotal, Decimal("0")),
    }
    if not code:
        return empty

    promo = PromoCode.objects.filter(code__iexact=code).first()
    if not promo:
        return {**empty, "code": code, "error": "Промокод не знайдено."}

    ok, error = promo.is_usable(subtotal)
    if not ok:
        return {**empty, "code": code, "error": error, "promo": promo}

    discount = promo.calc_discount(subtotal)
    total = subtotal - discount
    if total < 0:
        total = Decimal("0")
    return {
        "code": promo.code,
        "discount": discount,
        "error": "",
        "promo": promo,
        "total": total,
    }


def apply_promo_code(request, raw_code: str, subtotal: Decimal) -> dict:
    code = (raw_code or "").strip().upper()
    if not code:
        clear_session_promo_code(request)
        return {
            "ok": False,
            "code": "",
            "discount": Decimal("0"),
            "error": "Введіть промокод.",
            "total": subtotal,
        }

    promo = PromoCode.objects.filter(code__iexact=code).first()
    if not promo:
        clear_session_promo_code(request)
        return {
            "ok": False,
            "code": code,
            "discount": Decimal("0"),
            "error": "Промокод не знайдено.",
            "total": subtotal,
        }

    ok, error = promo.is_usable(subtotal)
    if not ok:
        clear_session_promo_code(request)
        return {
            "ok": False,
            "code": code,
            "discount": Decimal("0"),
            "error": error,
            "total": subtotal,
        }

    set_session_promo_code(request, promo.code)
    discount = promo.calc_discount(subtotal)
    return {
        "ok": True,
        "code": promo.code,
        "discount": discount,
        "error": "",
        "total": max(subtotal - discount, Decimal("0")),
    }
