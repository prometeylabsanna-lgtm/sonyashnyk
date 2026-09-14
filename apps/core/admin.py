from django.contrib import admin
from unfold.admin import ModelAdmin

from apps.core.admin_site_content_proxies import register_site_content_section_admins
from apps.core.admin_utils import ReadableUnfoldFieldsMixin, SingletonModelAdminMixin
from apps.core.models import HighlightPoint, Review, SiteSettings

# SiteBlock / HeroSlide — не реєструємо як звичайний ModelAdmin (CMS proxy).


@admin.register(SiteSettings)
class SiteSettingsAdmin(ReadableUnfoldFieldsMixin, SingletonModelAdminMixin, ModelAdmin):
    fieldsets = (
        (
            "Основне",
            {
                "fields": (
                    "site_name",
                    "phone",
                    "phone_raw",
                    "email",
                    "address",
                    "work_hours",
                    "free_shipping_threshold",
                    "meta_description",
                ),
            },
        ),
        (
            "Соцмережі",
            {
                "fields": ("instagram_url", "tiktok_url", "telegram_url"),
                "description": "Порожнє поле — іконка не показується у футері.",
            },
        ),
    )


@admin.register(HighlightPoint)
class HighlightPointAdmin(ModelAdmin):
    list_display = ("title", "section", "icon", "order", "is_active")
    list_filter = ("section",)
    list_editable = ("order", "is_active")


@admin.register(Review)
class ReviewAdmin(ModelAdmin):
    list_display = ("name", "city", "rating", "order", "is_active")
    list_editable = ("order", "is_active")


register_site_content_section_admins()
