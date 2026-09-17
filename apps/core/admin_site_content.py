"""Динамічна CMS-форма секції + view."""

from __future__ import annotations

from django import forms
from django.contrib import messages
from django.core.cache import cache
from django.shortcuts import redirect, render
from django.urls import reverse
from unfold.widgets import UnfoldAdminFileFieldWidget, UnfoldBooleanWidget

from apps.core.admin_guidelines import help_for_key, help_for_section
from apps.core.admin_hero_slides import build_hero_slide_formset
from apps.core.admin_site_content_widgets import CmsAdminTextInputWidget, CmsAdminTextareaWidget
from apps.core.block_defaults import (
    INLINE_KEYS,
    MULTILINE_KEYS,
    get_block_content_type,
    get_block_default,
    get_block_label,
    is_visibility_key,
)
from apps.core.models import SiteBlock, SiteSettings
from apps.core.site_content_registry import get_section

SITE_BLOCKS_CACHE_KEY = "sonyashnyk_site_blocks_v1"


def load_section_blocks(page: str, keys: list[str]) -> dict[str, SiteBlock]:
    result: dict[str, SiteBlock] = {}
    for key in keys:
        defaults = {
            "label": get_block_label(page, key),
            "content_type": get_block_content_type(page, key),
            "text_html": get_block_default(page, key),
        }
        try:
            from apps.core.block_defaults_ru import get_block_default_ru

            defaults["text_html_ru"] = get_block_default_ru(page, key)
        except Exception:
            pass
        block, _ = SiteBlock.objects.get_or_create(page=page, key=key, defaults=defaults)
        result[key] = block
    return result


