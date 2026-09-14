from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from .models import Category, Product, ProductImage, ProductVariant


@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    list_display = ("name", "erp_name", "parent", "order", "is_active", "has_custom_icon")
    list_filter = ("is_active", "parent")
    search_fields = ("name", "erp_name", "slug")
    ordering = ("order", "name")
    fields = (
        "name", "erp_name", "slug", "parent",
        "image", "description", "order", "is_active",
    )

    @admin.display(boolean=True, description="Своя іконка")
    def has_custom_icon(self, obj):
        return bool(obj.image)


class ProductVariantInline(TabularInline):
    model = ProductVariant
    extra = 1


class ProductImageInline(TabularInline):
    model = ProductImage
    extra = 1


@admin.register(Product)
class ProductAdmin(ModelAdmin):
    list_display = (
        "name", "sku", "category", "pack_volume", "base_price", "is_own_production",
        "is_hit", "is_new", "is_sale", "is_active",
    )
    list_filter = ("category", "is_own_production", "is_hit", "is_new", "is_sale", "is_active")
    search_fields = ("name", "sku", "pack_volume")
    inlines = [ProductVariantInline, ProductImageInline]
    fields = (
        "category", "sku", "name", "slug",
        "short_description", "description", "characteristics",
        "brand", "country_of_origin", "pack_volume",
        "base_price", "old_price",
        "is_own_production", "is_hit", "is_new", "is_sale", "is_active",
    )
