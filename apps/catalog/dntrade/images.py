"""Завантаження зображень товарів з CDN DNTrade."""

from __future__ import annotations

import logging
import urllib.error
import urllib.parse
import urllib.request
from io import BytesIO
from pathlib import Path

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db import transaction
from PIL import Image

from apps.catalog.models import Product, ProductImage
from apps.core.image_webp import image_to_webp_bytes, prepare_image_for_webp

logger = logging.getLogger(__name__)


def collect_image_urls(product_payload: dict) -> list[str]:
    urls: list[str] = []
    main = (product_payload.get("image_path") or "").strip()
    if main.startswith("http"):
        urls.append(main)
    for item in product_payload.get("images") or []:
        if not item:
            continue
        url = str(item).strip()
        if url.startswith("http") and url not in urls:
            urls.append(url)
    return urls


def _image_file_missing(img: ProductImage) -> bool:
    name = getattr(img.image, "name", "") or ""
    if not name:
        return True
    try:
        return not default_storage.exists(name)
    except Exception:
        return True


def sync_product_images(
    product: Product,
    product_payload: dict,
    *,
    dry_run: bool = False,
    force: bool = False,
) -> int:
    """Оновлює фото. Перекачує, якщо URL змінились, файлів немає на диску, або force=True."""
    urls = collect_image_urls(product_payload)
    existing = list(product.images.order_by("order", "id"))
    existing_urls = [img.source_url for img in existing if img.source_url]
    missing_files = any(_image_file_missing(img) for img in existing)

    if not force and existing_urls == urls and urls and not missing_files:
        return 0
    if not force and not urls and not existing:
        return 0

    if dry_run:
        return len(urls)

    downloaded = 0
    with transaction.atomic():
        product.images.all().delete()
        for order, url in enumerate(urls):
            content = _download_webp(url, product.sku or str(product.pk), order)
            if content is None:
                continue
            ProductImage.objects.create(
                product=product,
                image=content,
                source_url=url[:500],
                alt=product.name[:255],
                order=order,
            )
            downloaded += 1
    return downloaded


def _download_webp(url: str, sku: str, order: int) -> ContentFile | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "SonyashnykDNTradeSync/1.0"})
        with urllib.request.urlopen(req, timeout=45) as resp:
            raw = resp.read()
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        logger.warning("Не вдалося завантажити фото %s: %s", url, exc)
        return None

    try:
        img = Image.open(BytesIO(raw))
        img = prepare_image_for_webp(img)
        webp = image_to_webp_bytes(img)
    except Exception as exc:
        logger.warning("Не вдалося конвертувати фото %s: %s", url, exc)
        return None

    stem = Path(urllib.parse.urlparse(url).path).stem or f"{sku}-{order}"
    safe = "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in stem)[:80] or "img"
    return ContentFile(webp, name=f"{safe}.webp")
