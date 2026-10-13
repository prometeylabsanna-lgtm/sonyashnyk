"""Створення адрес / клієнтів / відправлень Укрпошти (eCom)."""

from __future__ import annotations

import logging
import re
import urllib.parse
from decimal import Decimal
from typing import Any

from django.conf import settings

from .ukrposhta import (
    ECOM_BASE,
    UkrposhtaError,
    _bearer_ecom,
    _counterparty_token,
    _request_json,
    is_shipping_configured,
)

logger = logging.getLogger(__name__)

_PHONE_RE = re.compile(r"\D+")


def _token_q() -> str:
    return urllib.parse.quote(_counterparty_token(), safe="")


def _ecom(method: str, path: str, *, body: dict[str, Any] | None = None, with_token: bool = True) -> Any:
    url = f"{ECOM_BASE}{path}"
    if with_token:
        sep = "&" if "?" in url else "?"
        url = f"{url}{sep}token={_token_q()}"
    return _request_json(method, url, _bearer_ecom(), body=body)


def create_address(*, postcode: str, country: str = "UA", **extra: Any) -> int:
    postcode = (postcode or "").strip()
    if not postcode:
        raise UkrposhtaError("Немає поштового індексу")
    payload = {"postcode": postcode, "country": country, **{k: v for k, v in extra.items() if v}}
    data = _ecom("POST", "/addresses", body=payload, with_token=False)
    address_id = data.get("id") if isinstance(data, dict) else None
    if not address_id:
        raise UkrposhtaError("Не вдалося створити адресу")
    return int(address_id)


def _split_name(full_name: str) -> tuple[str, str, str]:
    parts = [p for p in (full_name or "").strip().split() if p]
    if len(parts) >= 3:
        return parts[0], parts[1], " ".join(parts[2:])
    if len(parts) == 2:
        return parts[0], parts[1], ""
    if len(parts) == 1:
        return parts[0], parts[0], ""
    return "Отримувач", "Отримувач", ""


def _normalize_phone(phone: str) -> str:
    digits = _PHONE_RE.sub("", phone or "")
    if digits.startswith("380") and len(digits) == 12:
        return digits
    if digits.startswith("0") and len(digits) == 10:
        return "38" + digits
    if len(digits) == 9:
        return "380" + digits
    return digits


def create_individual_client(*, full_name: str, phone: str, address_id: int, email: str = "") -> str:
    last_name, first_name, middle_name = _split_name(full_name)
    body: dict[str, Any] = {
        "type": "INDIVIDUAL",
        "firstName": first_name,
        "lastName": last_name,
        "addressId": address_id,
        "phoneNumber": _normalize_phone(phone),
        "resident": True,
    }
    if middle_name:
        body["middleName"] = middle_name
    if email:
        body["email"] = email
    data = _ecom("POST", "/clients", body=body)
    uuid = data.get("uuid") if isinstance(data, dict) else None
    if not uuid:
        raise UkrposhtaError("Не вдалося створити клієнта-одержувача")
    return str(uuid)


def create_shipment_for_order(order) -> dict[str, Any]:
    """W2W відправлення на відділення за індексом з замовлення."""
    if not is_shipping_configured():
        raise UkrposhtaError("Укрпошта (eCom) не налаштована — перевірте Bearer/token/sender UUID")

    postindex = (getattr(order, "up_postindex", "") or "").strip()
    if not postindex:
        raise UkrposhtaError("У замовленні немає індексу відділення Укрпошти")

    sender_uuid = (getattr(settings, "UKRPOSHTA_SENDER_UUID", "") or "").strip()
    weight = int(getattr(settings, "UKRPOSHTA_DEFAULT_WEIGHT", 1000) or 1000)
    length = int(getattr(settings, "UKRPOSHTA_DEFAULT_LENGTH", 30) or 30)
    shipment_type = (getattr(settings, "UKRPOSHTA_SHIPMENT_TYPE", "STANDARD") or "STANDARD").strip().upper()

    recipient_address_id = create_address(postcode=postindex)
    recipient_uuid = create_individual_client(
        full_name=order.full_name,
        phone=order.phone,
        address_id=recipient_address_id,
        email=(order.email or "").strip(),
    )

    body: dict[str, Any] = {
        "type": shipment_type if shipment_type in ("STANDARD", "EXPRESS") else "STANDARD",
        "sender": {"uuid": sender_uuid},
        "recipient": {"uuid": recipient_uuid},
        "deliveryType": "W2W",
        "paidByRecipient": False,
        "parcels": [{"weight": weight, "length": length}],
        "externalId": order.order_number,
        "description": f"Замовлення {order.order_number}",
    }

    sender_address_id = (getattr(settings, "UKRPOSHTA_SENDER_ADDRESS_ID", "") or "").strip()
    if sender_address_id:
        body["senderAddressId"] = int(sender_address_id)

    declared = Decimal(order.total or 0)
    if declared > 0:
        body["parcels"][0]["declaredPrice"] = float(declared)

    from .models import Order

    if order.payment_method == Order.PaymentMethod.COD and declared > 0:
        body["postPay"] = float(declared)
        body["postPayPaidByRecipient"] = True

    data = _ecom("POST", "/shipments", body=body)
    if not isinstance(data, dict) or not data.get("barcode"):
        raise UkrposhtaError("Відправлення створено без ШКІ")
    return {
        "uuid": str(data.get("uuid") or ""),
        "barcode": str(data.get("barcode") or ""),
        "delivery_price": data.get("deliveryPrice"),
        "raw": data,
    }


