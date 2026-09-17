from django.contrib import admin
from django.db import models
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from unfold.admin import ModelAdmin, TabularInline

from apps.core.admin_filters import (
    CleanAllValuesDropdownFilter,
    CleanBooleanDropdownFilter,
    CleanRelatedDropdownFilter,
    ProductAvailabilityFilter,
    TopDropdownFiltersMixin,
    horizontal_options_for,
)
from apps.core.admin_utils import ImagePreviewMixin

from .forms import ProductAdminForm
from .icons import category_icon_caption, category_icon_url
from .models import Category, Product, ProductImage, ProductVariant


@admin.register(Category)
class CategoryAdmin(ImagePreviewMixin, TopDropdownFiltersMixin, ModelAdmin):
    list_display = ("name", "erp_name", "parent", "order", "is_active", "icon_thumb")
    list_filter = (
        ("is_active", CleanBooleanDropdownFilter),
        ("parent", CleanRelatedDropdownFilter),
    )
    list_filter_options = horizontal_options_for(list_filter)
    search_fields = ("name", "erp_name", "slug")
    ordering = ("order", "name")
    readonly_fields = ("image_preview",)
    fields = (
        "name", "erp_name", "slug", "parent",
        "image_preview", "image", "description", "order", "is_active",
    )
    preview_max_height = 96
    preview_max_width = 96

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related("parent")
        # Спочатку корені, далі за батьківською → менше плутанини в списку
        return qs.order_by(
            models.F("parent_id").asc(nulls_first=True),
            "parent__name",
            "order",
            "name",
        )

    def _preview_for_nav(self, obj):
        return bool(obj and obj.parent_id is None)

    def _icon_img_html(self, obj, *, size=40, show_caption=False):
        for_nav = self._preview_for_nav(obj)
        url = category_icon_url(obj, for_nav=for_nav)
        if not url:
            return "—"
        caption = ""
        if show_caption:
            caption = mark_safe(
                f'<div style="margin-top:6px;color:#6b7280;font-size:12px">'
                f"{category_icon_caption(obj, for_nav=for_nav)}</div>"
            )
        return format_html(
            '<img src="{}" alt="" width="{}" height="{}" '
            'style="width:{}px;height:{}px;object-fit:contain;'
            'border-radius:4px;background:#f3f4f6;padding:2px">'
            "{}",
            url,
            size,
            size,
            size,
            size,
            caption,
        )

    @admin.display(description="Превʼю")
    def image_preview(self, obj):
        return self._icon_img_html(obj, size=self.preview_max_height, show_caption=True)

    @admin.display(description="Іконка")
    def icon_thumb(self, obj):
        return self._icon_img_html(obj, size=40, show_caption=False)


class ProductVariantInline(TabularInline):
    model = ProductVariant
    extra = 1


class ProductImageInline(TabularInline):
    model = ProductImage
    extra = 1


@admin.register(Product)
class ProductAdmin(TopDropdownFiltersMixin, ModelAdmin):
    form = ProductAdminForm
    list_display = (
        "name", "sku", "category", "pack_volume", "power", "base_price",
        "is_own_production", "is_hit", "is_new", "is_sale", "is_active",
    )
    list_filter = (
        ("category", CleanRelatedDropdownFilter),
        ("brand", CleanAllValuesDropdownFilter),
        ("country_of_origin", CleanAllValuesDropdownFilter),
        ("power", CleanAllValuesDropdownFilter),
        ProductAvailabilityFilter,
        ("is_own_production", CleanBooleanDropdownFilter),
        ("is_hit", CleanBooleanDropdownFilter),
        ("is_new", CleanBooleanDropdownFilter),
        ("is_sale", CleanBooleanDropdownFilter),
        ("is_active", CleanBooleanDropdownFilter),
    )
    list_filter_options = horizontal_options_for(list_filter)
    search_fields = ("name", "sku", "pack_volume", "power", "brand", "country_of_origin")
    inlines = [ProductVariantInline, ProductImageInline]
    fields = (
        "category", "sku", "name", "slug",
        "short_description", "description", "characteristics",
        "brand", "country_of_origin", "pack_volume", "power",
        "base_price", "old_price",
        "is_own_production", "is_hit", "is_new", "is_sale", "is_active",
    )
