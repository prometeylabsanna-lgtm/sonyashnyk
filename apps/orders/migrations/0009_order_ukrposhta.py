from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0008_order_monopay_invoice"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="up_barcode",
            field=models.CharField(blank=True, default="", max_length=32, verbose_name="УП ШКІ (ТТН)"),
        ),
        migrations.AddField(
            model_name="order",
            name="up_city_id",
            field=models.CharField(blank=True, max_length=32, verbose_name="УП City ID"),
        ),
        migrations.AddField(
            model_name="order",
            name="up_postindex",
            field=models.CharField(blank=True, max_length=16, verbose_name="УП індекс відділення"),
        ),
        migrations.AddField(
            model_name="order",
            name="up_region_id",
            field=models.CharField(blank=True, max_length=32, verbose_name="УП Region ID"),
        ),
        migrations.AddField(
            model_name="order",
            name="up_shipment_uuid",
            field=models.CharField(blank=True, default="", max_length=64, verbose_name="УП UUID відправлення"),
        ),
        migrations.AddField(
            model_name="order",
            name="up_status",
            field=models.CharField(blank=True, default="", max_length=255, verbose_name="УП статус"),
        ),
        migrations.AddField(
            model_name="order",
            name="up_status_at",
            field=models.DateTimeField(blank=True, null=True, verbose_name="УП статус оновлено"),
        ),
    ]
