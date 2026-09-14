from django.contrib import admin
from django.utils.html import format_html

from .models import Lead


class NewLeadsFilter(admin.SimpleListFilter):
    title = "Нові"
    parameter_name = "only_new"

    def lookups(self, request, model_admin):
        return (("1", "Лише нові"),)

    def queryset(self, request, queryset):
        if self.value() == "1":
            return queryset.filter(status=Lead.Status.NEW)
        return queryset


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ("created_at", "lead_type", "name", "phone", "status_badge", "product")
    list_filter = (NewLeadsFilter, "lead_type", "status")
    search_fields = ("name", "phone", "email")
    fields = (
        "status", "lead_type", "name", "phone", "email", "message",
        "product", "source_page", "created_at",
    )
    readonly_fields = (
        "lead_type", "name", "phone", "email", "message", "product", "source_page", "created_at",
    )
    list_per_page = 40
    actions = ("mark_in_progress", "mark_done")

    class Media:
        css = {"all": ("css/admin_badges.css",)}

    @admin.display(description="Статус", ordering="status")
    def status_badge(self, obj):
        css = {
            Lead.Status.NEW: "badge-admin badge-admin--new",
            Lead.Status.IN_PROGRESS: "badge-admin badge-admin--progress",
            Lead.Status.DONE: "badge-admin badge-admin--done",
        }.get(obj.status, "badge-admin")
        return format_html('<span class="{}">{}</span>', css, obj.get_status_display())

    @admin.action(description="Статус → В обробці")
    def mark_in_progress(self, request, queryset):
        queryset.update(status=Lead.Status.IN_PROGRESS)

    @admin.action(description="Статус → Опрацьована")
    def mark_done(self, request, queryset):
        queryset.update(status=Lead.Status.DONE)

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        new_count = Lead.objects.filter(status=Lead.Status.NEW).count()
        extra_context["title"] = f"Заявки — нових: {new_count}"
        return super().changelist_view(request, extra_context=extra_context)
