from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from unfold.admin import ModelAdmin, TabularInline

from apps.core.admin_filters import (
    CleanAllValuesDropdownFilter,
    CleanBooleanDropdownFilter,
    CleanRelatedDropdownFilter,
    ProductAvailabilityFilter,
    TopDropdownFiltersMixin,
    horizontal_options_for,
)
from apps.core.admin_guidelines import help_for_category_level
from apps.core.admin_utils import ImagePreviewMixin

from .category_forms import RootCategoryForm, SubCategoryForm, SubSubCategoryForm
from .category_proxies import RootCategory, SubCategory, SubSubCategory
from .forms import ProductAdminForm
from .icons import category_icon_caption, category_icon_url
from .models import Category, Product, ProductImage, ProductVariant

# Реєстрація адмінки фільтрів
from . import filter_admin  # noqa: E402,F401


class CategoryLevelAdmin(ImagePreviewMixin, TopDropdownFiltersMixin, ModelAdmin):
    """Спільна база для рівнів меню."""

    list_display = ("name", "erp_name", "parent", "order", "is_active", "icon_thumb")
    list_filter = (("is_active", CleanBooleanDropdownFilter),)
    list_filter_options = horizontal_options_for(list_filter)
    search_fields = ("name", "erp_name", "slug")
    ordering = ("order", "name")
    readonly_fields = ("level_hint", "image_preview")
    preview_max_height = 96
    preview_max_width = 96
    for_nav_preview = False
    category_level = 1

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("parent", "parent__parent")

    @admin.display(description="Підказка")
    def level_hint(self, obj=None):
        tip = help_for_category_level(self.category_level)
        return format_html(
            '<div style="max-width:36rem;line-height:1.45;color:#4b5563;'
            'background:#f9fafb;border:1px solid #e5e7eb;border-radius:0.5rem;'
            'padding:0.75rem 1rem">{}</div>',
            tip,
        )

    def _icon_img_html(self, obj, *, size=40, show_caption=False):
        url = category_icon_url(obj, for_nav=self.for_nav_preview)
        if not url:
            return "—"
        caption = ""
        if show_caption:
            caption = mark_safe(
                '<div style="margin-top:6px;color:#6b7280;font-size:12px">'
                f"{category_icon_caption(obj, for_nav=self.for_nav_preview)}</div>"
            )
        return format_html(
            '<img src="{}" alt="" width="{}" height="{}" '
            'style="width:{}px;height:{}px;object-fit:contain;'
            'border-radius:4px;background:#f3f4f6;padding:2px">'
            "{}",
            url,
            size,
            size,
            size,
            size,
            caption,
        )

    @admin.display(description="Превʼю")
    def image_preview(self, obj):
        return self._icon_img_html(obj, size=self.preview_max_height, show_caption=True)

    @admin.display(description="Іконка")
    def icon_thumb(self, obj):
        return self._icon_img_html(obj, size=40, show_caption=False)


@admin.register(RootCategory)
class RootCategoryAdmin(CategoryLevelAdmin):
    form = RootCategoryForm
    for_nav_preview = True
    category_level = 1
    list_display = ("name", "erp_name", "order", "is_active", "icon_thumb")
    fields = (
        "level_hint",
        "name", "name_ru", "erp_name", "slug",
        "image_preview", "image", "description", "description_ru", "order", "is_active",
    )

    def get_queryset(self, request):
        return super().get_queryset(request).filter(parent__isnull=True)


@admin.register(SubCategory)
class SubCategoryAdmin(CategoryLevelAdmin):
    form = SubCategoryForm
    category_level = 2
    list_filter = (
        ("is_active", CleanBooleanDropdownFilter),
        ("parent", CleanRelatedDropdownFilter),
    )
    list_filter_options = horizontal_options_for(list_filter)
    fields = (
        "level_hint",
        "parent", "name", "name_ru", "erp_name", "slug",
        "image_preview", "image", "description", "description_ru", "order", "is_active",
    )

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .filter(parent__isnull=False, parent__parent__isnull=True)
        )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "parent":
            kwargs["queryset"] = Category.objects.filter(parent__isnull=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(SubSubCategory)
class SubSubCategoryAdmin(CategoryLevelAdmin):
    form = SubSubCategoryForm
    category_level = 3
    list_filter = (
        ("is_active", CleanBooleanDropdownFilter),
        ("parent", CleanRelatedDropdownFilter),
    )
    list_filter_options = horizontal_options_for(list_filter)
    fields = (
        "level_hint",
        "parent", "name", "name_ru", "erp_name", "slug",
        "image_preview", "image", "description", "description_ru", "order", "is_active",
    )

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .filter(parent__parent__isnull=False)
        )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "parent":
            kwargs["queryset"] = Category.objects.filter(
                parent__isnull=False, parent__parent__isnull=True,
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


# Прихована реєстрація Category — для FK у товарів, без пункту в меню
@admin.register(Category)
class CategoryAdmin(CategoryLevelAdmin):
    search_fields = ("name", "erp_name", "slug")

    def has_module_permission(self, request):
        return False


class ProductVariantInline(TabularInline):
    model = ProductVariant
    extra = 1


class ProductImageInline(TabularInline):
    model = ProductImage
    extra = 1


@admin.register(Product)
class ProductAdmin(TopDropdownFiltersMixin, ModelAdmin):
    form = ProductAdminForm
    list_display = (
        "image_thumb", "name", "sku", "category", "base_price", "active_flag",
    )
    list_filter = (
        ("category", CleanRelatedDropdownFilter),
        ("brand", CleanAllValuesDropdownFilter),
        ("country_of_origin", CleanAllValuesDropdownFilter),
        ("power", CleanAllValuesDropdownFilter),
        ProductAvailabilityFilter,
        ("is_own_production", CleanBooleanDropdownFilter),
        ("is_hit", CleanBooleanDropdownFilter),
        ("is_new", CleanBooleanDropdownFilter),
        ("is_sale", CleanBooleanDropdownFilter),
        ("is_active", CleanBooleanDropdownFilter),
    )
    list_filter_options = horizontal_options_for(list_filter)
    search_fields = ("name", "sku", "pack_volume", "power", "brand", "country_of_origin")
    inlines = [ProductVariantInline, ProductImageInline]
    fields = (
        "category", "sku", "name", "name_ru", "slug",
        "short_description", "short_description_ru",
        "description", "description_ru", "characteristics", "characteristics_ru",
        "brand", "country_of_origin", "pack_volume", "power",
        "base_price", "old_price",
        "is_own_production", "is_hit", "is_new", "is_sale", "is_active",
    )

    class Media:
        css = {"all": ("css/admin_product_list.css",)}

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("category")
            .prefetch_related("images")
        )

    @admin.display(description="")
    def image_thumb(self, obj):
        image = None
        for item in obj.images.all():
            if item.image:
                image = item.image
                break
        if not image:
            return "—"
        try:
            url = image.url
        except Exception:
            return "—"
        return format_html(
            '<img src="{}" alt="" width="40" height="40" '
            'class="admin-product-thumb" '
            'style="width:40px;height:40px;object-fit:cover;'
            'border-radius:4px;background:#f3f4f6;display:block">',
            url,
        )

    @admin.display(
        description=mark_safe(
            '<span title="Активний (видимий на сайті)" '
            'style="font-size:11px;line-height:1.2">Активність</span>'
        ),
        boolean=True,
        ordering="is_active",
    )
    def active_flag(self, obj):
        return obj.is_active
