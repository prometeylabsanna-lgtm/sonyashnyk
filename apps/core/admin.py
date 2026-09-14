from django.contrib import admin

from .models import HeroSlide, HighlightPoint, Review, SiteSettings


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        (
            "Соцмережі",
            {
                "fields": ("instagram_url", "tiktok_url", "telegram_url"),
                "description": "Порожнє поле — іконка не показується у футері.",
            },
        ),
    )

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(HeroSlide)
class HeroSlideAdmin(admin.ModelAdmin):
    list_display = ("title", "order", "is_active")
    list_editable = ("order", "is_active")


@admin.register(HighlightPoint)
class HighlightPointAdmin(admin.ModelAdmin):
    list_display = ("title", "section", "icon", "order", "is_active")
    list_filter = ("section",)
    list_editable = ("order", "is_active")


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "rating", "order", "is_active")
    list_editable = ("order", "is_active")
