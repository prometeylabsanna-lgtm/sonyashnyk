"""Клієнт API Нової Пошти з ручним fallback, коли ключ порожній."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from django.conf import settings

NP_API_URL = "https://api.novaposhta.ua/v2.0/json/"
REQUEST_TIMEOUT = 12


def is_configured() -> bool:
    return bool((settings.NOVA_POSHTA_API_KEY or "").strip())


def _post(model: str, method: str, props: dict[str, Any]) -> dict[str, Any]:
    body = {
        "apiKey": settings.NOVA_POSHTA_API_KEY,
        "modelName": model,
        "calledMethod": method,
        "methodProperties": props,
    }
    req = urllib.request.Request(
        NP_API_URL,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return {"ok": False, "fallback": False, "error": str(exc), "items": []}

    if not payload.get("success"):
        errors = payload.get("errors") or payload.get("errorCodes") or ["NP API error"]
        return {"ok": False, "fallback": False, "error": "; ".join(map(str, errors)), "items": []}
    return {"ok": True, "fallback": False, "error": "", "data": payload.get("data") or []}


def search_cities(query: str, limit: int = 20) -> dict[str, Any]:
    query = (query or "").strip()
    if not is_configured():
        return {"ok": False, "fallback": True, "error": "", "items": []}
    if len(query) < 2:
        return {"ok": True, "fallback": False, "error": "", "items": []}

    result = _post("Address", "searchSettlements", {"CityName": query, "Limit": str(limit)})
    if not result.get("ok"):
        return {**result, "items": []}

    items = []
    for block in result.get("data") or []:
        for row in block.get("Addresses") or []:
            ref = row.get("DeliveryCity") or row.get("Ref") or ""
            present = row.get("Present") or row.get("MainDescription") or ""
            if not ref or not present:
                continue
            items.append({"ref": ref, "name": present})
            if len(items) >= limit:
                break
        if len(items) >= limit:
            break
    return {"ok": True, "fallback": False, "error": "", "items": items}


def search_warehouses(
    city_ref: str,
    query: str = "",
    *,
    kind: str = "branch",
    limit: int = 50,
) -> dict[str, Any]:
    """kind: branch | locker."""
    city_ref = (city_ref or "").strip()
    if not is_configured():
        return {"ok": False, "fallback": True, "error": "", "items": []}
    if not city_ref:
        return {"ok": True, "fallback": False, "error": "", "items": []}

    props: dict[str, Any] = {
        "CityRef": city_ref,
        "Limit": str(limit),
    }
    q = (query or "").strip()
    if q:
        props["FindByString"] = q

    result = _post("Address", "getWarehouses", props)
    if not result.get("ok"):
        return {**result, "items": []}

    items = []
    for row in result.get("data") or []:
        category = (row.get("CategoryOfWarehouse") or "").strip()
        is_locker = category.lower() == "postomat" or "поштомат" in (row.get("Description") or "").lower()
        if kind == "locker" and not is_locker:
            continue
        if kind == "branch" and is_locker:
            continue
        ref = row.get("Ref") or ""
        name = row.get("Description") or row.get("DescriptionRu") or ""
        if not ref or not name:
            continue
        items.append({"ref": ref, "name": name})
        if len(items) >= limit:
            break
    return {"ok": True, "fallback": False, "error": "", "items": items}
