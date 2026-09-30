"""Синхронізація каталогу сайту з DNTrade."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Any

from django.conf import settings
from django.utils import timezone

from apps.catalog.models import Product, ProductVariant

from .categories import CategoryResolver, is_excluded_category
from .client import DntradeClient
from .images import sync_product_images

logger = logging.getLogger(__name__)

RETAIL_PRICE_ID = 2
RETAIL_PRICE_TITLE = "роздрібна"
# Склад «Перемоги 5» — асортимент для сайту (без електро/буд офлайн).
DEFAULT_CATALOG_STORE_ID = "9043f685-1aa5-49d5-af2d-c8777cf814f5"


@dataclass
class DntradeSyncStats:
    products_fetched: int = 0
    products_created: int = 0
    products_updated: int = 0
    variants_upserted: int = 0
    images_downloaded: int = 0
    skipped: int = 0
    skipped_excluded: int = 0
    purged: int = 0
    errors: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "products_fetched": self.products_fetched,
            "products_created": self.products_created,
            "products_updated": self.products_updated,
            "variants_upserted": self.variants_upserted,
            "images_downloaded": self.images_downloaded,
            "skipped": self.skipped,
            "skipped_excluded": self.skipped_excluded,
            "purged": self.purged,
            "errors": list(self.errors[:50]),
        }


def sync_catalog(
    *,
    client: DntradeClient | None = None,
    store_id: str | None = None,
    dry_run: bool = False,
    limit: int | None = None,
    offset: int = 0,
    skip_images: bool = False,
    force_images: bool = False,
    purge_missing: bool = False,
    progress=None,
) -> DntradeSyncStats:
    """Повний імпорт: товари, варіанти (parent_id), ціни, залишки, контент, фото."""
    stats = DntradeSyncStats()
    client = client or DntradeClient()
    store_id = (
        (store_id or getattr(settings, "DNTRADE_STORE_ID", "") or "").strip()
        or DEFAULT_CATALOG_STORE_ID
    )
    categories = CategoryResolver()
    categories.ensure_import_category()

    if progress:
        progress(f"Завантаження товарів з DNTrade (store={store_id})…")
    raw_products = list(client.iter_products(store_id=store_id, limit=limit, offset=offset))
    stats.products_fetched = len(raw_products)

    products: list[dict] = []
    for payload in raw_products:
        if is_excluded_category(payload.get("category")):
            stats.skipped_excluded += 1
            continue
        products.append(payload)

    if progress:
        progress(
            f"Товарів з API: {len(raw_products)}, після виключень: {len(products)}, "
            f"відсіяно груп: {stats.skipped_excluded}. Завантаження залишків…"
        )
    # При --limit не тягнемо всі баланси (інший порядок у API) — беремо balance з товару.
    if limit is None:
        stock_map = _build_stock_map(client, limit=None)
    else:
        stock_map = {}
        for payload in products:
            pid = _norm_id(payload.get("product_id"))
            if not pid:
                continue
            try:
                stock_map[pid] = max(0, int(payload.get("balance") or 0))
            except (TypeError, ValueError):
                stock_map[pid] = 0

    by_id = {str(p.get("product_id") or "").upper(): p for p in products if p.get("product_id")}
    children_by_parent: dict[str, list[dict]] = {}
    for payload in products:
        parent_id = _norm_id(payload.get("parent_id"))
        if parent_id:
            children_by_parent.setdefault(parent_id, []).append(payload)

    for payload in products:
        pid = _norm_id(payload.get("product_id"))
        if not pid:
            continue
        for mod in payload.get("modifications") or []:
            mid = _norm_id(mod.get("product_id"))
            if mid and mid in by_id:
                kids = children_by_parent.setdefault(pid, [])
                if by_id[mid] not in kids:
                    kids.append(by_id[mid])

    child_ids = { _norm_id(c.get("product_id")) for kids in children_by_parent.values() for c in kids }
    roots = [
        p for p in products
        if _norm_id(p.get("product_id")) and _norm_id(p.get("product_id")) not in child_ids
        and not _norm_id(p.get("parent_id"))
    ]

    seen_ids: set[str] = set()
    for idx, payload in enumerate(roots, start=1):
        pid = _norm_id(payload.get("product_id"))
        if pid:
            seen_ids.add(pid)
        for child in children_by_parent.get(pid, []):
            cid = _norm_id(child.get("product_id"))
            if cid:
                seen_ids.add(cid)
        try:
            _sync_root_product(
                payload,
                children=children_by_parent.get(_norm_id(payload.get("product_id")), []),
                stock_map=stock_map,
                categories=categories,
                stats=stats,
                dry_run=dry_run,
                skip_images=skip_images,
                force_images=force_images,
            )
        except Exception as exc:
            msg = f"{payload.get('code')}/{payload.get('sku')}: {exc}"
            logger.exception("DNTrade sync error: %s", msg)
            stats.errors.append(msg)
        if progress and idx % 100 == 0:
            progress(f"Оброблено коренів: {idx}/{len(roots)}")

    if purge_missing and limit is None and offset == 0:
        stats.purged = _purge_missing_products(seen_ids, dry_run=dry_run, progress=progress)

    return stats


def _purge_missing_products(
    seen_ids: set[str],
    *,
    dry_run: bool,
    progress=None,
) -> int:
    """Видаляє товари з dntrade_product_id, яких немає в поточному імпорті."""
    qs = Product.objects.exclude(dntrade_product_id="").exclude(dntrade_product_id__isnull=True)
    to_delete = []
    for pid, pk in qs.values_list("dntrade_product_id", "pk"):
        if _norm_id(pid) not in seen_ids:
            to_delete.append(pk)
    if progress:
        progress(f"До видалення (поза Перемоги / виключені групи): {len(to_delete)}")
    if dry_run or not to_delete:
        return len(to_delete)
    # Пачками, щоб не тримати гігантський queryset
    deleted = 0
    batch = 500
    for i in range(0, len(to_delete), batch):
        chunk = to_delete[i : i + batch]
        n, _ = Product.objects.filter(pk__in=chunk).delete()
        deleted += n
    return len(to_delete)


def _sync_root_product(
    payload: dict,
    *,
    children: list[dict],
    stock_map: dict[str, int],
    categories: CategoryResolver,
    stats: DntradeSyncStats,
    dry_run: bool,
    skip_images: bool,
    force_images: bool = False,
) -> None:
    title = (payload.get("title") or "").strip()
    if not title:
        stats.skipped += 1
        return

    sku = resolve_sku(payload)
    product_id = _norm_id(payload.get("product_id"))
    code = _parse_code(payload.get("code"))
    category = categories.resolve(payload.get("category"))
    price = retail_price(payload)
    stock = stock_for(payload, stock_map)
    is_active = int(payload.get("status") or 0) == 1
    short_description = (payload.get("short_description") or "")[:255]
    description = payload.get("description") or ""
    pack_volume = (payload.get("unit_title") or "")[:80]

    if dry_run:
        stats.products_updated += 1
        stats.variants_upserted += max(1, len(children))
        return

    product, created = _upsert_product(
        product_id=product_id,
        code=code,
        sku=sku,
        title=title,
        category=category,
        price=price,
        short_description=short_description,
        description=description,
        pack_volume=pack_volume,
        is_active=is_active,
    )
    if created:
        stats.products_created += 1
    else:
        stats.products_updated += 1

    if children:
        seen_variant_ids: set[int] = set()
        for order, child in enumerate(children):
            variant = _upsert_variant_from_child(
                product,
                child,
                stock_map=stock_map,
                order=order,
                is_default=(order == 0),
            )
            seen_variant_ids.add(variant.pk)
            stats.variants_upserted += 1
        # зайві варіанти без dntrade_id не чіпаємо; з dntrade_id яких немає — обнуляємо stock
        product.variants.exclude(pk__in=seen_variant_ids).exclude(
            dntrade_product_id__isnull=True,
        ).exclude(dntrade_product_id="").update(stock_qty=0, is_default=False)
        if not product.variants.filter(is_default=True).exists():
            first = product.variants.order_by("order", "id").first()
            if first:
                first.is_default = True
                first.save(update_fields=["is_default"])
    else:
        _upsert_default_variant(product, sku=sku, price=price, stock=stock, code=code, product_id=product_id)
        stats.variants_upserted += 1

    if not skip_images:
        stats.images_downloaded += sync_product_images(
            product, payload, dry_run=False, force=force_images,
        )


def _upsert_product(
    *,
    product_id: str,
    code: int | None,
    sku: str,
    title: str,
    category,
    price: Decimal,
    short_description: str,
    description: str,
    pack_volume: str,
    is_active: bool,
) -> tuple[Product, bool]:
    product = _find_product(product_id=product_id, sku=sku, code=code)
    created = product is None
    if created:
        product = Product(
            sku=_unique_sku(sku),
            category=category,
            base_price=price,
            name=title,
            is_new=True,
        )

    product.dntrade_product_id = product_id or product.dntrade_product_id
    product.dntrade_code = code
    product.name = title[:255]
    product.category = category
    product.base_price = price
    product.short_description = short_description
    product.description = description
    product.pack_volume = pack_volume
    product.is_active = is_active
    product.dntrade_synced_at = timezone.now()
    # SKU не міняємо для існуючих, якщо вже заданий і збігається по id
    if created or not product.sku:
        product.sku = _unique_sku(sku, exclude_pk=product.pk if product.pk else None)
    product.save()
    return product, created


def _upsert_default_variant(
    product: Product,
    *,
    sku: str,
    price: Decimal,
    stock: int,
    code: int | None,
    product_id: str,
) -> ProductVariant:
    variant = product.variants.filter(is_default=True).first()
    if variant is None:
        variant = product.variants.order_by("order", "id").first()
    if variant is None:
        variant = ProductVariant(product=product, label=product.pack_volume or "1 шт", is_default=True)

    variant.label = (product.pack_volume or variant.label or "1 шт")[:80]
    variant.sku_variant = sku[:64]
    variant.price = price
    variant.stock_qty = max(0, stock)
    variant.dntrade_product_id = product_id
    variant.dntrade_code = code
    variant.is_default = True
    variant.order = 0
    variant.save()
    product.variants.exclude(pk=variant.pk).update(is_default=False)
    return variant


def _upsert_variant_from_child(
    product: Product,
    child: dict,
    *,
    stock_map: dict[str, int],
    order: int,
    is_default: bool,
) -> ProductVariant:
    child_id = _norm_id(child.get("product_id"))
    code = _parse_code(child.get("code"))
    sku = resolve_sku(child)
    label = (child.get("title") or child.get("unit_title") or sku or "варіант")[:80]
    price = retail_price(child)
    stock = stock_for(child, stock_map)

    variant = None
    if child_id:
        variant = ProductVariant.objects.filter(dntrade_product_id=child_id).first()
    if variant is None and sku:
        variant = product.variants.filter(sku_variant=sku).first()
    if variant is None and code is not None:
        variant = product.variants.filter(dntrade_code=code).first()
    if variant is None:
        variant = ProductVariant(product=product)

    variant.product = product
    variant.label = label
    variant.sku_variant = sku[:64]
    variant.price = price
    variant.stock_qty = max(0, stock)
    variant.dntrade_product_id = child_id
    variant.dntrade_code = code
    variant.is_default = is_default
    variant.order = order
    variant.save()
    return variant


def _find_product(*, product_id: str, sku: str, code: int | None) -> Product | None:
    if product_id:
        found = Product.objects.filter(dntrade_product_id=product_id).first()
        if found:
            return found
    if sku:
        found = Product.objects.filter(sku=sku).first()
        if found:
            return found
    if code is not None:
        found = Product.objects.filter(dntrade_code=code).first()
        if found:
            return found
        found = Product.objects.filter(sku=str(code)).first()
        if found:
            return found
    return None


def _unique_sku(sku: str, exclude_pk: int | None = None) -> str:
    base = (sku or "item")[:64]
    candidate = base
    n = 2
    qs = Product.objects.all()
    while qs.filter(sku=candidate).exclude(pk=exclude_pk).exists():
        suffix = f"-{n}"
        candidate = f"{base[:64 - len(suffix)]}{suffix}"
        n += 1
    return candidate


def resolve_sku(payload: dict) -> str:
    sku = (payload.get("sku") or "").strip()
    if sku:
        return sku[:64]
    code = payload.get("code")
    if code is not None and str(code).strip() != "":
        return str(code)[:64]
    pid = _norm_id(payload.get("product_id"))
    return (pid or "unknown")[:64]


def retail_price(payload: dict) -> Decimal:
    for row in payload.get("prices") or []:
        title = str(row.get("price_title") or "").strip().lower()
        price_id = row.get("price_id")
        if price_id == RETAIL_PRICE_ID or title == RETAIL_PRICE_TITLE:
            return _to_decimal(row.get("price"))
    return _to_decimal(payload.get("price"))


def stock_for(payload: dict, stock_map: dict[str, int]) -> int:
    pid = _norm_id(payload.get("product_id"))
    if pid and pid in stock_map:
        return max(0, stock_map[pid])
    try:
        return max(0, int(payload.get("balance") or 0))
    except (TypeError, ValueError):
        return 0


def _build_stock_map(client: DntradeClient, *, limit: int | None) -> dict[str, int]:
    """Сумарний залишок по всіх складах (негативні → 0 на рівні суми)."""
    result: dict[str, int] = {}
    for row in client.iter_balances(limit=limit):
        pid = _norm_id(row.get("product_id"))
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


def _norm_id(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip().upper()


def _parse_code(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _to_decimal(value: Any) -> Decimal:
    try:
        return Decimal(str(value if value is not None else "0")).quantize(Decimal("0.01"))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal("0.00")
