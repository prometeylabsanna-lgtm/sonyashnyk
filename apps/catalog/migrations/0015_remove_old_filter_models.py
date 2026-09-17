"""Видалення старих FilterOption / CategoryFilterSetting / proxy."""

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0014_migrate_to_catalog_filter"),
    ]

    operations = [
        # Без RemoveField: на SQLite RemoveField(FK) ламає migrate
        # («NewCategoryFilterSetting has no field named category»).
        migrations.DeleteModel(name="BrandFilterOption"),
        migrations.DeleteModel(name="CountryFilterOption"),
        migrations.DeleteModel(name="PowerFilterOption"),
        migrations.DeleteModel(name="VolumeFilterOption"),
        migrations.DeleteModel(name="FilterOption"),
        migrations.DeleteModel(name="CategoryFilterSetting"),
    ]
