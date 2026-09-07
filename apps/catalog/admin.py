from django.contrib import admin

from .models import Category, Product, ProductImage, ProductVariant


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "erp_name", "parent", "order", "is_active")
    list_filter = ("is_active", "parent")
    search_fields = ("name", "erp_name", "slug")
    ordering = ("order", "name")


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name", "sku", "category", "base_price", "is_own_production",
        "is_hit", "is_new", "is_sale", "is_active",
    )
    list_filter = ("category", "is_own_production", "is_hit", "is_new", "is_sale", "is_active")
    search_fields = ("name", "sku")
    inlines = [ProductVariantInline, ProductImageInline]
