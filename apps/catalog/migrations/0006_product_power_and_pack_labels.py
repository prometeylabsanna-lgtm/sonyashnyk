# Generated manually for product.power + pack_volume labels

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0005_category_image_help_text_all_levels"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="power",
            field=models.CharField(
                blank=True,
                help_text="Наприклад: 600 Вт, 800 Вт, 1.2 кВт. Для інструменту та оприскувачів.",
                max_length=80,
                verbose_name="Потужність",
            ),
        ),
        migrations.AlterField(
            model_name="product",
            name="characteristics",
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text="У адмінці — рядки «назва → значення» (без JSON).",
                verbose_name="Характеристики",
            ),
        ),
        migrations.AlterField(
            model_name="product",
            name="pack_volume",
            field=models.CharField(
                blank=True,
                help_text=(
                    "Обʼєм або вага: 6 мл, 100 мл, 1 л, 10 г, 500 г, 5 кг. "
                    "Окремі фасування краще робити варіантами товару."
                ),
                max_length=80,
                verbose_name="Обʼєм / вага / фасування",
            ),
        ),
        migrations.AlterField(
            model_name="productvariant",
            name="label",
            field=models.CharField(
                help_text="Фасування: «100 мл», «1 л», «10 г», «500 г» — не розміри одягу.",
                max_length=80,
                verbose_name="Назва варіанту",
            ),
        ),
    ]
