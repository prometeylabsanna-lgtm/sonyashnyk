"""Видалення старих FilterOption / CategoryFilterSetting / proxy."""

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0014_migrate_to_catalog_filter"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="categoryfiltersetting",
            name="category",
        ),
        migrations.DeleteModel(name="FilterOption"),
        migrations.DeleteModel(name="BrandFilterOption"),
        migrations.DeleteModel(name="CountryFilterOption"),
        migrations.DeleteModel(name="PowerFilterOption"),
        migrations.DeleteModel(name="VolumeFilterOption"),
        migrations.DeleteModel(name="CategoryFilterSetting"),
    ]
