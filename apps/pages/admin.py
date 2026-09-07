from django.contrib import admin

from .models import Certificate


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ("title", "series", "product", "is_active", "order")
    list_filter = ("is_active", "series")
    search_fields = ("title", "series")
