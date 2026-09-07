from django.contrib import admin

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product", "variant", "product_name", "variant_label", "price", "quantity")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "order_number", "full_name", "phone", "status", "payment_status",
        "delivery_method", "total", "created_at",
    )
    list_filter = ("status", "payment_status", "delivery_method", "payment_method")
    search_fields = ("order_number", "full_name", "phone", "email")
    list_editable = ("status", "payment_status")
    readonly_fields = ("order_number", "subtotal", "total", "created_at")
    inlines = [OrderItemInline]
