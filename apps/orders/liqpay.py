"""Інтеграція LiqPay (Client-Server checkout + server callback).

Підпис за офіційними прикладами SDK: base64(sha1(private_key + data + private_key)).
Без ключів у .env працює mock-оплата для локальної перевірки sandbox-флоу.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
from decimal import Decimal
from typing import Any

from django.conf import settings
from django.urls import reverse


CHECKOUT_URL = "https://www.liqpay.ua/api/3/checkout"
SUCCESS_STATUSES = frozenset({"success"})
FAILED_STATUSES = frozenset({"failure", "error", "reversed"})


def is_configured() -> bool:
    return bool(settings.LIQPAY_PUBLIC_KEY and settings.LIQPAY_PRIVATE_KEY)


def _site_url() -> str:
    return (getattr(settings, "SITE_URL", "") or "http://127.0.0.1:8000").rstrip("/")


def encode_data(params: dict[str, Any]) -> str:
    payload = json.dumps(params, ensure_ascii=False, separators=(",", ":"))
    return base64.b64encode(payload.encode("utf-8")).decode("ascii")


def sign_data(data: str, private_key: str | None = None) -> str:
    key = private_key if private_key is not None else settings.LIQPAY_PRIVATE_KEY
    raw = f"{key}{data}{key}".encode("utf-8")
    digest = hashlib.sha1(raw).digest()
    return base64.b64encode(digest).decode("ascii")


def verify_signature(data: str, signature: str) -> bool:
    if not data or not signature or not settings.LIQPAY_PRIVATE_KEY:
        return False
    expected = sign_data(data)
    return hmac.compare_digest(expected, signature)


def decode_data(data: str) -> dict[str, Any]:
    raw = base64.b64decode(data.encode("ascii"))
    return json.loads(raw.decode("utf-8"))


def build_payment_params(order) -> dict[str, Any]:
    """Параметри платежу для order (без data/signature)."""
    amount = Decimal(order.total).quantize(Decimal("0.01"))
    params: dict[str, Any] = {
        "version": 3,
        "public_key": settings.LIQPAY_PUBLIC_KEY,
        "action": "pay",
        "amount": str(amount),
        "currency": "UAH",
        "description": f"Замовлення {order.order_number} — Соняшник",
        "order_id": order.order_number,
        "result_url": f"{_site_url()}{reverse('orders_checkout:thank_you', args=[order.order_number])}",
        "server_url": f"{_site_url()}{reverse('orders_checkout:liqpay_callback')}",
        "language": "uk",
    }
    if settings.LIQPAY_SANDBOX:
        params["sandbox"] = 1
    return params


def build_checkout_form(order) -> dict[str, str]:
    """Повертає {url, data, signature} для auto-submit форми."""
    if not is_configured():
        raise RuntimeError("LiqPay ключі не налаштовані.")
    params = build_payment_params(order)
    data = encode_data(params)
    return {
        "url": CHECKOUT_URL,
        "data": data,
        "signature": sign_data(data),
    }


def map_status(liqpay_status: str) -> str | None:
    """Повертає Order.PaymentStatus або None якщо статус проміжний."""
    status = (liqpay_status or "").strip().lower()
    if status in SUCCESS_STATUSES:
        return "paid"
    if status in FAILED_STATUSES:
        return "failed"
    return None
