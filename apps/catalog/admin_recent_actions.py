"""Окрема адмін-сторінка: усі недавні дії (LogEntry)."""

from __future__ import annotations

from django.contrib import admin
from django.contrib.admin.models import ADDITION, CHANGE, DELETION, LogEntry
from django.shortcuts import render
from django.urls import path, reverse
from django.utils.html import format_html

RECENT_LIMIT = 100

_ACTION_LABELS = {
    ADDITION: ("Додано", "addition"),
    CHANGE: ("Змінено", "change"),
    DELETION: ("Видалено", "deletion"),
}


def _action_meta(flag: int) -> tuple[str, str]:
    return _ACTION_LABELS.get(flag, ("Дія", "other"))


def _content_type_label(entry: LogEntry) -> str:
    if not entry.content_type_id:
        return "—"
    name = entry.content_type.name or entry.content_type.model
    return str(name).capitalize()


def _object_link(entry: LogEntry) -> str:
    label = entry.object_repr or f"#{entry.object_id}"
    if entry.is_deletion() or not entry.object_id:
        return format_html('<span class="recent-actions__muted">{}</span>', label)
    try:
        url = entry.get_admin_url()
    except Exception:
        url = None
    if not url:
        return format_html("<span>{}</span>", label)
    return format_html('<a href="{}">{}</a>', url, label)


def recent_actions_view(request):
    entries = list(
        LogEntry.objects.select_related("user", "content_type")
        .order_by("-action_time")[:RECENT_LIMIT]
    )
    rows = []
    for entry in entries:
        label, css = _action_meta(entry.action_flag)
        rows.append(
            {
                "time": entry.action_time,
                "user": entry.user.get_username() if entry.user_id else "—",
                "action_label": label,
                "action_css": css,
                "content_type": _content_type_label(entry),
                "object_html": _object_link(entry),
                "message": entry.get_change_message() or "—",
            }
        )
    context = {
        **admin.site.each_context(request),
        "title": "Недавні дії",
        "rows": rows,
        "has_view_permission": True,
        "products_url": reverse("admin:catalog_product_changelist"),
    }
    return render(request, "admin/catalog/recent_product_actions.html", context)


def patch_admin_recent_actions_urls() -> None:
    """Підключити recent-product-actions під поточним префіксом адмінки."""
    if getattr(admin.site, "_sonyashnyk_recent_actions_patched", False):
        return
    original = admin.site.get_urls

    def get_urls():
        return [
            path(
                "recent-product-actions/",
                admin.site.admin_view(recent_actions_view),
                name="catalog_recent_product_actions",
            ),
            *original(),
        ]

    admin.site.get_urls = get_urls  # type: ignore[method-assign]
    admin.site._sonyashnyk_recent_actions_patched = True  # type: ignore[attr-defined]
