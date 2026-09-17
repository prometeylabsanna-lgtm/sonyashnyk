"""Конвертація зображень у WebP (аплоади адмінки + static)."""

from __future__ import annotations

import logging
from io import BytesIO
from pathlib import Path

from django.core.files.base import ContentFile
from django.core.files.uploadedfile import UploadedFile
from PIL import Image, ImageOps

logger = logging.getLogger(__name__)

WEBP_QUALITY = 85
WEBP_METHOD = 6
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".tif", ".tiff", ".bmp", ".webp"}
SKIP_STATIC_NAMES = {
    "favicon.ico",
    "favicon-16x16.png",
    "favicon-32x32.png",
    "apple-touch-icon.png",
}


def _has_alpha(img: Image.Image) -> bool:
    if img.mode in ("RGBA", "LA"):
        return True
    if img.mode == "P" and "transparency" in img.info:
        return True
    return False


def prepare_image_for_webp(img: Image.Image) -> Image.Image:
    img = ImageOps.exif_transpose(img)
    if _has_alpha(img):
        return img.convert("RGBA")
    if img.mode != "RGB":
        return img.convert("RGB")
    return img


def image_to_webp_bytes(img: Image.Image, *, quality: int = WEBP_QUALITY) -> bytes:
    prepared = prepare_image_for_webp(img)
    buf = BytesIO()
    save_kwargs: dict = {
        "format": "WEBP",
        "method": WEBP_METHOD,
    }
    if prepared.mode == "RGBA":
        # прозорість (іконки/лого) — якісний lossy з alpha
        save_kwargs["quality"] = max(quality, 90)
    else:
        save_kwargs["quality"] = quality
    prepared.save(buf, **save_kwargs)
    return buf.getvalue()


def is_already_webp(name: str | None) -> bool:
    if not name:
        return False
    return Path(name).suffix.lower() == ".webp"


def convert_file_to_webp_content(
    source,
    *,
    original_name: str | None = None,
    quality: int = WEBP_QUALITY,
) -> ContentFile | None:
    """Повертає ContentFile(.webp) або None, якщо конвертація не потрібна / неможлива."""
    name = original_name or getattr(source, "name", "") or "image"
    if is_already_webp(name):
        return None

    try:
        if hasattr(source, "open"):
            try:
                source.open("rb")
            except Exception:
                pass
        if hasattr(source, "seek"):
            try:
                source.seek(0)
            except Exception:
                pass
        with Image.open(source) as img:
            data = image_to_webp_bytes(img, quality=quality)
    except Exception:
        logger.exception("Не вдалося конвертувати в WebP: %s", name)
        return None
    finally:
        if hasattr(source, "seek"):
            try:
                source.seek(0)
            except Exception:
                pass

    webp_name = f"{Path(name).stem}.webp"
    return ContentFile(data, name=webp_name)


def convert_path_to_webp(
    path: Path,
    *,
    quality: int = WEBP_QUALITY,
    delete_original: bool = True,
) -> Path | None:
    """Конвертує файл на диску → .webp поруч. Повертає шлях до webp."""
    if not path.is_file():
        return None
    if path.name in SKIP_STATIC_NAMES:
        return None
    if path.suffix.lower() not in IMAGE_EXTENSIONS - {".webp"}:
        if path.suffix.lower() == ".webp":
            return path
        return None

    dest = path.with_suffix(".webp")
    try:
        with Image.open(path) as img:
            data = image_to_webp_bytes(img, quality=quality)
        dest.write_bytes(data)
    except Exception:
        logger.exception("Static WebP fail: %s", path)
        return None

    if delete_original and dest != path and path.exists():
        path.unlink()
    return dest


def should_skip_static_path(path: Path) -> bool:
    return path.name in SKIP_STATIC_NAMES
