from django.contrib import admin, messages
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
from .filters import active_catalog_filters
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

    class Media:
        css = {"all": ("css/admin/lang_tabs.css",)}
        js = ("js/admin/lang_tabs.js",)

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
    fields = (
        "label", "label_ru", "sku_variant", "price", "old_price",
        "stock_qty", "is_default", "order",
    )


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
        ProductAvailabilityFilter,
        ("is_own_production", CleanBooleanDropdownFilter),
        ("is_hit", CleanBooleanDropdownFilter),
        ("is_new", CleanBooleanDropdownFilter),
        ("is_sale", CleanBooleanDropdownFilter),
        ("is_active", CleanBooleanDropdownFilter),
    )
    list_filter_options = horizontal_options_for(list_filter)
    search_fields = (
        "name", "sku", "pack_volume", "brand",
        "country_of_origin", "variants__sku_variant", "variants__label",
    )
    inlines = [ProductVariantInline, ProductImageInline]
    actions = ("merge_selected_products",)

    def get_fields(self, request, obj=None):
        attr_fields = [
            f"attr_{cf.slug}"
            for cf in active_catalog_filters()
        ]
        return (
            "category", "sku", "name", "name_ru", "slug",
            "short_description", "short_description_ru",
            "description", "description_ru", "characteristics", "characteristics_ru",
            *attr_fields,
            "brand", "country_of_origin", "pack_volume",
            "base_price", "old_price",
            "is_own_production", "is_hit", "is_new", "is_sale", "is_active",
        )

    def get_form(self, request, obj=None, change=False, **kwargs):
        # attr_* додаються у ProductAdminForm.__init__, їх немає на моделі.
        fields = kwargs.get("fields")
        if fields is None:
            fields = self.get_fields(request, obj)
        kwargs["fields"] = [
            name for name in fields if not str(name).startswith("attr_")
        ]
        return super().get_form(request, obj, change=change, **kwargs)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if hasattr(form, "_save_attributes"):
            form._save_attributes(obj)

    @admin.action(description="Об'єднати вибрані в один товар (варіанти)")
    def merge_selected_products(self, request, queryset):
        from .product_merge import MergeError, merge_products

        try:
            parent, hidden = merge_products(queryset)
        except MergeError as exc:
            self.message_user(request, str(exc), level=messages.ERROR)
            return
        hidden_skus = ", ".join(item.sku for item in hidden)
        self.message_user(
            request,
            (
                f"Варіанти зібрано в «{parent.name}» ({parent.sku}). "
                f"Приховано як окремі товари: {hidden_skus}. "
                f"Перевірте варіанти в картці основного товару."
            ),
        )

    class Media:
        css = {
            "all": (
                "css/admin_product_list.css",
                "css/admin/lang_tabs.css",
                "css/admin/cms_tinymce.css",
            )
        }
        js = ("js/admin/lang_tabs.js",)

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("category")
            .prefetch_related("images")
            .distinct()
        )

    @admin.display(description="")
    def image_thumb(self, obj):
        image = None
        for item in obj.images.all():
            if not item.image:
                continue
            try:
                if item.image.storage.exists(item.image.name):
                    image = item.image
                    break
            except Exception:
                continue
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


from .admin_recent_actions import patch_admin_recent_actions_urls  # noqa: E402

patch_admin_recent_actions_urls()
