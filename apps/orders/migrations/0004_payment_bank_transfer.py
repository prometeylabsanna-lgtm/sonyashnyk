from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0003_order_np_refs"),
    ]

    operations = [
        migrations.AlterField(
            model_name="order",
            name="payment_method",
            field=models.CharField(
                choices=[
                    ("liqpay", "Оплата карткою (LiqPay)"),
                    ("cod", "Оплата при отриманні (післяплата)"),
                    ("bank", "Оплата на розрахунковий рахунок"),
                    ("cash_pickup", "Оплата при самовивозі"),
                ],
                max_length=16,
                verbose_name="Спосіб оплати",
            ),
        ),
    ]
