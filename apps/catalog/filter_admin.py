"""Адмінка довідника фільтрів каталогу."""

from django.contrib import admin
from unfold.admin import ModelAdmin

from apps.core.admin_filters import (
    CleanAllValuesDropdownFilter,
    CleanBooleanDropdownFilter,
    CleanRelatedDropdownFilter,
    TopDropdownFiltersMixin,
    horizontal_options_for,
)

from .filter_models import (
    BrandFilterOption,
    CategoryFilterSetting,
    CountryFilterOption,
    FilterType,
    PowerFilterOption,
    VolumeFilterOption,
)


class _FilterOptionAdmin(TopDropdownFiltersMixin, ModelAdmin):
    """База для proxy-значень фільтра."""

    filter_type = None
    list_display = ("value", "order", "is_active")
    list_editable = ("order", "is_active")
    list_filter = (("is_active", CleanBooleanDropdownFilter),)
    list_filter_options = horizontal_options_for(list_filter)
    search_fields = ("value",)
    ordering = ("order", "value")
    fields = ("value", "order", "is_active")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if self.filter_type:
            return qs.filter(filter_type=self.filter_type)
        return qs

    def save_model(self, request, obj, form, change):
        if self.filter_type:
            obj.filter_type = self.filter_type
        super().save_model(request, obj, form, change)

    def get_changeform_initial_data(self, request):
        data = super().get_changeform_initial_data(request)
        if self.filter_type:
            data["filter_type"] = self.filter_type
        return data


@admin.register(BrandFilterOption)
class BrandFilterOptionAdmin(_FilterOptionAdmin):
    filter_type = FilterType.BRAND


@admin.register(CountryFilterOption)
class CountryFilterOptionAdmin(_FilterOptionAdmin):
    filter_type = FilterType.COUNTRY


@admin.register(VolumeFilterOption)
class VolumeFilterOptionAdmin(_FilterOptionAdmin):
    filter_type = FilterType.VOLUME


@admin.register(PowerFilterOption)
class PowerFilterOptionAdmin(_FilterOptionAdmin):
    filter_type = FilterType.POWER


@admin.register(CategoryFilterSetting)
class CategoryFilterSettingAdmin(TopDropdownFiltersMixin, ModelAdmin):
    list_display = ("category", "filter_type", "is_enabled")
    list_editable = ("is_enabled",)
    list_filter = (
        ("filter_type", CleanAllValuesDropdownFilter),
        ("is_enabled", CleanBooleanDropdownFilter),
        ("category", CleanRelatedDropdownFilter),
    )
    list_filter_options = horizontal_options_for(list_filter)
    search_fields = ("category__name", "category__slug")
    autocomplete_fields = ("category",)
    ordering = ("category__order", "category__name", "filter_type")
    fields = ("category", "filter_type", "is_enabled")
