from django.contrib import admin

from .models import Lead


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ("created_at", "lead_type", "name", "phone", "status", "product")
    list_filter = ("lead_type", "status")
    search_fields = ("name", "phone", "email")
    list_editable = ("status",)
    readonly_fields = ("lead_type", "name", "phone", "email", "message", "product", "source_page", "created_at")
