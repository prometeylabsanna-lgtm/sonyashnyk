"""Адмінка динамічних фільтрів каталогу."""

from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from apps.core.admin_filters import (
    CleanBooleanDropdownFilter,
    TopDropdownFiltersMixin,
    horizontal_options_for,
)

from .filter_models import CatalogFilter, CatalogFilterCategory, CatalogFilterValue


class CatalogFilterValueInline(TabularInline):
    model = CatalogFilterValue
    extra = 1
    fields = ("value", "order", "is_active")
    ordering = ("order", "value")


class CatalogFilterCategoryInline(TabularInline):
    model = CatalogFilterCategory
    extra = 1
    autocomplete_fields = ("category",)
    fields = ("category", "is_enabled")
    ordering = ("category__order", "category__name")


@admin.register(CatalogFilter)
class CatalogFilterAdmin(TopDropdownFiltersMixin, ModelAdmin):
    list_display = ("name", "slug", "order", "is_active", "values_count", "bindings_count")
    list_editable = ("order", "is_active")
    list_filter = (("is_active", CleanBooleanDropdownFilter),)
    list_filter_options = horizontal_options_for(list_filter)
    search_fields = ("name", "name_ru", "slug")
    ordering = ("order", "name")
    prepopulated_fields = {"slug": ("name",)}
    fields = (
        "name", "name_ru", "slug", "order", "is_active", "use_country_labels",
    )
    inlines = [CatalogFilterValueInline, CatalogFilterCategoryInline]

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .prefetch_related("values", "category_bindings")
        )

    @admin.display(description="Значень")
    def values_count(self, obj):
        return obj.values.count()

    @admin.display(description="Категорій")
    def bindings_count(self, obj):
        return obj.category_bindings.filter(is_enabled=True).count()
