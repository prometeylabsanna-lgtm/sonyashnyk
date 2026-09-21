from django.db import migrations


def replace_size_pack_labels(apps, schema_editor):
    Product = apps.get_model("catalog", "Product")
    from apps.catalog.category_tree import rewrite_size_variant_labels

    products = (
        Product.objects.filter(variants__label__in=["S", "M", "L", "s", "m", "l"])
        .distinct()
        .select_related("category", "category__parent", "category__parent__parent")
        .prefetch_related("variants")
    )
    for product in products:
        rewrite_size_variant_labels(product)

    SiteBlock = apps.get_model("core", "SiteBlock")
    block = SiteBlock.objects.filter(page="product", key="volume_label").first()
    if block is None:
        return
    updates = []
    uk = (block.text_html or "").strip()
    ru = (block.text_html_ru or "").strip()
    if uk in {"Фасування:", "Фасування", "Фасовка:"}:
        block.text_html = "Обʼєм:"
        updates.append("text_html")
    if ru in {"Фасовка:", "Фасовка", "Фасування:"}:
        block.text_html_ru = "Объём:"
        updates.append("text_html_ru")
    if updates:
        block.save(update_fields=updates)


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0016_remove_power_catalog_filter"),
        ("core", "0006_i18n_ru_fields"),
    ]

    operations = [
        migrations.RunPython(replace_size_pack_labels, migrations.RunPython.noop),
    ]
