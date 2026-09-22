from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0009_hardcode_shipping_threshold"),
    ]

    operations = [
        migrations.AddField(
            model_name="pickuppoint",
            name="map_embed",
            field=models.TextField(
                blank=True,
                default="",
                help_text=(
                    "Вставте код iframe з Google Maps (Поділитися → Вбудувати карту) "
                    "або лише посилання embed. Порожнє — заглушка «Київ, Хрещатик 1»."
                ),
                verbose_name="Google Maps (iframe)",
            ),
        ),
    ]