def sticker_url(shipment_uuid_or_barcode: str) -> str:
    """PDF ярлик — forms endpoint (відкривається в браузері з token у query)."""
    token = _token_q()
    key = urllib.parse.quote((shipment_uuid_or_barcode or "").strip(), safe="")
    return f"https://www.ukrposhta.ua/forms/ecom/0.0.1/shipments/{key}/sticker?token={token}"


def bootstrap_sender_client() -> dict[str, Any]:
    """Одноразове створення відправника з env (для management command)."""
    if not (_bearer_ecom() and _counterparty_token()):
        raise UkrposhtaError("Потрібні UKRPOSHTA_BEARER_ECOM і UKRPOSHTA_COUNTERPARTY_TOKEN")

    postcode = (getattr(settings, "UKRPOSHTA_SENDER_POSTCODE", "") or "").strip()
    phone = (getattr(settings, "UKRPOSHTA_SENDER_PHONE", "") or "").strip()
    client_type = (getattr(settings, "UKRPOSHTA_SENDER_TYPE", "PRIVATE_ENTREPRENEUR") or "").strip()
    name = (getattr(settings, "UKRPOSHTA_SENDER_NAME", "") or "").strip()
    if not postcode or not phone or not name:
        raise UkrposhtaError(
            "Задайте UKRPOSHTA_SENDER_POSTCODE, UKRPOSHTA_SENDER_PHONE, UKRPOSHTA_SENDER_NAME"
        )

    extra = {
        "region": (getattr(settings, "UKRPOSHTA_SENDER_REGION", "") or "").strip(),
        "city": (getattr(settings, "UKRPOSHTA_SENDER_CITY", "") or "").strip(),
        "street": (getattr(settings, "UKRPOSHTA_SENDER_STREET", "") or "").strip(),
        "houseNumber": (getattr(settings, "UKRPOSHTA_SENDER_HOUSE", "") or "").strip(),
        "apartmentNumber": (getattr(settings, "UKRPOSHTA_SENDER_APARTMENT", "") or "").strip(),
    }
    address_id = create_address(postcode=postcode, **extra)
    body: dict[str, Any] = {
        "type": client_type or "PRIVATE_ENTREPRENEUR",
        "name": name,
        "addressId": address_id,
        "phoneNumber": _normalize_phone(phone),
        "resident": True,
    }
    tin = (getattr(settings, "UKRPOSHTA_SENDER_TIN", "") or "").strip()
    edrpou = (getattr(settings, "UKRPOSHTA_SENDER_EDRPOU", "") or "").strip()
    email = (getattr(settings, "UKRPOSHTA_SENDER_EMAIL", "") or "").strip()
    if tin:
        body["tin"] = tin
    if edrpou:
        body["edrpou"] = edrpou
    if email:
        body["email"] = email

    data = _ecom("POST", "/clients", body=body)
    uuid = data.get("uuid") if isinstance(data, dict) else None
    if not uuid:
        raise UkrposhtaError("Не вдалося створити відправника")
    return {"uuid": str(uuid), "address_id": address_id, "raw": data}
