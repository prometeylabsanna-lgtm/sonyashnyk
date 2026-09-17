"""Перенос FilterOption / CategoryFilterSetting / полів Product → динамічні фільтри."""

from django.db import migrations

FILTER_DEFS = (
    ("brand", "Бренд", "Бренд", False, 10),
    ("country", "Країна виробник", "Страна производитель", True, 20),
    ("volume", "Обʼєм / вага", "Объём / вес", False, 30),
    ("power", "Потужність", "Мощность", False, 40),
)

LEGACY_FIELDS = {
    "brand": "brand",
    "country": "country_of_origin",
    "volume": "pack_volume",
    "power": "power",
}

TYPE_TO_SLUG = {
    "brand": "brand",
    "country": "country",
    "volume": "volume",
    "power": "power",
}


def forwards(apps, schema_editor):
    Product = apps.get_model("catalog", "Product")
    FilterOption = apps.get_model("catalog", "FilterOption")
    CategoryFilterSetting = apps.get_model("catalog", "CategoryFilterSetting")
    CatalogFilter = apps.get_model("catalog", "CatalogFilter")
    CatalogFilterValue = apps.get_model("catalog", "CatalogFilterValue")
    CatalogFilterCategory = apps.get_model("catalog", "CatalogFilterCategory")
    ProductAttribute = apps.get_model("catalog", "ProductAttribute")

    filters_by_slug = {}
    for slug, name, name_ru, use_country, order in FILTER_DEFS:
        cf, _ = CatalogFilter.objects.get_or_create(
            slug=slug,
            defaults={
                "name": name,
                "name_ru": name_ru,
                "order": order,
                "is_active": True,
                "use_country_labels": use_country,
            },
        )
        filters_by_slug[slug] = cf

    for opt in FilterOption.objects.all():
        slug = TYPE_TO_SLUG.get(opt.filter_type)
        cf = filters_by_slug.get(slug)
        if not cf:
            continue
        CatalogFilterValue.objects.get_or_create(
            catalog_filter=cf,
            value=opt.value,
            defaults={"order": opt.order, "is_active": opt.is_active},
        )

    for setting in CategoryFilterSetting.objects.all():
        slug = TYPE_TO_SLUG.get(setting.filter_type)
        cf = filters_by_slug.get(slug)
        if not cf:
            continue
        CatalogFilterCategory.objects.get_or_create(
            catalog_filter=cf,
            category_id=setting.category_id,
            defaults={"is_enabled": setting.is_enabled},
        )

    for product in Product.objects.all().iterator():
        for slug, field in LEGACY_FIELDS.items():
            value = (getattr(product, field, "") or "").strip()
            if not value:
                continue
            cf = filters_by_slug[slug]
            ProductAttribute.objects.get_or_create(
                product_id=product.pk,
                catalog_filter=cf,
                defaults={"value": value},
            )
            CatalogFilterValue.objects.get_or_create(
                catalog_filter=cf,
                value=value,
                defaults={"order": 0, "is_active": True},
            )


def backwards(apps, schema_editor):
    CatalogFilter = apps.get_model("catalog", "CatalogFilter")
    CatalogFilter.objects.filter(slug__in=LEGACY_FIELDS.keys()).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0013_catalog_filter_dynamic"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