class SitePageContentForm(forms.Form):
    def __init__(self, *args, section=None, blocks=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.section = section
        self.blocks = blocks or {}
        if section.visibility_key:
            block = self.blocks.get(section.visibility_key)
            initial = True
            if block is not None:
                initial = block.text_html not in {"0", "false", "False", ""}
            self.fields["section_visible"] = forms.BooleanField(
                required=False,
                initial=initial,
                label="Показувати секцію на сайті",
                widget=UnfoldBooleanWidget(),
            )

        for page, key in section.blocks:
            if section.visibility_key and key == section.visibility_key:
                continue
            block = self.blocks[key]
            ctype = get_block_content_type(page, key)
            label = block.label or get_block_label(page, key)
            help_text = help_for_key(key, page=page)

            if is_visibility_key(key):
                self.fields[f"block__{page}__{key}__visible"] = forms.BooleanField(
                    required=False,
                    initial=block.text_html not in {"0", "false", "False", ""},
                    label=label,
                    help_text=help_text,
                    widget=UnfoldBooleanWidget(),
                )
                continue

            if ctype == "image":
                self.fields[f"block__{page}__{key}__image"] = forms.ImageField(
                    required=False,
                    label=label,
                    help_text=help_text,
                    widget=UnfoldAdminFileFieldWidget(),
                )
                continue

            if ctype == "url":
                self.fields[f"block__{page}__{key}__link_url"] = forms.CharField(
                    required=False,
                    initial=block.link_url or block.text_html or get_block_default(page, key),
                    label=label,
                    help_text=help_text,
                    widget=CmsAdminTextInputWidget(),
                )
                continue

            pair = (page, key)
            if pair in INLINE_KEYS:
                widget = CmsAdminTextInputWidget()
            elif pair in MULTILINE_KEYS:
                widget = CmsAdminTextareaWidget(attrs={"rows": 6})
            else:
                widget = CmsAdminTextareaWidget(attrs={"rows": 2})
            self.fields[f"block__{page}__{key}__text_html"] = forms.CharField(
                required=False,
                initial=block.text_html,
                label=label,
                help_text=help_text,
                widget=widget,
            )
            if pair in INLINE_KEYS:
                ru_widget = CmsAdminTextInputWidget()
            elif pair in MULTILINE_KEYS:
                ru_widget = CmsAdminTextareaWidget(attrs={"rows": 6})
            else:
                ru_widget = CmsAdminTextareaWidget(attrs={"rows": 2})
            self.fields[f"block__{page}__{key}__text_html_ru"] = forms.CharField(
                required=False,
                initial=getattr(block, "text_html_ru", "") or "",
                label=f"{label} (RU)",
                help_text="Російська версія. Порожнє = український текст.",
                widget=ru_widget,
            )

    def save(self):
        section = self.section
        if section.visibility_key:
            visible = self.cleaned_data.get("section_visible", True)
            block = self.blocks[section.visibility_key]
            block.text_html = "1" if visible else "0"
            block.content_type = SiteBlock.ContentType.TEXT
            block.save(update_fields=["text_html", "content_type"])

        for name, value in self.cleaned_data.items():
            if not name.startswith("block__"):
                continue
            parts = name.split("__")
            if len(parts) != 4:
                continue
            _, page, key, suffix = parts
            block = self.blocks[key]
            if suffix == "visible":
                block.text_html = "1" if value else "0"
                block.save(update_fields=["text_html"])
            elif suffix == "text_html":
                block.text_html = value or ""
                block.save(update_fields=["text_html"])
            elif suffix == "text_html_ru":
                block.text_html_ru = value or ""
                block.save(update_fields=["text_html_ru"])
            elif suffix == "image":
                if value:
                    block.image = value
                    block.content_type = SiteBlock.ContentType.IMAGE
                    block.save(update_fields=["image", "content_type"])
            elif suffix == "link_url":
                block.link_url = value or ""
                block.content_type = SiteBlock.ContentType.URL
                block.text_html = value or ""
                block.save(update_fields=["link_url", "content_type", "text_html"])

        cache.delete(SITE_BLOCKS_CACHE_KEY)


def site_content_section_view(request, page_slug: str, section_slug: str, model_admin=None):
    section = get_section(page_slug, section_slug)
    if section is None:
        messages.error(request, "Секцію не знайдено.")
        return redirect("admin:index")

    keys = [key for _, key in section.blocks]
    blocks = load_section_blocks(section.page_slug, keys)
    hero_formset = None

    if request.method == "POST":
        form = SitePageContentForm(request.POST, request.FILES, section=section, blocks=blocks)
        if section.has_hero_slides:
            hero_formset = build_hero_slide_formset(data=request.POST, files=request.FILES)
        ok = form.is_valid() and (hero_formset is None or hero_formset.is_valid())
        if ok:
            form.save()
            if hero_formset is not None:
                hero_formset.save()
            messages.success(request, "Збережено.")
            return redirect(request.path)
    else:
        form = SitePageContentForm(section=section, blocks=blocks)
        if section.has_hero_slides:
            hero_formset = build_hero_slide_formset()

    field_groups = []
    for group in section.field_groups:
        bound = []
        for key in group.keys:
            if section.visibility_key and key == section.visibility_key:
                if "section_visible" in form.fields:
                    bound.append(form["section_visible"])
                continue
            page = section.page_slug
            ctype = get_block_content_type(page, key)
            if is_visibility_key(key):
                name = f"block__{page}__{key}__visible"
            elif ctype == "image":
                name = f"block__{page}__{key}__image"
            elif ctype == "url":
                name = f"block__{page}__{key}__link_url"
            else:
                name = f"block__{page}__{key}__text_html"
            if name in form.fields:
                bound.append(form[name])
                # image preview from current block
        field_groups.append({"title": group.title, "description": group.description, "fields": bound, "keys": group.keys})

    image_previews = {
        key: (blocks[key].image.url if blocks[key].image else "")
        for key in keys
        if get_block_content_type(section.page_slug, key) == "image" and key in blocks
    }

    context = {
        **(model_admin.admin_site.each_context(request) if model_admin else {}),
        "title": section.title,
        "section": section,
        "section_hint": help_for_section(section.page_slug, section.slug),
        "form": form,
        "field_groups": field_groups,
        "image_previews": image_previews,
        "blocks_map": blocks,
        "hero_formset": hero_formset,
        "opts": SiteSettings._meta,
        "has_view_permission": True,
        "has_change_permission": True,
        "preview_url": section.preview_url,
        "media": form.media,
    }
    if hero_formset is not None:
        context["media"] += hero_formset.media
    return render(request, "admin/core/site_content_page.html", context)
