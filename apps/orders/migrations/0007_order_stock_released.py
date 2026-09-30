from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("orders", "0006_monopay"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="stock_released",
            field=models.BooleanField(
                default=False,
                help_text="True після повернення резерву (невдала / прострочена / refunded оплата).",
                verbose_name="Залишок повернуто",
            ),
        ),
    ]
