"""Розділити обʼєм / вагу / кількість шт. Прибрати потужність з товару і CMS."""

import re

from django.db import migrations

_WEIGHT_RE = re.compile(
    r"\d+(?:[.,]\d+)?\s*(?:кг|г)(?![а-яіїєґa-z])",
    re.IGNORECASE,
)
_VOLUME_RE = re.compile(
    r"\d+(?:[.,]\d+)?\s*(?:мл|л)(?![а-яіїєґa-z])",
    re.IGNORECASE,
)
_PIECE_RE = re.compile(
    r"\d+(?:[.,]\d+)?\s*шт(?![а-яіїєґa-z])",
    re.IGNORECASE,
)
_POWER_CHAR_KEYS = ("Потужність", "Мощность", "power", "Power")
_PIECE_ROOT_SLUGS = (
    "nasinnia",
    "posadkovii-material",
    "sadovii-instrument",
    "poliv-ta-opriskuvachi",
    "zakhist-vid-pobutovikh-shkidnikiv",
)


def _unit_kind(text):
    value = text or ""
    if _WEIGHT_RE.search(value):
        return "weight"
    if _VOLUME_RE.search(value):
        return "volume"
    if _PIECE_RE.search(value):
        return "pieces"
    return None


def _ensure_filter(CatalogFilter, slug, name, name_ru, order):
    cf, created = CatalogFilter.objects.get_or_create(
        slug=slug,
        defaults={
            "name": name,
            "name_ru": name_ru,
            "order": order,
            "is_active": True,
            "use_country_labels": False,
        },
    )
    if not created and slug == "volume":
        if cf.name in {"Обʼєм / вага", "Об'єм / вага"}:
            cf.name = name
            cf.name_ru = name_ru
            cf.save(update_fields=["name", "name_ru"])
    return cf


def _ensure_value(CatalogFilterValue, catalog_filter, value):
    CatalogFilterValue.objects.get_or_create(
        catalog_filter=catalog_filter,
        value=value,
        defaults={"order": 0, "is_active": True},
    )


def forwards(apps, schema_editor):
    CatalogFilter = apps.get_model("catalog", "CatalogFilter")
    CatalogFilterValue = apps.get_model("catalog", "CatalogFilterValue")
    CatalogFilterCategory = apps.get_model("catalog", "CatalogFilterCategory")
    ProductAttribute = apps.get_model("catalog", "ProductAttribute")
    Product = apps.get_model("catalog", "Product")
    ProductVariant = apps.get_model("catalog", "ProductVariant")
    Category = apps.get_model("catalog", "Category")
    SiteBlock = apps.get_model("core", "SiteBlock")

    CatalogFilter.objects.filter(slug="power").delete()
    CatalogFilter.objects.filter(name__in=("Потужність", "Мощность")).delete()
    SiteBlock.objects.filter(
        page__in=("catalog", "product"),
        key__in=("filters_power", "power_label"),
    ).delete()

    volume_cf = _ensure_filter(CatalogFilter, "volume", "Обʼєм", "Объём", 30)
    weight_cf = _ensure_filter(CatalogFilter, "weight", "Вага", "Вес", 35)
    pieces_cf = _ensure_filter(CatalogFilter, "pieces", "Кількість шт", "Количество шт", 40)
    by_slug = {"volume": volume_cf, "weight": weight_cf, "pieces": pieces_cf}

    for binding in list(volume_cf.category_bindings.all()):
        for target in (weight_cf, pieces_cf):
            CatalogFilterCategory.objects.get_or_create(
                catalog_filter=target,
                category_id=binding.category_id,
                defaults={"is_enabled": binding.is_enabled},
            )

    for slug in _PIECE_ROOT_SLUGS:
        cat = Category.objects.filter(slug=slug).first()
        if not cat:
            continue
        CatalogFilterCategory.objects.get_or_create(
            catalog_filter=pieces_cf,
            category_id=cat.pk,
            defaults={"is_enabled": True},
        )

    for value_obj in list(volume_cf.values.all()):
        kind = _unit_kind(value_obj.value) or "volume"
        if kind == "volume":
            continue
        target = by_slug[kind]
        _ensure_value(CatalogFilterValue, target, value_obj.value)
        for attr in ProductAttribute.objects.filter(
            catalog_filter=volume_cf,
            value=value_obj.value,
        ):
            clash = (
                ProductAttribute.objects.filter(
                    product_id=attr.product_id,
                    catalog_filter=target,
                )
                .exclude(pk=attr.pk)
                .exists()
            )
            if clash:
                attr.delete()
            else:
                attr.catalog_filter = target
                attr.save(update_fields=["catalog_filter"])
        value_obj.delete()

    for product in Product.objects.all().iterator():
        chars = product.characteristics or {}
        ru = product.characteristics_ru or {}
        char_updates = []
        if any(key in chars for key in _POWER_CHAR_KEYS):
            for key in _POWER_CHAR_KEYS:
                chars.pop(key, None)
            product.characteristics = chars
            char_updates.append("characteristics")
        if any(key in ru for key in _POWER_CHAR_KEYS):
            for key in _POWER_CHAR_KEYS:
                ru.pop(key, None)
            product.characteristics_ru = ru
            char_updates.append("characteristics_ru")
        if char_updates:
            product.save(update_fields=char_updates)

        labels = []
        pack = (product.pack_volume or "").strip()
        if pack:
            labels.append(pack)
        for variant in ProductVariant.objects.filter(product_id=product.pk):
            label = (variant.label or "").strip()
            if label:
                labels.append(label)
        for label in labels:
            kind = _unit_kind(label)
            if not kind:
                continue
            _ensure_value(CatalogFilterValue, by_slug[kind], label)


def backwards(apps, schema_editor):
    CatalogFilter = apps.get_model("catalog", "CatalogFilter")
    CatalogFilter.objects.filter(slug__in=("weight", "pieces")).delete()
    volume = CatalogFilter.objects.filter(slug="volume").first()
    if volume:
        volume.name = "Обʼєм / вага"
        volume.name_ru = "Объём / вес"
        volume.save(update_fields=["name", "name_ru"])


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0017_replace_sml_pack_labels"),
        ("core", "0009_hardcode_shipping_threshold"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
        migrations.RemoveField(
            model_name="product",
            name="power",
        ),
    ]
