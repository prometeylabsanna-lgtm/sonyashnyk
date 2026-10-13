"""Клієнт API Укрпошти: адресний класифікатор + трекінг (production)."""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from django.conf import settings

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 12
ADDRESS_BASE = "https://www.ukrposhta.ua/address-classifier-ws"
TRACKING_BASE = "https://www.ukrposhta.ua/status-tracking/0.0.1"
ECOM_BASE = "https://www.ukrposhta.ua/ecom/0.0.1"


class UkrposhtaError(Exception):
    """Помилка API Укрпошти."""


def is_address_configured() -> bool:
    return bool((getattr(settings, "UKRPOSHTA_BEARER_ECOM", "") or "").strip())


def is_tracking_configured() -> bool:
    return bool((getattr(settings, "UKRPOSHTA_BEARER_STATUS", "") or "").strip())


def is_shipping_configured() -> bool:
    return bool(
        is_address_configured()
        and (getattr(settings, "UKRPOSHTA_COUNTERPARTY_TOKEN", "") or "").strip()
        and (getattr(settings, "UKRPOSHTA_SENDER_UUID", "") or "").strip()
    )


def _bearer_ecom() -> str:
    return (getattr(settings, "UKRPOSHTA_BEARER_ECOM", "") or "").strip()


def _bearer_status() -> str:
    return (getattr(settings, "UKRPOSHTA_BEARER_STATUS", "") or "").strip()


def _counterparty_token() -> str:
    return (getattr(settings, "UKRPOSHTA_COUNTERPARTY_TOKEN", "") or "").strip()


