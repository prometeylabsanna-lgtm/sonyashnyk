"""Базові типи CMS registry."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from django.urls import reverse_lazy


@dataclass(frozen=True)
class FieldGroup:
    title: str
    keys: tuple[str, ...]
    description: str = ""


@dataclass(frozen=True)
class ContentSection:
    slug: str
    page_slug: str
    title: str
    blocks: tuple[tuple[str, str], ...]
    sidebar_title: str = ""
    sidebar_icon: str = "edit_note"
    preview_url: str = "/"
    description: str = ""
    visibility_key: str = ""
    field_groups: tuple[FieldGroup, ...] = ()
    admin_model_name: str = ""
    has_hero_slides: bool = False

    def __post_init__(self):
        if not self.admin_model_name:
            object.__setattr__(
                self,
                "admin_model_name",
                f"{self.page_slug}{self.slug}settings".replace("_", "").lower(),
            )


def _b(page: str, *keys: str) -> tuple[tuple[str, str], ...]:
    return tuple((page, k) for k in keys)
