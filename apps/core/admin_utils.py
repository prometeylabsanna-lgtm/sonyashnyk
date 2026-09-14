"""Mixins для Unfold admin."""

from django.contrib import admin
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.html import format_html

from apps.core.admin_site_content_widgets import apply_readable_widget
from apps.core.models import SiteSettings


class SingletonModelAdminMixin:
    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        obj = SiteSettings.get_solo()
        return redirect(reverse(f"admin:{obj._meta.app_label}_{self.model._meta.model_name}_change", args=[obj.pk]))


class ReadableUnfoldFieldsMixin:
    def formfield_for_dbfield(self, db_field, request, **kwargs):
        formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
        if formfield is not None and getattr(formfield, "widget", None) is not None:
            formfield.widget = apply_readable_widget(formfield.widget)
        return formfield


class ImagePreviewMixin:
    @admin.display(description="Превʼю")
    def image_preview(self, obj):
        image = getattr(obj, "image", None)
        if not image:
            return "—"
        try:
            url = image.url
        except Exception:
            return "—"
        return format_html(
            '<img src="{}" alt="" style="max-height:80px;max-width:120px;object-fit:cover;border-radius:4px">',
            url,
        )
