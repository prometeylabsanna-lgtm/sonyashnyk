from django.contrib import admin
from django.utils.html import format_html
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

    @admin.display(description="Іконка")
    def icon_thumb(self, obj):
        if not obj.image:
            return "—"
        try:
            url = obj.image.url
        except Exception:
            return "—"
        return format_html(
            '<img src="{}" alt="" width="40" height="40" '
            'style="width:40px;height:40px;object-fit:contain;'
            'border-radius:4px;background:#f3f4f6;padding:2px">',
            url,
        )


class ProductVariantInline(TabularInline):
    model = ProductVariant
    extra = 1


class ProductImageInline(TabularInline):
    model = ProductImage
    extra = 1


@admin.register(Product)
class ProductAdmin(TopDropdownFiltersMixin, ModelAdmin):
    list_display = (
        "name", "sku", "category", "pack_volume", "base_price", "is_own_production",
        "is_hit", "is_new", "is_sale", "is_active",
    )
    list_filter = (
        ("category", CleanRelatedDropdownFilter),
        ("brand", CleanAllValuesDropdownFilter),
        ("country_of_origin", CleanAllValuesDropdownFilter),
        ProductAvailabilityFilter,
        ("is_own_production", CleanBooleanDropdownFilter),
        ("is_hit", CleanBooleanDropdownFilter),
        ("is_new", CleanBooleanDropdownFilter),
        ("is_sale", CleanBooleanDropdownFilter),
        ("is_active", CleanBooleanDropdownFilter),
    )
    list_filter_options = horizontal_options_for(list_filter)
    search_fields = ("name", "sku", "pack_volume", "brand", "country_of_origin")
    inlines = [ProductVariantInline, ProductImageInline]
    fields = (
        "category", "sku", "name", "slug",
        "short_description", "description", "characteristics",
        "brand", "country_of_origin", "pack_volume",
        "base_price", "old_price",
        "is_own_production", "is_hit", "is_new", "is_sale", "is_active",
    )
