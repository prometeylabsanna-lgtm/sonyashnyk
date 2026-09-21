"""Прибрати фільтр «Потужність» з каталогу. Поле Product.power лишається."""

from django.db import migrations


def remove_power_filter(apps, schema_editor):
    CatalogFilter = apps.get_model("catalog", "CatalogFilter")
    CatalogFilter.objects.filter(slug="power").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0015_remove_old_filter_models"),
    ]

    operations = [
        migrations.RunPython(remove_power_filter, migrations.RunPython.noop),
    ]
