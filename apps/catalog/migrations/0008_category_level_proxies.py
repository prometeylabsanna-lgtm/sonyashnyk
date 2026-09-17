from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0007_category_image_help_text_static_slugs"),
    ]

    operations = [
        migrations.CreateModel(
            name="RootCategory",
            fields=[],
            options={
                "verbose_name": "Головна категорія",
                "verbose_name_plural": "Головні категорії",
                "proxy": True,
                "indexes": [],
                "constraints": [],
            },
            bases=("catalog.category",),
        ),
        migrations.CreateModel(
            name="SubCategory",
            fields=[],
            options={
                "verbose_name": "Підкатегорія",
                "verbose_name_plural": "Підкатегорії",
                "proxy": True,
                "indexes": [],
                "constraints": [],
            },
            bases=("catalog.category",),
        ),
        migrations.CreateModel(
            name="SubSubCategory",
            fields=[],
            options={
                "verbose_name": "Підпідкатегорія",
                "verbose_name_plural": "Підпідкатегорії",
                "proxy": True,
                "indexes": [],
                "constraints": [],
            },
            bases=("catalog.category",),
        ),
        migrations.AlterField(
            model_name="category",
            name="image",
            field=models.ImageField(
                blank=True,
                help_text=(
                    "PNG або WebP. Головні: якщо порожньо — іконка шапки/головної. "
                    "Підкатегорії та підпідкатегорії: якщо порожньо — соняшник."
                ),
                null=True,
                upload_to="categories/",
                verbose_name="Іконка категорії",
            ),
        ),
    ]
