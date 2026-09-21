"""Динамічні фільтри каталогу: визначення → значення → привʼязка → атрибути товару."""

from django.db import models, transaction

from apps.core.utils import make_unique_slug


# Сумісність зі старими CharField на Product (PDP / картки / seed).
# Потужність лишається полем товару і не входить у фільтри каталогу.
LEGACY_PRODUCT_FIELDS = {
    "brand": "brand",
    "country": "country_of_origin",
    "volume": "pack_volume",
}


class CatalogFilter(models.Model):
    """Фільтр каталогу (можна додавати / видаляти в адмінці)."""

    name = models.CharField("Назва", max_length=120)
    name_ru = models.CharField("Назва (RU)", max_length=120, blank=True, default="")
    slug = models.SlugField(
        "Ключ (slug)",
        max_length=64,
        unique=True,
        blank=True,
        help_text="Параметр у URL (?brand=…). Залиште порожнім — згенерується з назви.",
    )
    order = models.PositiveIntegerField("Порядок", default=0)
    is_active = models.BooleanField("Активний", default=True)
    use_country_labels = models.BooleanField(
        "Показувати як назви країн",
        default=False,
        help_text="Для фільтра країни — підставляти локалізовані назви.",
    )

    class Meta:
        verbose_name = "Фільтр"
        verbose_name_plural = "Фільтри"
        ordering = ["order", "name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = make_unique_slug(CatalogFilter, self.name, instance_pk=self.pk)
        super().save(*args, **kwargs)

    def display_name(self):
        from apps.core.i18n_utils import is_ru

        if is_ru() and self.name_ru:
            return self.name_ru
        return self.name


class CatalogFilterValue(models.Model):
    """Дозволене значення фільтра."""

    catalog_filter = models.ForeignKey(
        CatalogFilter,
        verbose_name="Фільтр",
        on_delete=models.CASCADE,
        related_name="values",
    )
    value = models.CharField("Значення", max_length=120)
    order = models.PositiveIntegerField("Порядок", default=0)
    is_active = models.BooleanField("Активне", default=True)

    class Meta:
        verbose_name = "Значення фільтра"
        verbose_name_plural = "Значення фільтра"
        ordering = ["order", "value"]
        constraints = [
            models.UniqueConstraint(
                fields=["catalog_filter", "value"],
                name="catalog_filtervalue_filter_value_uniq",
            ),
        ]

    def __str__(self):
        return f"{self.catalog_filter.name}: {self.value}"

    def save(self, *args, **kwargs):
        old_value = None
        if self.pk:
            old_value = (
                CatalogFilterValue.objects.filter(pk=self.pk)
                .values_list("value", flat=True)
                .first()
            )
        super().save(*args, **kwargs)
        if old_value and old_value != self.value:
            self._sync_attributes(old_value, self.value)

    def _sync_attributes(self, old_value, new_value):
        with transaction.atomic():
            ProductAttribute.objects.filter(
                catalog_filter_id=self.catalog_filter_id,
                value=old_value,
            ).update(value=new_value)
            legacy = LEGACY_PRODUCT_FIELDS.get(self.catalog_filter.slug)
            if legacy:
                from .models import Product

                Product.objects.filter(**{legacy: old_value}).update(**{legacy: new_value})


class CatalogFilterCategory(models.Model):
    """Привʼязка фільтра до категорії (показувати на цій гілці каталогу)."""

    catalog_filter = models.ForeignKey(
        CatalogFilter,
        verbose_name="Фільтр",
        on_delete=models.CASCADE,
        related_name="category_bindings",
    )
    category = models.ForeignKey(
        "catalog.Category",
        verbose_name="Категорія",
        on_delete=models.CASCADE,
        related_name="catalog_filter_bindings",
    )
    is_enabled = models.BooleanField("Увімкнено", default=True)

    class Meta:
        verbose_name = "Привʼязка до категорії"
        verbose_name_plural = "Привʼязки до категорій"
        ordering = ["category__order", "category__name"]
        constraints = [
            models.UniqueConstraint(
                fields=["catalog_filter", "category"],
                name="catalog_filtercat_filter_cat_uniq",
            ),
        ]

    def __str__(self):
        state = "увімкнено" if self.is_enabled else "вимкнено"
        return f"{self.catalog_filter} · {self.category} ({state})"


class ProductAttribute(models.Model):
    """Значення фільтра на товарі (довільний ключ через CatalogFilter)."""

    product = models.ForeignKey(
        "catalog.Product",
        verbose_name="Товар",
        on_delete=models.CASCADE,
        related_name="filter_attrs",
    )
    catalog_filter = models.ForeignKey(
        CatalogFilter,
        verbose_name="Фільтр",
        on_delete=models.CASCADE,
        related_name="product_attrs",
    )
    value = models.CharField("Значення", max_length=120)

    class Meta:
        verbose_name = "Атрибут товару"
        verbose_name_plural = "Атрибути товарів"
        constraints = [
            models.UniqueConstraint(
                fields=["product", "catalog_filter"],
                name="catalog_productattr_product_filter_uniq",
            ),
        ]

    def __str__(self):
        return f"{self.product_id}: {self.catalog_filter.slug}={self.value}"


def sync_legacy_product_attrs(product) -> None:
    """Записує brand/country/volume з CharField у ProductAttribute."""
    for slug, field in LEGACY_PRODUCT_FIELDS.items():
        value = (getattr(product, field, "") or "").strip()
        cf = CatalogFilter.objects.filter(slug=slug, is_active=True).first()
        if not cf:
            continue
        if value:
            ProductAttribute.objects.update_or_create(
                product=product,
                catalog_filter=cf,
                defaults={"value": value},
            )
        else:
            ProductAttribute.objects.filter(
                product=product,
                catalog_filter=cf,
            ).delete()
