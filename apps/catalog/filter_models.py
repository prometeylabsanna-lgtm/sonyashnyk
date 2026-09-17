"""Довідник значень фільтрів каталогу та привʼязка до категорій."""

from django.db import models, transaction


class FilterType(models.TextChoices):
    BRAND = "brand", "Бренд"
    COUNTRY = "country", "Країна"
    VOLUME = "volume", "Обʼєм / вага"
    POWER = "power", "Потужність"


# Поле Product ↔ тип фільтра
FILTER_PRODUCT_FIELDS = {
    FilterType.BRAND: "brand",
    FilterType.COUNTRY: "country_of_origin",
    FilterType.VOLUME: "pack_volume",
    FilterType.POWER: "power",
}


class FilterOption(models.Model):
    """Дозволене значення фільтра (бренд, країна, обʼєм, потужність)."""

    filter_type = models.CharField(
        "Тип фільтра",
        max_length=20,
        choices=FilterType.choices,
        db_index=True,
    )
    value = models.CharField("Значення", max_length=120)
    order = models.PositiveIntegerField("Порядок", default=0)
    is_active = models.BooleanField("Активне", default=True)

    class Meta:
        verbose_name = "Значення фільтра"
        verbose_name_plural = "Значення фільтрів"
        ordering = ["filter_type", "order", "value"]
        constraints = [
            models.UniqueConstraint(
                fields=["filter_type", "value"],
                name="catalog_filteroption_type_value_uniq",
            ),
        ]

    def __str__(self):
        return f"{self.get_filter_type_display()}: {self.value}"

    def save(self, *args, **kwargs):
        old_value = None
        if self.pk:
            old_value = (
                FilterOption.objects.filter(pk=self.pk)
                .values_list("value", flat=True)
                .first()
            )
        super().save(*args, **kwargs)
        if old_value and old_value != self.value:
            self._sync_products(old_value, self.value)

    def _sync_products(self, old_value, new_value):
        from .models import Product

        field = FILTER_PRODUCT_FIELDS.get(self.filter_type)
        if not field:
            return
        with transaction.atomic():
            Product.objects.filter(**{field: old_value}).update(**{field: new_value})


class CategoryFilterSetting(models.Model):
    """Де показувати який тип фільтра (категорія + нащадки через ланцюг)."""

    category = models.ForeignKey(
        "catalog.Category",
        verbose_name="Категорія",
        on_delete=models.CASCADE,
        related_name="filter_settings",
    )
    filter_type = models.CharField(
        "Тип фільтра",
        max_length=20,
        choices=FilterType.choices,
        db_index=True,
    )
    is_enabled = models.BooleanField("Увімкнено", default=True)

    class Meta:
        verbose_name = "Привʼязка фільтра до категорії"
        verbose_name_plural = "Привʼязки фільтрів до категорій"
        ordering = ["category__order", "category__name", "filter_type"]
        constraints = [
            models.UniqueConstraint(
                fields=["category", "filter_type"],
                name="catalog_catfilter_cat_type_uniq",
            ),
        ]

    def __str__(self):
        state = "увімкнено" if self.is_enabled else "вимкнено"
        return f"{self.category} · {self.get_filter_type_display()} ({state})"


class BrandFilterOption(FilterOption):
    class Meta:
        proxy = True
        verbose_name = "Бренд"
        verbose_name_plural = "Бренди"


class CountryFilterOption(FilterOption):
    class Meta:
        proxy = True
        verbose_name = "Країна"
        verbose_name_plural = "Країни"


class VolumeFilterOption(FilterOption):
    class Meta:
        proxy = True
        verbose_name = "Обʼєм / вага"
        verbose_name_plural = "Обʼєм / вага"


class PowerFilterOption(FilterOption):
    class Meta:
        proxy = True
        verbose_name = "Потужність"
        verbose_name_plural = "Потужність"
