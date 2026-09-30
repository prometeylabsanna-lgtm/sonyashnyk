from django.core.cache import cache
from django.db import models
from django.urls import reverse

from apps.core.fields import WebPImageField
from apps.core.utils import make_unique_slug


class Category(models.Model):
    """Категорія каталогу. Підтримує до 3 рівнів вкладеності через parent.

    Назва на сайті може відрізнятись від назви в обліковій системі —
    для цього призначене поле `erp_name`.
    """

    name = models.CharField("Назва на сайті", max_length=160)
    name_ru = models.CharField("Назва на сайті (RU)", max_length=160, blank=True, default="")
    erp_name = models.CharField(
        "Назва в обліковій системі", max_length=160, blank=True,
        help_text="Заповнюється, якщо назва на сайті відрізняється від довідника.",
    )
    slug = models.SlugField(
        "Адреса в посиланні", max_length=180, unique=True, blank=True,
        help_text="Краще не змінювати — заповниться само з назви.",
    )
    parent = models.ForeignKey(
        "self", verbose_name="Батьківська категорія",
        null=True, blank=True, on_delete=models.CASCADE, related_name="children",
    )
    image = WebPImageField(
        "Іконка категорії",
        upload_to="categories/",
        blank=True,
        null=True,
        help_text=(
            "Завантажте іконку або залиште порожньою. "
            "Головні розділи — тоді буде стандартна іконка сайту; "
            "підрозділи — соняшник."
        ),
    )
    description = models.TextField("Опис", blank=True)
    description_ru = models.TextField("Опис (RU)", blank=True, default="")
    order = models.PositiveIntegerField("Порядок сортування", default=0)
    is_active = models.BooleanField("Активна", default=True)

    class Meta:
        verbose_name = "Категорія"
        verbose_name_plural = "Категорії"
        ordering = ["order", "name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = make_unique_slug(Category, self.name, instance_pk=self.pk)
        super().save(*args, **kwargs)
        cache.delete("nav_categories")
        cache.delete("footer_categories")

    def delete(self, *args, **kwargs):
        result = super().delete(*args, **kwargs)
        cache.delete("nav_categories")
        cache.delete("footer_categories")
        return result

    def get_absolute_url(self):
        return reverse("catalog:category", kwargs={"slug": self.slug})

    @property
    def level(self):
        """0 — коренева категорія, 1 — підкатегорія, 2 — уточнення."""
        level, node = 0, self.parent
        while node is not None:
            level += 1
            node = node.parent
        return level

    def breadcrumb_chain(self):
        chain, node = [], self
        while node is not None:
            chain.append(node)
            node = node.parent
        return list(reversed(chain))

    def get_descendant_ids(self):
        """ID цієї категорії + усіх дочірніх (до 3 рівнів), для збору товарів."""
        ids = [self.pk]
        for child in self.children.filter(is_active=True):
            ids.extend(child.get_descendant_ids())
        return ids


class ProductQuerySet(models.QuerySet):
    def for_cards(self):
        return self.select_related(
            "category",
            "category__parent",
            "category__parent__parent",
        ).prefetch_related("variants", "images")


class Product(models.Model):
    """Товар. sku синхронізується з обліковою системою/касою."""

    category = models.ForeignKey(
        Category, verbose_name="Категорія", on_delete=models.PROTECT, related_name="products",
    )
    sku = models.CharField("Код товару (SKU)", max_length=64, unique=True)
    dntrade_product_id = models.CharField(
        "DNTrade product_id",
        max_length=64,
        blank=True,
        default="",
        db_index=True,
        help_text="UUID товару в Navkolo DNTrade.",
    )
    dntrade_code = models.BigIntegerField(
        "DNTrade code",
        null=True,
        blank=True,
        db_index=True,
        help_text="Числовий код товару в DNTrade.",
    )
    dntrade_synced_at = models.DateTimeField(
        "Остання синхронізація DNTrade",
        null=True,
        blank=True,
    )
    name = models.CharField("Назва на сайті", max_length=255)
    name_ru = models.CharField("Назва на сайті (RU)", max_length=255, blank=True, default="")
    slug = models.SlugField(
        "Адреса в посиланні", max_length=255, unique=True, blank=True,
        help_text="Краще не змінювати — заповниться само з назви.",
    )
    short_description = models.CharField("Короткий опис", max_length=255, blank=True)
    short_description_ru = models.CharField("Короткий опис (RU)", max_length=255, blank=True, default="")
    description = models.TextField(
        "Опис",
        blank=True,
        help_text=(
            "Повний опис товару. Пишіть звичайними реченнями — "
            "Enter робить новий абзац. Жирний, списки й посилання — кнопками зверху."
        ),
    )
    description_ru = models.TextField("Опис (RU)", blank=True, default="")
    characteristics = models.JSONField(
        "Характеристики",
        default=dict,
        blank=True,
        help_text="Рядки «назва → значення», наприклад «Обʼєм → 100 мл».",
    )
    characteristics_ru = models.JSONField(
        "Характеристики",
        default=dict,
        blank=True,
        help_text="Ті самі характеристики російською, рядки «назва → значення».",
    )

    brand = models.CharField("Бренд / виробник", max_length=120, blank=True)
    country_of_origin = models.CharField("Країна виробник", max_length=120, blank=True)
    pack_volume = models.CharField(
        "Обʼєм / вага / кількість",
        max_length=80,
        blank=True,
        help_text="Обʼєм, вага або кількість: 6 мл, 100 мл, 1 л, 10 г, 500 г, 5 кг, 10 шт. "
                  "Окремі варіанти краще робити варіантами товару.",
    )

    base_price = models.DecimalField("Базова ціна", max_digits=10, decimal_places=2)
    old_price = models.DecimalField(
        "Стара ціна (для акції)", max_digits=10, decimal_places=2, blank=True, null=True,
    )

    is_own_production = models.BooleanField("Власне виробництво", default=False)
    is_hit = models.BooleanField("Хіт продажу", default=False)
    is_new = models.BooleanField("Новинка", default=False)
    is_sale = models.BooleanField("Акція / знижка", default=False)
    is_active = models.BooleanField("Активний (видимий на сайті)", default=True)

    created_at = models.DateTimeField("Створено", auto_now_add=True)
    updated_at = models.DateTimeField("Оновлено", auto_now=True)

    objects = models.Manager.from_queryset(ProductQuerySet)()

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товари"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.sku})"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = make_unique_slug(Product, self.name, instance_pk=self.pk)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("product_detail", kwargs={"slug": self.slug})

    @property
    def pack_measure_label(self):
        from .category_tree import pack_measure_label

        return pack_measure_label(self.category, self.pack_volume)

    @property
    def show_pack_volume(self):
        from .category_tree import pack_volume_worth_showing

        return pack_volume_worth_showing(self.pack_volume)

    @property
    def pack_variants(self):
        """Префетчений список варіантів — без зайвих запитів на картках."""
        return list(self.variants.all())

    @property
    def has_pack_choices(self):
        return len(self.pack_variants) > 1

    @property
    def default_variant(self):
        variants = self.pack_variants
        for variant in variants:
            if variant.is_default:
                return variant
        return variants[0] if variants else None

    @property
    def offer_variant(self):
        """Варіант для картки/кнопки: дефолт у наявності, інакше перший з залишком."""
        variants = self.pack_variants
        if not variants:
            return None
        default = None
        for variant in variants:
            if variant.is_default:
                default = variant
                break
        if default is None:
            default = variants[0]
        if default.stock_qty > 0:
            return default
        for variant in variants:
            if variant.stock_qty > 0:
                return variant
        return default

    @property
    def display_price(self):
        variant = self.offer_variant
        return variant.price if variant else self.base_price

    @property
    def display_old_price(self):
        variant = self.offer_variant
        old = variant.old_price if variant and variant.old_price else self.old_price
        if old is None:
            return None
        current = self.display_price
        if old <= current:
            return None
        return old

    @property
    def in_stock(self):
        variants = self.pack_variants
        if not variants:
            return False
        return any(variant.stock_qty > 0 for variant in variants)

    def get_characteristics(self):
        from apps.core.i18n_utils import is_ru

        base = self.characteristics or {}
        if not is_ru():
            return base
        ru = self.characteristics_ru or {}
        if not ru:
            return base
        # Якщо RU — повний словник з іншими ключами
        if set(ru.keys()) != set(base.keys()) and all(isinstance(v, str) for v in ru.values()):
            # значення під українськими ключами або повна заміна
            if any(k in base for k in ru):
                return {k: ru.get(k, v) for k, v in base.items()}
            return ru
        return {k: ru.get(k, v) for k, v in base.items()}


class ProductVariant(models.Model):
    """Варіант обʼєму, ваги або кількості зі своєю ціною й залишком."""

    product = models.ForeignKey(Product, verbose_name="Товар", on_delete=models.CASCADE, related_name="variants")
    label = models.CharField(
        "Назва варіанту",
        max_length=80,
        help_text="Наприклад: «100 мл», «1 л», «10 г», «500 г», «10 шт» — не розміри одягу S/M/L.",
    )
    label_ru = models.CharField("Назва варіанту (RU)", max_length=80, blank=True, default="")
    sku_variant = models.CharField("Код варіанту", max_length=64, blank=True)
    dntrade_product_id = models.CharField(
        "DNTrade product_id",
        max_length=64,
        blank=True,
        default="",
        db_index=True,
    )
    dntrade_code = models.BigIntegerField(
        "DNTrade code",
        null=True,
        blank=True,
        db_index=True,
    )
    price = models.DecimalField("Ціна", max_digits=10, decimal_places=2)
    old_price = models.DecimalField("Стара ціна", max_digits=10, decimal_places=2, blank=True, null=True)
    stock_qty = models.PositiveIntegerField("Залишок", default=0)
    max_per_order = models.PositiveIntegerField(
        "Макс. шт. в одному замовленні",
        null=True,
        blank=True,
        help_text="Порожньо — без ліміту («в одні руки»).",
    )
    is_default = models.BooleanField("Варіант за замовчуванням", default=False)
    order = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        verbose_name = "Варіант товару"
        verbose_name_plural = "Варіанти товару"
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.product.name} — {self.label}"


class ProductImage(models.Model):
    """Фото товару. Поки немає реальних фото — на фронті рендериться плейсхолдер."""

    product = models.ForeignKey(Product, verbose_name="Товар", on_delete=models.CASCADE, related_name="images")
    image = WebPImageField("Зображення", upload_to="products/", blank=True, null=True)
    source_url = models.URLField(
        "URL джерела (DNTrade)",
        max_length=500,
        blank=True,
        default="",
        help_text="Щоб не качати те саме фото щодня.",
    )
    alt = models.CharField("Alt-текст", max_length=255, blank=True)
    alt_ru = models.CharField("Alt-текст (RU)", max_length=255, blank=True, default="")
    order = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        verbose_name = "Фото товару"
        verbose_name_plural = "Фото товару"
        ordering = ["order", "id"]

    def __str__(self):
        return f"Фото {self.product.name} #{self.order}"


# Довідник фільтрів (окремий модуль, реєстрація через models)
from .filter_models import (  # noqa: E402,F401
    CatalogFilter,
    CatalogFilterCategory,
    CatalogFilterValue,
    ProductAttribute,
)
