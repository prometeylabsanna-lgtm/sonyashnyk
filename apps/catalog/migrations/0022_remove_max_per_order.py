from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0021_dntrade_fields"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="productvariant",
            name="max_per_order",
        ),
    ]
