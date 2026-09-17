"""Seed довідника фільтрів з товарів і slug-правил категорій."""

from django.db import migrations


VOLUME_ROOT_SLUGS = frozenset({
    "nasinnia",
    "dobriva-ta-stimuliatori-rostu",
    "zasobi-zakhistu-roslin",
    "grunti-ta-vse-dlia-posadki",
})
VOLUME_EXTRA_SLUGS = frozenset({"vagove-nasinnia"})
POWER_ROOT_SLUGS = frozenset({
    "sadovii-instrument",
    "poliv-ta-opriskuvachi",
})

FIELD_MAP = {
    "brand": "brand",
    "country": "country_of_origin",
    "volume": "pack_volume",
    "power": "power",
}


def seed_filters(apps, schema_editor):
    Product = apps.get_model("catalog", "Product")
    Category = apps.get_model("catalog", "Category")
    FilterOption = apps.get_model("catalog", "FilterOption")
    CategoryFilterSetting = apps.get_model("catalog", "CategoryFilterSetting")

    for filter_type, field in FIELD_MAP.items():
        values = (
            Product.objects.exclude(**{field: ""})
            .order_by(field)
            .values_list(field, flat=True)
            .distinct()
        )
        for order, value in enumerate(values):
            if not value:
                continue
            FilterOption.objects.get_or_create(
                filter_type=filter_type,
                value=value,
                defaults={"order": order, "is_active": True},
            )

    roots = list(Category.objects.filter(parent__isnull=True))
    for cat in roots:
        for filter_type in ("brand", "country"):
            CategoryFilterSetting.objects.get_or_create(
                category_id=cat.pk,
                filter_type=filter_type,
                defaults={"is_enabled": True},
            )

    volume_slugs = VOLUME_ROOT_SLUGS | VOLUME_EXTRA_SLUGS
    for cat in Category.objects.filter(slug__in=volume_slugs):
        CategoryFilterSetting.objects.get_or_create(
            category_id=cat.pk,
            filter_type="volume",
            defaults={"is_enabled": True},
        )

    for cat in Category.objects.filter(slug__in=POWER_ROOT_SLUGS):
        CategoryFilterSetting.objects.get_or_create(
            category_id=cat.pk,
            filter_type="power",
            defaults={"is_enabled": True},
        )


def unseed_filters(apps, schema_editor):
    FilterOption = apps.get_model("catalog", "FilterOption")
    CategoryFilterSetting = apps.get_model("catalog", "CategoryFilterSetting")
    CategoryFilterSetting.objects.all().delete()
    FilterOption.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0011_filter_dictionary"),
    ]

    operations = [
        migrations.RunPython(seed_filters, unseed_filters),
    ]