def _entries(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        return []
    entries = payload.get("Entries") or {}
    if not isinstance(entries, dict):
        return []
    entry = entries.get("Entry")
    if entry is None:
        return []
    if isinstance(entry, list):
        return [row for row in entry if isinstance(row, dict)]
    if isinstance(entry, dict):
        return [entry]
    return []


def _get_json(url: str, bearer: str, *, accept_empty: bool = False) -> dict[str, Any]:
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {bearer}",
            "Accept": "application/json",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        body = ""
        try:
            body = exc.read().decode("utf-8", errors="replace")[:500]
        except Exception:
            pass
        raise UkrposhtaError(f"HTTP {exc.code}: {body or exc.reason}") from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise UkrposhtaError(str(exc)) from exc

    if not raw.strip():
        if accept_empty:
            return {}
        raise UkrposhtaError("Порожня відповідь API")
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise UkrposhtaError("Некоректний JSON від API") from exc


def _request_json(
    method: str,
    url: str,
    bearer: str,
    *,
    body: dict[str, Any] | None = None,
) -> Any:
    data = None
    headers = {
        "Authorization": f"Bearer {bearer}",
        "Accept": "application/json",
    }
    if body is not None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            raw = resp.read().decode("utf-8")
            if not raw.strip():
                return {}
            return json.loads(raw)
    except urllib.error.HTTPError as exc:
        err_body = ""
        try:
            err_body = exc.read().decode("utf-8", errors="replace")[:800]
        except Exception:
            pass
        raise UkrposhtaError(f"HTTP {exc.code}: {err_body or exc.reason}") from exc
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise UkrposhtaError(str(exc)) from exc


def search_cities(query: str, limit: int = 20) -> dict[str, Any]:
    query = (query or "").strip()
    if not is_address_configured():
        return {"ok": False, "fallback": True, "error": "", "items": []}
    if len(query) < 2:
        return {"ok": True, "fallback": False, "error": "", "items": []}

    params = urllib.parse.urlencode({"city_ua": query})
    url = f"{ADDRESS_BASE}/get_city_by_region_id_and_district_id_and_city_ua?{params}"
    try:
        payload = _get_json(url, _bearer_ecom(), accept_empty=True)
    except UkrposhtaError as exc:
        logger.warning("ukrposhta cities: %s", exc)
        return {"ok": False, "fallback": False, "error": str(exc), "items": []}

    items = []
    seen: set[str] = set()
    for row in _entries(payload):
        city_id = str(row.get("CITY_ID") or "").strip()
        name = (row.get("CITY_UA") or "").strip()
        region = (row.get("REGION_UA") or "").strip()
        district = (row.get("DISTRICT_UA") or "").strip()
        region_id = str(row.get("REGION_ID") or "").strip()
        if not city_id or not name or city_id in seen:
            continue
        seen.add(city_id)
        label = name
        if district and district != name:
            label = f"{name}, {district}"
        if region and region != name:
            label = f"{label}, {region}"
        items.append({
            "ref": city_id,
            "name": label,
            "region_id": region_id,
            "city_name": name,
        })
        if len(items) >= limit:
            break
    return {"ok": True, "fallback": False, "error": "", "items": items}


def search_warehouses(city_ref: str, query: str = "", *, region_id: str = "", limit: int = 50) -> dict[str, Any]:
    city_ref = (city_ref or "").strip()
    if not is_address_configured():
        return {"ok": False, "fallback": True, "error": "", "items": []}
    if not city_ref:
        return {"ok": True, "fallback": False, "error": "", "items": []}

    params: dict[str, str] = {"city_id": city_ref}
    region_id = (region_id or "").strip()
    if region_id:
        params["region_id"] = region_id
    url = f"{ADDRESS_BASE}/get_postoffices_by_city_id?{urllib.parse.urlencode(params)}"
    try:
        payload = _get_json(url, _bearer_ecom(), accept_empty=True)
    except UkrposhtaError as exc:
        logger.warning("ukrposhta warehouses: %s", exc)
        return {"ok": False, "fallback": False, "error": str(exc), "items": []}

    q = (query or "").strip().lower()
    items = []
    for row in _entries(payload):
        postindex = str(row.get("POSTINDEX") or row.get("TECHINDEX") or "").strip()
        short = (row.get("PO_SHORT") or "").strip()
        long_name = (row.get("PO_LONG") or "").strip()
        address = (row.get("ADDRESS") or "").strip()
        lock = str(row.get("LOCK_CODE") or "0").strip()
        available = str(row.get("AVALIBLE") or row.get("AVAILABLE") or "1").strip()
        if not postindex:
            continue
        if lock not in ("", "0") and available == "0":
            continue
        name = short or long_name or f"Відділення {postindex}"
        if address:
            name = f"{name} — {address} ({postindex})"
        else:
            name = f"{name} ({postindex})"
        if q and q not in name.lower() and q not in postindex:
            continue
        items.append({
            "ref": postindex,
            "name": name,
            "postindex": postindex,
            "city_id": str(row.get("CITY_ID") or city_ref),
            "region_id": str(row.get("REGION_ID") or region_id),
        })
        if len(items) >= limit:
            break
    return {"ok": True, "fallback": False, "error": "", "items": items}


def warehouse_exists(city_ref: str, postindex: str, *, region_id: str = "") -> bool:
    """Fail-open при збої API; False якщо відповідь успішна і індексу немає."""
    city_ref = (city_ref or "").strip()
    postindex = (postindex or "").strip()
    if not is_address_configured() or not postindex:
        return False

    params = urllib.parse.urlencode({"postindex": postindex})
    url = f"{ADDRESS_BASE}/get_postoffices_by_city_id?{params}"
    try:
        payload = _get_json(url, _bearer_ecom(), accept_empty=True)
    except UkrposhtaError:
        return True

    rows = _entries(payload)
    if not rows:
        listed = search_warehouses(city_ref, region_id=region_id, limit=100)
        if listed.get("fallback") or not listed.get("ok"):
            return True
        return any(item.get("ref") == postindex for item in listed.get("items") or [])

    for row in rows:
        pi = str(row.get("POSTINDEX") or row.get("TECHINDEX") or "").strip()
        if pi == postindex:
            if city_ref and str(row.get("CITY_ID") or "").strip() not in ("", city_ref):
                continue
            return True
    return False


def track_barcode(barcode: str) -> dict[str, Any]:
    barcode = (barcode or "").strip()
    if not barcode:
        raise UkrposhtaError("Порожній ШКІ")
    if is_tracking_configured():
        params = urllib.parse.urlencode({"barcode": barcode})
        url = f"{TRACKING_BASE}/statuses?{params}"
        payload = _get_json(url, _bearer_status())
        return {"source": "status-tracking", "barcode": barcode, "data": payload}

    if is_shipping_configured():
        token = urllib.parse.quote(_counterparty_token(), safe="")
        url = f"{ECOM_BASE}/shipments/{urllib.parse.quote(barcode, safe='')}/lifecycle?token={token}"
        payload = _request_json("GET", url, _bearer_ecom())
        return {"source": "ecom-lifecycle", "barcode": barcode, "data": payload}

    raise UkrposhtaError("Трекінг не налаштовано")


def summarize_tracking(payload: dict[str, Any]) -> str:
    data = payload.get("data")
    if isinstance(data, list) and data:
        last = data[-1] if isinstance(data[-1], dict) else {}
        event = last.get("eventName") or last.get("name") or last.get("status") or ""
        date = last.get("date") or last.get("eventDate") or ""
        return f"{event} {date}".strip() or "Отримано статуси"
    if isinstance(data, dict):
        status = data.get("status") or (data.get("lifecycle") or {}).get("status") or ""
        date = data.get("statusDate") or (data.get("lifecycle") or {}).get("statusDate") or ""
        return f"{status} {date}".strip() or "Отримано статус"
    return "Немає даних трекінгу"
