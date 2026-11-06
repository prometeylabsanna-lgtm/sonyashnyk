"""Розбір полів товару DNTrade: SKU, ціна, залишок, статус."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

from .client import DntradeClient

RETAIL_PRICE_ID = 2
RETAIL_PRICE_TITLE = "роздрібна"


def resolve_sku(payload: dict) -> str:
    sku = (payload.get("sku") or "").strip()
    if sku:
        return sku[:64]
    code = payload.get("code")
    if code is not None and str(code).strip() != "":
        return str(code)[:64]
    pid = norm_id(payload.get("product_id"))
    return (pid or "unknown")[:64]


def retail_price(payload: dict) -> Decimal | None:
    """Роздрібна ціна. None — у фіді ціни немає, наявну в каталозі не затираємо."""
    rows = payload.get("prices")
    if isinstance(rows, list):
        for row in rows:
            if not isinstance(row, dict):
                continue
            title = str(row.get("price_title") or "").strip().lower()
            price_id = row.get("price_id")
            if price_id == RETAIL_PRICE_ID or title == RETAIL_PRICE_TITLE:
                return optional_decimal(row.get("price"))
    if "price" in payload:
        return optional_decimal(payload.get("price"))
    return None


def payload_is_active(payload: dict) -> bool | None:
    """None — status у фіді відсутній або порожній, прапор на сайті не змінюємо."""
    if "status" not in payload:
        return None
    raw = payload.get("status")
    if raw is None or raw == "":
        return None
    try:
        return int(raw) == 1
    except (TypeError, ValueError):
        return None


def stock_for(payload: dict, stock_map: dict[str, int]) -> int:
    pid = norm_id(payload.get("product_id"))
    if pid and pid in stock_map:
        return max(0, stock_map[pid])
    try:
        return max(0, int(payload.get("balance") or 0))
    except (TypeError, ValueError):
        return 0


def build_stock_map(client: DntradeClient, *, limit: int | None) -> dict[str, int]:
    """Сумарний залишок по всіх складах (негативні → 0 на рівні суми)."""
    result: dict[str, int] = {}
    for row in client.iter_balances(limit=limit):
        pid = norm_id(row.get("product_id"))
        if not pid:
            continue
        total = 0
        for store in row.get("stores") or []:
            try:
                total += int(store.get("balance") or 0)
            except (TypeError, ValueError):
                continue
        result[pid] = max(0, total)
    return result


def norm_id(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip().upper()


def parse_code(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def optional_decimal(value: Any) -> Decimal | None:
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value)).quantize(Decimal("0.01"))
    except (InvalidOperation, TypeError, ValueError):
        return None
