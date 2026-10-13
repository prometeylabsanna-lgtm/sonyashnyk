from django.contrib import admin, messages
from django.db.models import Count
from django.utils import timezone
from django.utils.html import format_html
from unfold.admin import ModelAdmin, TabularInline

from apps.core.admin_filters import (
    CleanBooleanDropdownFilter,
    CleanChoicesDropdownFilter,
    CleanDropdownFilter,
    TopDropdownFiltersMixin,
    horizontal_options_for,
)

from .models import Order, OrderItem, PromoCode
from .stock import release_order_stock
from .ukrposhta import UkrposhtaError, is_shipping_configured, is_tracking_configured
from .ukrposhta import summarize_tracking, track_barcode
from .ukrposhta_shipments import create_shipment_for_order, sticker_url


class OrderItemInline(TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product", "variant", "product_name", "variant_label", "price", "quantity")


class NewOrdersFilter(CleanDropdownFilter):
    title = "Нові"
    parameter_name = "only_new"

    def lookups(self, request, model_admin):
        return (("1", "Лише нові"),)

    def queryset(self, request, queryset):
        if self.value() == "1":
            return queryset.filter(status=Order.Status.NEW)
        return queryset


@admin.register(Order)
class OrderAdmin(TopDropdownFiltersMixin, ModelAdmin):
    list_display = (
        "order_number", "full_name", "phone", "status_badge", "payment_badge",
        "delivery_method", "up_barcode", "total", "stock_released", "created_at",
    )
    list_filter = (
        NewOrdersFilter,
        ("status", CleanChoicesDropdownFilter),
        ("payment_status", CleanChoicesDropdownFilter),
        ("delivery_method", CleanChoicesDropdownFilter),
        ("payment_method", CleanChoicesDropdownFilter),
        ("stock_released", CleanBooleanDropdownFilter),
    )
    list_filter_options = horizontal_options_for(list_filter)
    search_fields = (
        "order_number", "full_name", "phone", "email", "city", "warehouse",
        "up_barcode", "up_postindex",
    )
    readonly_fields = (
        "order_number", "subtotal", "discount_total", "total", "shipping_is_free", "created_at",
        "np_city_ref", "np_warehouse_ref",
        "up_city_id", "up_region_id", "up_postindex", "up_shipment_uuid", "up_barcode",
        "up_status", "up_status_at", "up_sticker_link",
        "stock_released",
        "monopay_invoice_id", "monopay_invoice_at",
    )
    inlines = [OrderItemInline]
    list_per_page = 40
    actions = (
        "mark_processing", "mark_shipped", "mark_done", "mark_paid", "restore_stock",
        "create_ukrposhta_ttn", "refresh_ukrposhta_tracking",
    )

    fieldsets = (
        ("Клієнт", {"fields": ("full_name", "phone", "email")}),
        ("Доставка", {"fields": (
            "delivery_method", "city", "warehouse",
            "np_city_ref", "np_warehouse_ref",
            "up_city_id", "up_region_id", "up_postindex",
            "up_shipment_uuid", "up_barcode", "up_status", "up_status_at", "up_sticker_link",
            "shipping_is_free",
        )}),
        ("Оплата", {"fields": (
            "payment_method", "payment_status", "stock_released",
            "monopay_invoice_id", "monopay_invoice_at", "promo_code",
            "subtotal", "discount_total", "total",
        )}),
        ("Статус", {"fields": (
            "status", "comment", "agreed_to_data_processing", "order_number", "created_at",
        )}),
    )

    class Media:
        css = {"all": ("css/admin_badges.css",)}

    @admin.display(description="Ярлик УП")
    def up_sticker_link(self, obj):
        key = (obj.up_shipment_uuid or obj.up_barcode or "").strip()
        if not key or not is_shipping_configured():
            return "—"
        return format_html(
            '<a href="{}" target="_blank" rel="noopener">PDF ярлик</a>',
            sticker_url(key),
        )

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
            Order.PaymentStatus.REFUNDED: "badge-admin badge-admin--failed",
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

    @admin.action(description="Повернути залишок на склад")
    def restore_stock(self, request, queryset):
        """Разове повернення резерву (failed / refunded / pending). Не чіпає paid."""
        restored = 0
        skipped = 0
        for order in queryset.prefetch_related("items"):
            if order.payment_status == Order.PaymentStatus.PAID:
                skipped += 1
                continue
            if release_order_stock(order):
                restored += 1
            else:
                skipped += 1
        self.message_user(
            request,
            f"Повернено залишок: {restored}. Пропущено: {skipped}.",
            messages.SUCCESS if restored else messages.WARNING,
        )

    @admin.action(description="Укрпошта: створити ТТН (ШКІ)")
    def create_ukrposhta_ttn(self, request, queryset):
        if not is_shipping_configured():
            self.message_user(
                request,
                "Укрпошта eCom не налаштована (Bearer / token / SENDER_UUID).",
                messages.ERROR,
            )
            return
        ok = 0
        errors = 0
        for order in queryset:
            if order.delivery_method != Order.DeliveryMethod.UKRPOSHTA:
                errors += 1
                continue
            if order.up_barcode:
                errors += 1
                continue
            try:
                result = create_shipment_for_order(order)
            except UkrposhtaError as exc:
                errors += 1
                self.message_user(request, f"{order.order_number}: {exc}", messages.ERROR)
                continue
            order.up_shipment_uuid = result["uuid"]
            order.up_barcode = result["barcode"]
            order.up_status = "CREATED"
            order.up_status_at = timezone.now()
            order.status = Order.Status.PROCESSING
            order.save(update_fields=[
                "up_shipment_uuid", "up_barcode", "up_status", "up_status_at", "status",
            ])
            ok += 1
        self.message_user(
            request,
            f"ТТН створено: {ok}. Помилок/пропущено: {errors}.",
            messages.SUCCESS if ok else messages.WARNING,
        )

    @admin.action(description="Укрпошта: оновити трекінг")
    def refresh_ukrposhta_tracking(self, request, queryset):
        if not (is_tracking_configured() or is_shipping_configured()):
            self.message_user(request, "Трекінг Укрпошти не налаштований.", messages.ERROR)
            return
        ok = 0
        errors = 0
        for order in queryset:
            barcode = (order.up_barcode or "").strip()
            if not barcode:
                errors += 1
                continue
            try:
                payload = track_barcode(barcode)
                summary = summarize_tracking(payload)
            except UkrposhtaError as exc:
                errors += 1
                self.message_user(request, f"{order.order_number}: {exc}", messages.ERROR)
                continue
            order.up_status = summary[:255]
            order.up_status_at = timezone.now()
            order.save(update_fields=["up_status", "up_status_at"])
            ok += 1
        self.message_user(
            request,
            f"Трекінг оновлено: {ok}. Помилок/пропущено: {errors}.",
            messages.SUCCESS if ok else messages.WARNING,
        )

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        new_count = Order.objects.filter(status=Order.Status.NEW).count()
        unpaid = Order.objects.filter(
            payment_method=Order.PaymentMethod.MONOPAY,
            payment_status=Order.PaymentStatus.PENDING,
        ).count()
        extra_context["title"] = f"Замовлення — нових: {new_count}, очікують оплату: {unpaid}"
        return super().changelist_view(request, extra_context=extra_context)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(_items_count=Count("items"))


@admin.register(PromoCode)
class PromoCodeAdmin(TopDropdownFiltersMixin, ModelAdmin):
    list_display = (
        "code", "discount_type", "amount", "min_subtotal",
        "used_count", "max_uses", "is_active", "valid_until",
    )
    list_filter = (
        ("discount_type", CleanChoicesDropdownFilter),
        ("is_active", CleanBooleanDropdownFilter),
    )
    list_filter_options = horizontal_options_for(list_filter)
    search_fields = ("code",)
    list_editable = ("is_active",)
    readonly_fields = ("used_count",)
