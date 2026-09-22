from django.contrib import admin
from unfold.admin import ModelAdmin

from apps.core.admin_filters import (
    CleanChoicesDropdownFilter,
    TopDropdownFiltersMixin,
    horizontal_options_for,
)
from apps.core.admin_site_content_proxies import register_site_content_section_admins
from apps.core.admin_utils import ReadableUnfoldFieldsMixin, SingletonModelAdminMixin
from apps.core.models import HighlightPoint, Review, SiteSettings

# SiteBlock / HeroSlide / PickupPoint — не реєструємо як звичайний ModelAdmin (CMS).


@admin.register(SiteSettings)
class SiteSettingsAdmin(ReadableUnfoldFieldsMixin, SingletonModelAdminMixin, ModelAdmin):
    fieldsets = (
        (
            "Основне",
            {
                "fields": (
                    "site_name",
                    ("phone", "phone_raw"),
                    "email",
                    ("address", "address_ru"),
                    ("work_hours", "work_hours_ru"),
                    "free_shipping_threshold",
                    ("meta_description", "meta_description_ru"),
                ),
            },
        ),
        (
            "Соцмережі",
            {
                "fields": ("instagram_url", "tiktok_url", "telegram_url"),
                "description": "Порожнє поле — іконка без посилання. Показується у шапці, на сторінці контактів і в підвалі.",
            },
        ),
    )


@admin.register(HighlightPoint)
class HighlightPointAdmin(TopDropdownFiltersMixin, ModelAdmin):
    list_display = ("title", "section", "icon", "order", "is_active")
    list_filter = (
        ("section", CleanChoicesDropdownFilter),
    )
    list_filter_options = horizontal_options_for(list_filter)
    list_editable = ("order", "is_active")
    fields = ("section", "icon", "title", "title_ru", "text", "text_ru", "order", "is_active")


@admin.register(Review)
class ReviewAdmin(ModelAdmin):
    list_display = ("name", "city", "rating", "order", "is_active")
    list_editable = ("order", "is_active")
    fields = ("name", "city", "city_ru", "text", "text_ru", "rating", "order", "is_active")


register_site_content_section_admins()
