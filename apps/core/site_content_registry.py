"""Registry CMS-секцій → sidebar + proxy admin."""

from __future__ import annotations

from typing import Iterable

from django.urls import reverse_lazy

from apps.core.site_content_registry_base import ContentSection, FieldGroup, _b  # noqa: F401
from apps.core.site_content_registry_home import CONTENT_SECTIONS_HOME
from apps.core.site_content_registry_pages import CONTENT_SECTIONS_PAGES
from apps.core.site_content_registry_shop import CONTENT_SECTIONS_SHOP

CONTENT_SECTIONS: tuple[ContentSection, ...] = (
    CONTENT_SECTIONS_HOME + CONTENT_SECTIONS_PAGES + CONTENT_SECTIONS_SHOP
)


def get_section(page_slug: str, section_slug: str) -> ContentSection | None:
    for section in CONTENT_SECTIONS:
        if section.page_slug == page_slug and section.slug == section_slug:
            return section
    return None


def all_registry_block_keys() -> list[tuple[str, str]]:
    keys: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for section in CONTENT_SECTIONS:
        for pair in section.blocks:
            if pair not in seen:
                seen.add(pair)
                keys.append(pair)
    return keys


def build_content_sidebar_items() -> list[dict]:
    return [
        {
            "title": section.sidebar_title or section.title,
            "icon": section.sidebar_icon,
            "link": reverse_lazy(f"admin:core_{section.admin_model_name}_changelist"),
        }
        for section in CONTENT_SECTIONS
    ]


def iter_section_blocks(section: ContentSection) -> Iterable[tuple[str, str]]:
    return section.blocks
