# Generated manually — help_text for Category.image

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0006_product_power_and_pack_labels"),
    ]

    operations = [
        migrations.AlterField(
            model_name="category",
            name="image",
            field=models.ImageField(
                blank=True,
                help_text=(
                    "PNG або WebP. Якщо порожньо — береться static-іконка: "
                    "корені з шапки/головної, підкатегорії з static/img/catalog/subcats/{slug}.png."
                ),
                null=True,
                upload_to="categories/",
                verbose_name="Іконка категорії",
            ),
        ),
    ]
