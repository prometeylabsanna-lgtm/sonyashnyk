from django.contrib import admin
from unfold.admin import ModelAdmin

from apps.core.admin_filters import (
    CleanAllValuesDropdownFilter,
    CleanBooleanDropdownFilter,
    TopDropdownFiltersMixin,
    horizontal_options_for,
)

from .models import Certificate


@admin.register(Certificate)
class CertificateAdmin(TopDropdownFiltersMixin, ModelAdmin):
    list_display = ("title", "series", "product", "is_active", "order")
    list_filter = (
        ("is_active", CleanBooleanDropdownFilter),
        ("series", CleanAllValuesDropdownFilter),
    )
    list_filter_options = horizontal_options_for(list_filter)
    search_fields = ("title", "series")
    fields = ("title", "title_ru", "series", "series_ru", "file", "product", "is_active", "order")
