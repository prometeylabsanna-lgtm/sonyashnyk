"""Віджети адмінки каталогу."""

import json

from django import forms
from django.forms.utils import flatatt
from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe


class CharacteristicsKeyValueWidget(forms.Widget):
    """Рядки «назва → значення» замість сирого JSON."""

    template_name = None  # рендер вручну — сумісність з Unfold

    class Media:
        css = {"all": ("css/admin/characteristics_kv.css",)}
        js = ("js/admin/characteristics_kv.js",)

    def format_value(self, value):
        if value in (None, "", {}, []):
            return []
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except (TypeError, ValueError, json.JSONDecodeError):
                return []
        if isinstance(value, dict):
            return [(str(k), "" if v is None else str(v)) for k, v in value.items()]
        return []

    def value_from_datadict(self, data, files, name):
        keys = data.getlist(f"{name}_key")
        vals = data.getlist(f"{name}_value")
        result = {}
        for key, val in zip(keys, vals):
            key = (key or "").strip()
            if not key:
                continue
            result[key] = (val or "").strip()
        return result

    def render(self, name, value, attrs=None, renderer=None):
        pairs = self.format_value(value)
        if not pairs:
            pairs = [("", "")]

        final_attrs = self.build_attrs(attrs or {})
        widget_id = final_attrs.get("id") or f"id_{name}"
        rows_html = format_html_join(
            "",
            (
                '<div class="char-kv__row" data-char-kv-row>'
                '<input type="text" name="{}_key" value="{}" '
                'placeholder="Назва (напр. Тип)" autocomplete="off" class="char-kv__input">'
                '<span class="char-kv__arrow" aria-hidden="true">→</span>'
                '<input type="text" name="{}_value" value="{}" '
                'placeholder="Значення (напр. овочеве)" autocomplete="off" class="char-kv__input">'
                '<button type="button" class="char-kv__remove" data-char-kv-remove '
                'aria-label="Видалити рядок">×</button>'
                "</div>"
            ),
            ((name, key, name, val) for key, val in pairs),
        )
        return format_html(
            '<div class="char-kv" id="{}" data-char-kv data-char-kv-name="{}"{}>'
            '<div class="char-kv__rows" data-char-kv-rows>{}</div>'
            '<button type="button" class="char-kv__add" data-char-kv-add>+ Додати характеристику</button>'
            '<p class="char-kv__hint">Пишіть звичайним текстом: зліва назва, справа значення. '
            "Без JSON і лапок.</p>"
            "</div>",
            widget_id,
            name,
            mark_safe(flatatt({k: v for k, v in final_attrs.items() if k != "id"})),
            rows_html,
        )
