from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("orders", "0007_order_stock_released"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="monopay_invoice_id",
            field=models.CharField(
                blank=True, default="", max_length=64, verbose_name="Monopay invoiceId",
            ),
        ),
        migrations.AddField(
            model_name="order",
            name="monopay_invoice_at",
            field=models.DateTimeField(
                blank=True, null=True, verbose_name="Monopay інвойс створено",
            ),
        ),
    ]
