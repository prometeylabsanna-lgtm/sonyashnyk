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
    """Роздрібна ціна. None — у фіді ціни немає, наявну в каталозі не затираємо.

    Порожня роздрібна в списку prices не ховає окреме поле price.
    Явний 0 у роздрібному рядку лишається 0.
    """
    rows = payload.get("prices")
    if isinstance(rows, list):
        for row in rows:
            if not isinstance(row, dict):
                continue
            title = str(row.get("price_title") or "").strip().lower()
            price_id = row.get("price_id")
            if price_id == RETAIL_PRICE_ID or title == RETAIL_PRICE_TITLE:
                parsed = optional_decimal(row.get("price"))
                if parsed is not None:
                    return parsed
                break
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


def parse_stock_qty(value: Any) -> int | None:
    """Ціле зі значення залишку. None — порожньо або не число, це не явний 0.

    Дробове (зокрема рядок «1.5») зрізається до цілого, а не перетворюється на 0.
    Від'ємне лишається від'ємним: нуль застосовується до суми, не до кожного складу.
    """
    if isinstance(value, bool) or value is None or value == "":
        return None
    try:
        number = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None
    if not number.is_finite():
        return None
    return int(number)


def stock_for(payload: dict, stock_map: dict[str, int]) -> int | None:
    """Відомий залишок або None, якщо його не можна вивести.

    Ключ у карті балансів — явна кількість, включно з 0.
    Немає ключа в непорожній карті — невідомо: наявний залишок не затираємо
    і не підставляємо payload.balance. Порожня карта (баланси не завантажені):
    лише явне поле balance.
    """
    pid = norm_id(payload.get("product_id"))
    if pid and pid in stock_map:
        return max(0, stock_map[pid])
    if stock_map:
        return None
    if "balance" not in payload:
        return None
    parsed = parse_stock_qty(payload.get("balance"))
    if parsed is None:
        return None
    return max(0, parsed)


def build_stock_map(client: DntradeClient, *, limit: int | None) -> dict[str, int]:
    """Сумарний залишок по всіх складах (негативні → 0 на рівні суми).

    Сам рядок товару в відповіді — явна наявність даних, навіть якщо сума 0.
    Товарів, яких у відповіді немає, у карту не додаємо.
    """
    result: dict[str, int] = {}
    for row in client.iter_balances(limit=limit):
        pid = norm_id(row.get("product_id"))
        if not pid:
            continue
        total = 0
        for store in row.get("stores") or []:
            parsed = parse_stock_qty(store.get("balance"))
            if parsed is None:
                continue
            total += parsed
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
