"""Інтеграція Monobank Acquiring (Monopay): invoice + webhook."""

from __future__ import annotations

import base64
import hashlib
import json
import logging
import urllib.error
import urllib.request
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from django.conf import settings
from django.core.cache import cache
from django.urls import reverse

from .access import make_order_access_token

logger = logging.getLogger(__name__)

API_BASE = "https://api.monobank.ua"
CREATE_INVOICE_URL = f"{API_BASE}/api/merchant/invoice/create"
PUBKEY_URL = f"{API_BASE}/api/merchant/pubkey"
CCY_UAH = 980
REQUEST_TIMEOUT = 20
PUBKEY_CACHE_KEY = "monopay:merchant_pubkey"
PUBKEY_CACHE_TTL = 3600

SUCCESS_STATUSES = frozenset({"success"})
FAILED_STATUSES = frozenset({"failure", "expired"})
REFUNDED_STATUSES = frozenset({"reversed"})


class MonopayError(Exception):
    """Помилка створення/обробки платежу Monopay."""


def is_configured() -> bool:
    return bool((getattr(settings, "MONOPAY_TOKEN", "") or "").strip())


def _site_url() -> str:
    url = (
        getattr(settings, "PUBLIC_BASE_URL", "")
        or getattr(settings, "SITE_URL", "")
        or "http://127.0.0.1:8000"
    )
    return str(url).rstrip("/")


def _token() -> str:
    token = (getattr(settings, "MONOPAY_TOKEN", "") or "").strip()
    if not token:
        raise MonopayError("MONOPAY_TOKEN не налаштований.")
    return token


def amount_to_kopiyky(total) -> int:
    amount = Decimal(total).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return int(amount * 100)


def _api_request(method: str, url: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    headers = {
        "X-Token": _token(),
        "Accept": "application/json",
    }
    raw = None
    if payload is not None:
        raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=raw, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            body = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        logger.warning("Monopay HTTP %s: %s", exc.code, detail)
        raise MonopayError(f"Monopay HTTP {exc.code}") from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        logger.warning("Monopay network error: %s", exc)
        raise MonopayError("Не вдалося звʼязатися з Monopay") from exc

    if not body:
        return {}
    try:
        data = json.loads(body)
    except json.JSONDecodeError as exc:
        raise MonopayError("Некоректна відповідь Monopay") from exc
    if not isinstance(data, dict):
        raise MonopayError("Некоректна відповідь Monopay")
    return data


def create_invoice(order) -> dict[str, str]:
    """Створює рахунок і повертає {invoice_id, page_url}."""
    if not is_configured():
        raise MonopayError("MONOPAY_TOKEN не налаштований.")

    access = make_order_access_token(order.order_number)
    thank_path = reverse("orders_checkout:thank_you", args=[order.order_number])
    payload = {
        "amount": amount_to_kopiyky(order.total),
        "ccy": CCY_UAH,
        "merchantPaymInfo": {
            "reference": order.order_number,
            "destination": f"Замовлення {order.order_number} — Соняшник",
            "comment": f"Замовлення {order.order_number}",
        },
        "redirectUrl": f"{_site_url()}{thank_path}?t={access}",
        "webHookUrl": f"{_site_url()}{reverse('orders_checkout:monopay_callback')}",
    }
    data = _api_request("POST", CREATE_INVOICE_URL, payload)
    invoice_id = (data.get("invoiceId") or "").strip()
    page_url = (data.get("pageUrl") or "").strip()
    if not invoice_id or not page_url:
        raise MonopayError("Monopay не повернув invoiceId/pageUrl")
    return {"invoice_id": invoice_id, "page_url": page_url}


def fetch_pubkey_pem() -> str:
    """Публічний ключ для перевірки X-Sign (base64 → PEM)."""
    cached = cache.get(PUBKEY_CACHE_KEY)
    if cached:
        return cached
    data = _api_request("GET", PUBKEY_URL)
    key_b64 = (data.get("key") or "").strip()
    if not key_b64:
        raise MonopayError("Порожній pubkey від Monopay")
    try:
        pem = base64.b64decode(key_b64).decode("utf-8")
    except (ValueError, UnicodeDecodeError) as exc:
        raise MonopayError("Некоректний pubkey від Monopay") from exc
    cache.set(PUBKEY_CACHE_KEY, pem, PUBKEY_CACHE_TTL)
    return pem


def verify_webhook(body: bytes, x_sign_b64: str) -> bool:
    """Перевірка ECDSA-підпису вебхука (X-Sign)."""
    if not body or not x_sign_b64 or not is_configured():
        return False
    try:
        import ecdsa
    except ImportError:
        logger.error("Пакет ecdsa не встановлений — неможливо перевірити webhook Monopay")
        return False
    try:
        pem = fetch_pubkey_pem()
        signature = base64.b64decode(x_sign_b64)
        vk = ecdsa.VerifyingKey.from_pem(pem)
        return bool(
            vk.verify(
                signature,
                body,
                sigdecode=ecdsa.util.sigdecode_der,
                hashfunc=hashlib.sha256,
            )
        )
    except Exception as exc:  # noqa: BLE001 — будь-яка помилка підпису = reject
        logger.warning("Monopay webhook signature invalid: %s", exc)
        return False


def map_status(mono_status: str) -> str | None:
    """Повертає Order.PaymentStatus або None для проміжних статусів."""
    status = (mono_status or "").strip().lower()
    if status in SUCCESS_STATUSES:
        return "paid"
    if status in FAILED_STATUSES:
        return "failed"
    if status in REFUNDED_STATUSES:
        return "refunded"
    return None


def amount_matches_order(payload: dict[str, Any], order) -> bool:
    """amount у копійках; ccy має бути 980 (UAH)."""
    ccy = payload.get("ccy")
    if ccy is not None and int(ccy) != CCY_UAH:
        return False
    raw = payload.get("finalAmount", payload.get("amount"))
    if raw is None:
        return False
    try:
        paid = int(raw)
    except (TypeError, ValueError):
        return False
    return paid == amount_to_kopiyky(order.total)


def resolve_order_number(payload: dict[str, Any]) -> str:
    ref = (payload.get("reference") or "").strip()
    if ref:
        return ref
    info = payload.get("merchantPaymInfo") or {}
    if isinstance(info, dict):
        return (info.get("reference") or "").strip()
    return ""
