"""HTTP-клієнт DNTrade API з урахуванням rate-limit (100 req/хв)."""

from __future__ import annotations

import json
import logging
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from django.conf import settings

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "https://api.dntrade.com.ua"
PAGE_SIZE = 100
# 100 req/хв → тримаємо ~1.1 req/с з запасом
MIN_INTERVAL_SEC = 0.7


class DntradeApiError(Exception):
    def __init__(self, message: str, *, status_code: int | None = None, payload: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload


class DntradeClient:
    def __init__(
        self,
        api_key: str | None = None,
        *,
        base_url: str | None = None,
        timeout: int = 60,
    ):
        self.api_key = (api_key or getattr(settings, "DNTRADE_API_KEY", "") or "").strip()
        self.base_url = (base_url or getattr(settings, "DNTRADE_BASE_URL", "") or DEFAULT_BASE_URL).rstrip("/")
        self.timeout = timeout
        self._last_request_at = 0.0
        if not self.api_key:
            raise DntradeApiError("DNTRADE_API_KEY не задано в .env")

    def list_stores(self) -> list[dict]:
        data = self._request("GET", "/products/stores")
        return list(data.get("stores") or [])

    def list_categories(self, *, store_id: str | None = None) -> list[dict]:
        params: dict[str, Any] = {}
        if store_id:
            params["store_id"] = store_id
        data = self._request("GET", "/products/categories", params=params)
        return list(data.get("categories") or [])

    def iter_products(
        self,
        *,
        store_id: str | None = None,
        limit: int | None = None,
        offset: int = 0,
    ):
        """Пагінація /products/list (POST). yield dict товару."""
        fetched = 0
        page_offset = max(0, int(offset or 0))
        while True:
            page_limit = PAGE_SIZE
            if limit is not None:
                remaining = limit - fetched
                if remaining <= 0:
                    break
                page_limit = min(PAGE_SIZE, remaining)
            params: dict[str, Any] = {"limit": page_limit, "offset": page_offset}
            if store_id:
                params["store_id"] = store_id
            data = self._request("POST", "/products/list", params=params, body={})
            products = list(data.get("products") or [])
            if not products:
                break
            for item in products:
                yield item
                fetched += 1
                if limit is not None and fetched >= limit:
                    return
            if len(products) < page_limit:
                break
            page_offset += page_limit

    def iter_balances(self, *, store_id: str | None = None, limit: int | None = None):
        """Пагінація /products/balances (GET). yield dict залишку."""
        fetched = 0
        offset = 0
        while True:
            page_limit = PAGE_SIZE
            if limit is not None:
                remaining = limit - fetched
                if remaining <= 0:
                    break
                page_limit = min(PAGE_SIZE, remaining)
            params: dict[str, Any] = {"limit": page_limit, "offset": offset}
            if store_id:
                params["store_id"] = store_id
            data = self._request("GET", "/products/balances", params=params)
            # Swagger каже balances, фактично — products
            rows = list(data.get("products") or data.get("balances") or [])
            if not rows:
                break
            for item in rows:
                yield item
                fetched += 1
                if limit is not None and fetched >= limit:
                    return
            if len(rows) < page_limit:
                break
            offset += page_limit

    def _throttle(self) -> None:
        elapsed = time.monotonic() - self._last_request_at
        if elapsed < MIN_INTERVAL_SEC:
            time.sleep(MIN_INTERVAL_SEC - elapsed)

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        body: dict | None = None,
        retries: int = 3,
    ) -> dict:
        query = urllib.parse.urlencode({k: v for k, v in (params or {}).items() if v is not None})
        url = f"{self.base_url}{path}"
        if query:
            url = f"{url}?{query}"

        raw = None if body is None else json.dumps(body).encode("utf-8")
        headers = {
            "ApiKey": self.api_key,
            "Accept": "application/json",
        }
        if raw is not None:
            headers["Content-Type"] = "application/json"

        attempt = 0
        while True:
            attempt += 1
            self._throttle()
            req = urllib.request.Request(url, data=raw, headers=headers, method=method)
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    self._last_request_at = time.monotonic()
                    payload = json.loads(resp.read().decode("utf-8") or "{}")
            except urllib.error.HTTPError as exc:
                self._last_request_at = time.monotonic()
                retry_after = exc.headers.get("Retry-After") if exc.headers else None
                body_text = ""
                try:
                    body_text = exc.read().decode("utf-8", errors="replace")
                except Exception:
                    pass
                if exc.code == 429 and attempt <= retries:
                    wait = int(retry_after or 60)
                    logger.warning("DNTrade 429, чекаємо %ss", wait)
                    time.sleep(max(wait, 1))
                    continue
                raise DntradeApiError(
                    f"DNTrade HTTP {exc.code}: {body_text[:300]}",
                    status_code=exc.code,
                ) from exc
            except urllib.error.URLError as exc:
                self._last_request_at = time.monotonic()
                if attempt <= retries:
                    time.sleep(2 * attempt)
                    continue
                raise DntradeApiError(f"DNTrade мережа: {exc}") from exc

            if isinstance(payload, dict) and payload.get("status") == 0:
                raise DntradeApiError("DNTrade повернув status=0", payload=payload)
            return payload if isinstance(payload, dict) else {"data": payload}
