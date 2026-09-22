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
    return mark_safe(render_cms_rich(raw or ""))


@register.simple_tag(takes_context=True)
def block_rich(context, page, key, fallback=None):
    """HTML з TinyMCE або legacy-текст із абзацами."""
    raw = get_block_text(page, key, site_blocks=_blocks(context), fallback=fallback)
    return mark_safe(render_cms_rich(raw or ""))


def render_cms_rich(value: str) -> str:
    if not value:
        return ""
    text = value.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not text:
        return ""
    if _TAG_RE.search(text):
        return sanitize_cms_html(text)
    parts = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if not parts:
        parts = [text]
    if len(parts) == 1 and "\n" not in parts[0]:
        sentences = _split_sentences(parts[0])
        if len(sentences) > 1:
            parts = sentences
    out = []
    for part in parts:
        escaped = html.escape(part.replace("\n", " ").strip())
        if escaped:
            out.append(f"<p>{escaped}</p>")
    return "".join(out)


_SENTENCE_SPLIT_RE = re.compile(
    r"(?<=[.!?…])[\"»”']?\)?\s+(?=[A-ZА-ЯЁЇІЄҐ])"
)


def _split_sentences(text: str) -> list[str]:
    parts = [p.strip() for p in _SENTENCE_SPLIT_RE.split(text) if p and p.strip()]
    return parts or [text]


_ALLOWED_TAGS = {
    "p", "br", "strong", "b", "em", "i", "u", "ul", "ol", "li",
    "a", "h2", "h3", "h4", "span",
}
_ALLOWED_ATTRS = {"a": {"href", "title", "target", "rel"}}


def sanitize_cms_html(value: str) -> str:
    """Мінімальна санітизація HTML зі штатного TinyMCE (без сторонніх пакетів)."""
    from html.parser import HTMLParser

    class _Sanitizer(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.parts: list[str] = []

        def handle_starttag(self, tag, attrs):
            tag = tag.lower()
            if tag not in _ALLOWED_TAGS:
                return
            if tag == "br":
                self.parts.append("<br>")
                return
            allowed = _ALLOWED_ATTRS.get(tag, set())
            chunks = [tag]
            for name, val in attrs:
                name = (name or "").lower()
                if name not in allowed or val is None:
                    continue
                if name == "href" and not re.match(r"^(https?:|/|#|mailto:)", val, re.I):
                    continue
                if name == "target" and val not in {"_blank", "_self"}:
                    continue
                chunks.append(f'{name}="{html.escape(val, quote=True)}"')
                if name == "target" and val == "_blank":
                    chunks.append('rel="noopener noreferrer"')
            self.parts.append("<" + " ".join(chunks) + ">")

        def handle_endtag(self, tag):
            tag = tag.lower()
            if tag in _ALLOWED_TAGS and tag != "br":
                self.parts.append(f"</{tag}>")

        def handle_data(self, data):
            self.parts.append(html.escape(data))

        def handle_entityref(self, name):
            self.parts.append(f"&{name};")

        def handle_charref(self, name):
            self.parts.append(f"&#{name};")

    parser = _Sanitizer()
    try:
        parser.feed(value)
        parser.close()
    except Exception:
        return html.escape(html_to_plain(value)).replace("\n", "<br>")
    return "".join(parser.parts)

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
def block_image_url(context, page, key, fallback_static=None):
    """URL фото SiteBlock або static-fallback (для CSS background)."""
    from django.templatetags.static import static

    block = _get_block(context, page, key)
    if block is not None and block.image:
        try:
            return block.image.url
        except Exception:
            pass
    static_path = fallback_static or STATIC_FALLBACKS.get((page, key), "")
    if static_path:
        return static(static_path)
    return ""


@register.simple_tag(takes_context=True)
def block_format(context, page, key, fallback=None, **kwargs):
    raw = get_block_text(page, key, site_blocks=_blocks(context), fallback=fallback)
    try:
        return raw.format(**kwargs)
    except (KeyError, ValueError):
        return raw


@register.filter
def cms_rich(value):
    """Фільтр: plain → <p>, HTML TinyMCE → санітизований HTML."""
    return mark_safe(render_cms_rich(value or ""))


@register.filter
def cms_lines(value):
    plain = html_to_plain(value or "")
    return mark_safe(html.escape(plain).replace("\n", "<br>"))


@register.filter
def cms_splitlines(value):
    return [line.strip() for line in html_to_plain(value or "").split("\n") if line.strip()]


@register.simple_tag(takes_context=True)
def cms_numbered_items(context, page, prefix, count=12):
    """Список непорожніх SiteBlock з ключами prefix_1 … prefix_N."""
    items = []
    site_blocks = _blocks(context)
    has_blocks = any(
        f"{page}.{prefix}_{i}" in site_blocks for i in range(1, int(count) + 1)
    )
    if has_blocks:
        for i in range(1, int(count) + 1):
            text = get_block_text(page, f"{prefix}_{i}", site_blocks, fallback="")
            plain = html_to_plain(text or "").strip()
            if plain:
                items.append(plain)
        return items

    if prefix == "shelves_item":
        legacy = site_blocks.get(f"{page}.shelves_list")
        if legacy is not None:
            return [
                line.strip()
                for line in html_to_plain(
                    get_block_text(page, "shelves_list", site_blocks, fallback="") or ""
                ).split("\n")
                if line.strip()
            ]
        for i in range(1, int(count) + 1):
            plain = html_to_plain(_default_for_lang(page, f"{prefix}_{i}") or "").strip()
            if plain:
                items.append(plain)
    return items


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
