from django.db import migrations, models


def forwards_liqpay_to_monopay(apps, schema_editor):
    Order = apps.get_model("orders", "Order")
    Order.objects.filter(payment_method="liqpay").update(payment_method="monopay")


def backwards_monopay_to_liqpay(apps, schema_editor):
    Order = apps.get_model("orders", "Order")
    Order.objects.filter(payment_method="monopay").update(payment_method="liqpay")


class Migration(migrations.Migration):
    dependencies = [
        ("orders", "0005_audit_checkout_security"),
    ]

    operations = [
        migrations.AlterField(
            model_name="order",
            name="payment_method",
            field=models.CharField(
                choices=[
                    ("monopay", "Оплата карткою (Monobank)"),
                    ("cod", "Оплата при отриманні (післяплата)"),
                    ("bank", "Оплата на розрахунковий рахунок"),
                    ("cash_pickup", "Оплата при самовивозі"),
                ],
                max_length=16,
                verbose_name="Спосіб оплати",
            ),
        ),
        migrations.RunPython(forwards_liqpay_to_monopay, backwards_monopay_to_liqpay),
    ]
