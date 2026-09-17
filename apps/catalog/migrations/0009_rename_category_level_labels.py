from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0008_category_level_proxies"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="rootcategory",
            options={
                "verbose_name": "1 рівень категорій",
                "verbose_name_plural": "1 рівень категорій",
            },
        ),
        migrations.AlterModelOptions(
            name="subcategory",
            options={
                "verbose_name": "2 рівень категорій",
                "verbose_name_plural": "2 рівень категорій",
            },
        ),
        migrations.AlterModelOptions(
            name="subsubcategory",
            options={
                "verbose_name": "3 рівень категорій",
                "verbose_name_plural": "3 рівень категорій",
            },
        ),
    ]
