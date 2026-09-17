"""Template tags для SiteBlock CMS."""

from __future__ import annotations

import html
import re

from django import template
from django.utils.safestring import mark_safe

from apps.core.block_defaults import STATIC_FALLBACKS, get_block_default
from apps.core.i18n_utils import is_ru, loc, pick

register = template.Library()

_TAG_RE = re.compile(r"<[^>]+>")


def _blocks(context):
    return context.get("site_blocks") or {}


def _get_block(context, page, key):
    blocks = _blocks(context)
    return blocks.get(f"{page}.{key}")


def _default_for_lang(page: str, key: str) -> str:
    if is_ru():
        try:
            from apps.core.block_defaults_ru import get_block_default_ru

            ru = get_block_default_ru(page, key)
            if ru:
                return ru
        except Exception:
            pass
    return get_block_default(page, key)


def get_block_text(page, key, site_blocks=None, fallback=None):
    if site_blocks is None:
        site_blocks = {}
    block = site_blocks.get(f"{page}.{key}")
    if block is not None:
        if is_ru():
            ru = getattr(block, "text_html_ru", "") or ""
            if str(ru).strip():
                return ru
        if block.text_html not in (None, ""):
            return block.text_html
    if fallback is not None:
        if is_ru() and not (fallback or "").strip():
            return _default_for_lang(page, key)
        if is_ru():
            # fallback переданий як UK — спробувати RU дефолт
            ru_def = _default_for_lang(page, key)
            if ru_def and ru_def != get_block_default(page, key):
                return ru_def
        return fallback
    return _default_for_lang(page, key)


def is_section_visible(page, visibility_key, site_blocks=None) -> bool:
    # видимість не залежить від мови — беремо UK/основне поле
    if site_blocks is None:
        site_blocks = {}
    block = site_blocks.get(f"{page}.{visibility_key}")
    if block is not None and block.text_html not in (None, ""):
        value = block.text_html
    else:
        value = get_block_default(page, visibility_key) or "1"
    return value not in {"0", "false", "False", ""}


def html_to_plain(value: str) -> str:
    if not value:
        return ""
    text = value.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"(?i)<br\s*/?>", "\n", text)
    text = re.sub(r"(?i)</p\s*>", "\n", text)
    text = re.sub(r"(?i)<p[^>]*>", "", text)
    text = _TAG_RE.sub("", text)
    text = html.unescape(text)
    return text


@register.simple_tag(takes_context=True)
def section_visible(context, page, visibility_key):
    return is_section_visible(page, visibility_key, site_blocks=_blocks(context))


@register.simple_tag(takes_context=True)
def block_plain(context, page, key, fallback=None):
    raw = get_block_text(page, key, site_blocks=_blocks(context), fallback=fallback)
    plain = html_to_plain(raw)
    escaped = html.escape(plain)
    return mark_safe(escaped.replace("\n", "<br>"))


@register.simple_tag(takes_context=True)
def block_text(context, page, key, fallback=None):
    return get_block_text(page, key, site_blocks=_blocks(context), fallback=fallback)


@register.simple_tag(takes_context=True)
def block_html(context, page, key, fallback=None):
    raw = get_block_text(page, key, site_blocks=_blocks(context), fallback=fallback)
    return mark_safe(raw or "")


@register.simple_tag(takes_context=True)
def block_url(context, page, key, fallback=None):
    block = _get_block(context, page, key)
    if block is not None:
        if block.link_url:
            return block.link_url
        if block.text_html:
            return block.text_html
    if fallback is not None:
        return fallback
    return get_block_default(page, key)


@register.simple_tag(takes_context=True)
def block_url_label(context, page, key, fallback=None):
    block = _get_block(context, page, key)
    if block is not None:
        label = pick(block.link_label, getattr(block, "link_label_ru", ""))
        if label:
            return label
    if key.endswith("_link"):
        label_key = f"{key}_label"
        text = get_block_text(page, label_key, site_blocks=_blocks(context), fallback=None)
        if text:
            return text
    if fallback is not None:
        return fallback
    return ""


@register.inclusion_tag("includes/cms_block_image.html", takes_context=True)
def block_image(context, page, key, css_class="", alt="", fallback_static=None):
    block = _get_block(context, page, key)
    url = ""
    if block is not None and block.image:
        try:
            url = block.image.url
        except Exception:
            url = ""
    static_path = fallback_static or STATIC_FALLBACKS.get((page, key), "")
    return {
        "url": url,
        "static_path": static_path,
        "css_class": css_class,
        "alt": alt,
    }


@register.simple_tag(takes_context=True)
def block_format(context, page, key, fallback=None, **kwargs):
    raw = get_block_text(page, key, site_blocks=_blocks(context), fallback=fallback)
    try:
        return raw.format(**kwargs)
    except (KeyError, ValueError):
        return raw


@register.filter
def cms_lines(value):
    plain = html_to_plain(value or "")
    return mark_safe(html.escape(plain).replace("\n", "<br>"))


@register.filter
def cms_splitlines(value):
    return [line.strip() for line in html_to_plain(value or "").split("\n") if line.strip()]


@register.filter
def loc_field(obj, field_name):
    """{{ product|loc_field:'name' }}"""
    if obj is None:
        return ""
    return loc(obj, field_name)


@register.filter
def country_name(value):
    from apps.core.i18n_utils import country_label

    return country_label(value or "")
