from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline
from django.db.models import Count
from django.utils.html import format_html

from .models import Order, OrderItem, PromoCode


class OrderItemInline(TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product", "variant", "product_name", "variant_label", "price", "quantity")


class NewOrdersFilter(admin.SimpleListFilter):
    title = "Нові"
    parameter_name = "only_new"

    def lookups(self, request, model_admin):
        return (("1", "Лише нові"),)

    def queryset(self, request, queryset):
        if self.value() == "1":
            return queryset.filter(status=Order.Status.NEW)
        return queryset


@admin.register(Order)
class OrderAdmin(ModelAdmin):
    list_display = (
        "order_number", "full_name", "phone", "status_badge", "payment_badge",
        "delivery_method", "total", "created_at",
    )
    list_filter = (NewOrdersFilter, "status", "payment_status", "delivery_method", "payment_method")
    search_fields = ("order_number", "full_name", "phone", "email", "city", "warehouse")
    readonly_fields = (
        "order_number", "subtotal", "discount_total", "total", "created_at",
        "np_city_ref", "np_warehouse_ref",
    )
    inlines = [OrderItemInline]
    list_per_page = 40
    actions = ("mark_processing", "mark_shipped", "mark_done", "mark_paid")

    fieldsets = (
        ("Клієнт", {"fields": ("full_name", "phone", "email")}),
        ("Доставка", {"fields": (
            "delivery_method", "city", "warehouse", "np_city_ref", "np_warehouse_ref",
        )}),
        ("Оплата", {"fields": (
            "payment_method", "payment_status", "promo_code",
            "subtotal", "discount_total", "total",
        )}),
        ("Статус", {"fields": (
            "status", "comment", "agreed_to_data_processing", "order_number", "created_at",
        )}),
    )

    class Media:
        css = {"all": ("css/admin_badges.css",)}

    @admin.display(description="Статус", ordering="status")
    def status_badge(self, obj):
        css = {
            Order.Status.NEW: "badge-admin badge-admin--new",
            Order.Status.PROCESSING: "badge-admin badge-admin--progress",
            Order.Status.SHIPPED: "badge-admin badge-admin--shipped",
            Order.Status.DONE: "badge-admin badge-admin--done",
        }.get(obj.status, "badge-admin")
        return format_html('<span class="{}">{}</span>', css, obj.get_status_display())

    @admin.display(description="Оплата", ordering="payment_status")
    def payment_badge(self, obj):
        css = {
            Order.PaymentStatus.PENDING: "badge-admin badge-admin--pending",
            Order.PaymentStatus.PAID: "badge-admin badge-admin--paid",
            Order.PaymentStatus.FAILED: "badge-admin badge-admin--failed",
        }.get(obj.payment_status, "badge-admin")
        return format_html('<span class="{}">{}</span>', css, obj.get_payment_status_display())

    @admin.action(description="Статус → В обробці")
    def mark_processing(self, request, queryset):
        queryset.update(status=Order.Status.PROCESSING)

    @admin.action(description="Статус → Відправлено")
    def mark_shipped(self, request, queryset):
        queryset.update(status=Order.Status.SHIPPED)

    @admin.action(description="Статус → Виконано")
    def mark_done(self, request, queryset):
        queryset.update(status=Order.Status.DONE)

    @admin.action(description="Оплата → Оплачено")
    def mark_paid(self, request, queryset):
        queryset.update(payment_status=Order.PaymentStatus.PAID)

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        new_count = Order.objects.filter(status=Order.Status.NEW).count()
        unpaid = Order.objects.filter(
            payment_method=Order.PaymentMethod.LIQPAY,
            payment_status=Order.PaymentStatus.PENDING,
        ).count()
        extra_context["title"] = f"Замовлення — нових: {new_count}, очікують оплату: {unpaid}"
        return super().changelist_view(request, extra_context=extra_context)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(_items_count=Count("items"))


@admin.register(PromoCode)
class PromoCodeAdmin(ModelAdmin):
    list_display = ("code", "discount_type", "amount", "min_subtotal", "is_active", "valid_until")
    list_filter = ("discount_type", "is_active")
    search_fields = ("code",)
    list_editable = ("is_active",)
