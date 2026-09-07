from django.contrib import admin

from .models import HeroSlide, HighlightPoint, Review


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
    list_display = ("name", "rating", "order", "is_active")
    list_editable = ("order", "is_active")
