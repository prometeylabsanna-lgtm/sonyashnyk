from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0020_max_per_order"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="dntrade_code",
            field=models.BigIntegerField(
                blank=True,
                db_index=True,
                help_text="Числовий код товару в DNTrade.",
                null=True,
                verbose_name="DNTrade code",
            ),
        ),
        migrations.AddField(
            model_name="product",
            name="dntrade_product_id",
            field=models.CharField(
                blank=True,
                db_index=True,
                default="",
                help_text="UUID товару в Navkolo DNTrade.",
                max_length=64,
                verbose_name="DNTrade product_id",
            ),
        ),
        migrations.AddField(
            model_name="product",
            name="dntrade_synced_at",
            field=models.DateTimeField(
                blank=True,
                null=True,
                verbose_name="Остання синхронізація DNTrade",
            ),
        ),
        migrations.AddField(
            model_name="productimage",
            name="source_url",
            field=models.URLField(
                blank=True,
                default="",
                help_text="Щоб не качати те саме фото щодня.",
                max_length=500,
                verbose_name="URL джерела (DNTrade)",
            ),
        ),
        migrations.AddField(
            model_name="productvariant",
            name="dntrade_code",
            field=models.BigIntegerField(
                blank=True,
                db_index=True,
                null=True,
                verbose_name="DNTrade code",
            ),
        ),
        migrations.AddField(
            model_name="productvariant",
            name="dntrade_product_id",
            field=models.CharField(
                blank=True,
                db_index=True,
                default="",
                max_length=64,
                verbose_name="DNTrade product_id",
            ),
        ),
    ]
